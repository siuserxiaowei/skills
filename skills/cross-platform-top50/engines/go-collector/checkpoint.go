package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"sync"
)

var artifactFilenamePattern = regexp.MustCompile(`^[0-9a-f]{16}-[0-9a-f]{16}\.body$`)

type checkpointDocument struct {
	ContractVersion string                     `json:"contract_version"`
	EngineID        string                     `json:"engine_id"`
	EngineVersion   string                     `json:"engine_version"`
	RunID           string                     `json:"run_id"`
	Completed       map[string]checkpointEntry `json:"completed"`
}

type checkpointEntry struct {
	JobFingerprint    string    `json:"job_fingerprint"`
	ResultFingerprint string    `json:"result_fingerprint"`
	Result            JobResult `json:"result"`
}

type checkpointStore struct {
	mu        sync.Mutex
	path      string
	artifacts string
	doc       checkpointDocument
}

func openCheckpoint(path string, manifest Manifest, artifacts string) (*checkpointStore, error) {
	store := &checkpointStore{
		path:      path,
		artifacts: artifacts,
		doc: checkpointDocument{
			ContractVersion: CheckpointContractVersion,
			EngineID:        EngineID,
			EngineVersion:   EngineVersion,
			RunID:           manifest.RunID,
			Completed:       make(map[string]checkpointEntry),
		},
	}
	if path == "" {
		return store, nil
	}
	file, err := os.Open(path)
	if errors.Is(err, os.ErrNotExist) {
		return store, nil
	}
	if err != nil {
		return nil, errorf("checkpoint_read_error", false, "open checkpoint: %v", err)
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	decoder.DisallowUnknownFields()
	var doc checkpointDocument
	if err := decoder.Decode(&doc); err != nil {
		return nil, errorf("checkpoint_invalid", false, "decode checkpoint: %v", err)
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return nil, errorf("checkpoint_invalid", false, "checkpoint contains trailing JSON")
	}
	if doc.ContractVersion != CheckpointContractVersion || doc.EngineID != EngineID || doc.EngineVersion != EngineVersion || doc.RunID != manifest.RunID || doc.Completed == nil {
		return nil, errorf("checkpoint_invalid", false, "checkpoint identity does not match this run")
	}
	store.doc = doc
	return store, nil
}

func fingerprintJob(manifest Manifest, job Job) string {
	type header struct {
		Name  string `json:"name"`
		Value string `json:"value"`
	}
	names := make([]string, 0, len(job.Headers))
	for name := range job.Headers {
		names = append(names, name)
	}
	sort.Strings(names)
	headers := make([]header, 0, len(names))
	for _, name := range names {
		headers = append(headers, header{Name: name, Value: job.Headers[name]})
	}
	stable := struct {
		CollectorIdentity string   `json:"collector_identity"`
		MaxResponseBytes  int64    `json:"max_response_bytes"`
		TimeoutMS         int      `json:"timeout_ms"`
		MaxAttempts       int      `json:"max_attempts"`
		QueryID           string   `json:"query_id"`
		Platform          string   `json:"platform"`
		URL               string   `json:"url"`
		Method            string   `json:"method"`
		Headers           []header `json:"headers"`
	}{CollectorUserAgent, manifest.MaxResponseBytes, manifest.TimeoutMS, manifest.MaxAttempts, job.QueryID, job.Platform, job.URL, job.Method, headers}
	payload, _ := json.Marshal(stable)
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}

func (store *checkpointStore) resume(manifest Manifest, job Job) (JobResult, bool) {
	if store.path == "" {
		return JobResult{}, false
	}
	store.mu.Lock()
	entry, exists := store.doc.Completed[job.JobID]
	store.mu.Unlock()
	if !exists || entry.JobFingerprint != fingerprintJob(manifest, job) || !validCheckpointResult(job, entry) {
		return JobResult{}, false
	}
	if !verifyArtifact(store.artifacts, entry.Result) {
		return JobResult{}, false
	}
	result := entry.Result
	result.FromCheckpoint = true
	return result, true
}

func validCheckpointResult(job Job, entry checkpointEntry) bool {
	result := entry.Result
	if result.Status != StatusTransportSuccess || result.JobID != job.JobID || result.QueryID != job.QueryID ||
		result.Platform != job.Platform || result.URL != job.URL || result.FinalURL == "" {
		return false
	}
	if ValidateURLStructure(result.FinalURL) != nil {
		return false
	}
	return entry.ResultFingerprint != "" && entry.ResultFingerprint == fingerprintResult(result)
}

func fingerprintResult(result JobResult) string {
	copy := result
	copy.FromCheckpoint = false
	payload, _ := json.Marshal(copy)
	sum := sha256.Sum256(payload)
	return hex.EncodeToString(sum[:])
}

func verifyArtifact(artifacts string, result JobResult) bool {
	if result.ArtifactPath == "" || result.BodySHA256 == "" || result.Bytes < 0 {
		return false
	}
	base, err := filepath.Abs(artifacts)
	if err != nil {
		return false
	}
	target, err := filepath.Abs(result.ArtifactPath)
	if err != nil || !filepath.IsAbs(result.ArtifactPath) || filepath.Dir(target) != base || !artifactFilenamePattern.MatchString(filepath.Base(target)) {
		return false
	}
	info, err := os.Lstat(target)
	if err != nil || !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 {
		return false
	}
	file, err := os.Open(target)
	if err != nil {
		return false
	}
	defer file.Close()
	hash := sha256.New()
	bytesCopied, err := io.Copy(hash, file)
	return err == nil && bytesCopied == result.Bytes && hex.EncodeToString(hash.Sum(nil)) == result.BodySHA256
}

func (store *checkpointStore) record(manifest Manifest, job Job, result JobResult) error {
	if store.path == "" || result.Status != StatusTransportSuccess {
		return nil
	}
	result.FromCheckpoint = false
	store.mu.Lock()
	defer store.mu.Unlock()
	store.doc.Completed[job.JobID] = checkpointEntry{
		JobFingerprint:    fingerprintJob(manifest, job),
		ResultFingerprint: fingerprintResult(result),
		Result:            result,
	}
	if err := AtomicWriteJSON(store.path, store.doc); err != nil {
		delete(store.doc.Completed, job.JobID)
		return errorf("checkpoint_write_error", false, "write checkpoint: %v", err)
	}
	return nil
}

func AtomicWriteJSON(path string, value any) error {
	if path == "" {
		return errors.New("output path is empty")
	}
	directory := filepath.Dir(path)
	if err := os.MkdirAll(directory, 0o700); err != nil {
		return fmt.Errorf("create output directory: %w", err)
	}
	temporary, err := os.CreateTemp(directory, ".json-tmp-*")
	if err != nil {
		return fmt.Errorf("create temporary output: %w", err)
	}
	temporaryPath := temporary.Name()
	keep := false
	defer func() {
		_ = temporary.Close()
		if !keep {
			_ = os.Remove(temporaryPath)
		}
	}()
	if err := temporary.Chmod(0o600); err != nil {
		return fmt.Errorf("set output permissions: %w", err)
	}
	encoder := json.NewEncoder(temporary)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		return fmt.Errorf("encode output: %w", err)
	}
	if err := temporary.Sync(); err != nil {
		return fmt.Errorf("sync output: %w", err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close output: %w", err)
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return fmt.Errorf("replace output: %w", err)
	}
	keep = true
	if dir, err := os.Open(directory); err == nil {
		_ = dir.Sync()
		_ = dir.Close()
	}
	return nil
}

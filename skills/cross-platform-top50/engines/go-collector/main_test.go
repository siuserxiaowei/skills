package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestProbeCommandPrintsSingleMachineReadableJSON(t *testing.T) {
	var stdout, stderr bytes.Buffer
	if err := run([]string{"probe", "--json"}, &stdout, &stderr); err != nil {
		t.Fatal(err)
	}
	var probe Probe
	decoder := json.NewDecoder(bytes.NewReader(stdout.Bytes()))
	if err := decoder.Decode(&probe); err != nil {
		t.Fatalf("decode probe: %v; stdout=%q", err, stdout.String())
	}
	if decoder.Decode(&struct{}{}) == nil {
		t.Fatalf("stdout contains more than one JSON value: %q", stdout.String())
	}
	if probe.ContractVersion != EngineContractVersion || probe.EngineID != EngineID || probe.EngineVersion != EngineVersion || probe.Status != "ready" {
		t.Fatalf("probe = %#v", probe)
	}
	if probe.EngineVersion != "0.2.0" {
		t.Fatalf("engine version = %q; want 0.2.0", probe.EngineVersion)
	}
	want := []string{
		"public_http_collect", "get", "head", "bounded_concurrency",
		"per_host_rate_limit", "retry_429_5xx_transient_network",
		"response_size_limit", "sha256_artifacts", "atomic_result",
		"checkpoint_resume", "dns_rebinding_defense", "same_origin_redirect_revalidation",
		"robots_rfc9309", "fixed_transparent_user_agent", "content_negotiation_provenance",
		"input_sha256_binding",
	}
	if strings.Join(probe.Capabilities, ",") != strings.Join(want, ",") {
		t.Fatalf("capabilities=%v want=%v", probe.Capabilities, want)
	}
	if stderr.Len() != 0 {
		t.Fatalf("stderr=%q", stderr.String())
	}
}

func TestProbeRequiresJSONAndUnknownCommandFails(t *testing.T) {
	for _, args := range [][]string{{"probe"}, {"nope"}, {}} {
		if err := run(args, &bytes.Buffer{}, &bytes.Buffer{}); err == nil {
			t.Fatalf("run(%v) unexpectedly succeeded", args)
		}
	}
}

func TestCollectCommandResumesCheckpointAndWritesSingleJSON(t *testing.T) {
	directory := t.TempDir()
	artifacts := filepath.Join(directory, "artifacts")
	if err := os.MkdirAll(artifacts, 0o700); err != nil {
		t.Fatal(err)
	}
	manifest := validManifest()
	body := []byte("checkpoint fixture")
	digest := sha256.Sum256(body)
	digestHex := hex.EncodeToString(digest[:])
	artifact := artifactName(artifacts, manifest.Jobs[0].JobID, digestHex)
	if err := os.WriteFile(artifact, body, 0o600); err != nil {
		t.Fatal(err)
	}
	checkpoint := filepath.Join(directory, "checkpoint.json")
	checkpointResult := JobResult{
		JobID: manifest.Jobs[0].JobID, QueryID: manifest.Jobs[0].QueryID,
		Platform: manifest.Jobs[0].Platform, URL: manifest.Jobs[0].URL,
		FinalURL: manifest.Jobs[0].URL,
		Status:   StatusTransportSuccess, Attempts: 1, HTTPStatus: 200,
		ContentType: "text/plain", Bytes: int64(len(body)),
		BodySHA256: digestHex, ArtifactPath: artifact,
	}
	checkpointValue := checkpointDocument{
		ContractVersion: CheckpointContractVersion,
		EngineID:        EngineID, EngineVersion: EngineVersion, RunID: manifest.RunID,
		Completed: map[string]checkpointEntry{
			manifest.Jobs[0].JobID: {
				JobFingerprint:    fingerprintJob(manifest, manifest.Jobs[0]),
				ResultFingerprint: fingerprintResult(checkpointResult),
				Result:            checkpointResult,
			},
		},
	}
	if err := AtomicWriteJSON(checkpoint, checkpointValue); err != nil {
		t.Fatal(err)
	}
	input := filepath.Join(directory, "manifest.json")
	if err := AtomicWriteJSON(input, manifest); err != nil {
		t.Fatal(err)
	}
	inputDigest := fileSHA256ForTest(t, input)
	output := filepath.Join(directory, "result.json")
	var stdout, stderr bytes.Buffer
	if err := runWithCollector([]string{
		"collect", "--input", input, "--output", output,
		"--artifacts", artifacts, "--checkpoint", checkpoint,
		"--expected-input-sha256", inputDigest,
	}, &stdout, &stderr, func(Manifest) *Collector {
		return &Collector{Robots: allowAllRobots{}}
	}); err != nil {
		t.Fatalf("collect error=%v stderr=%q", err, stderr.String())
	}
	if stderr.Len() != 0 {
		t.Fatalf("stderr=%q", stderr.String())
	}
	var streamed ResultDocument
	decoder := json.NewDecoder(bytes.NewReader(stdout.Bytes()))
	if err := decoder.Decode(&streamed); err != nil {
		t.Fatalf("stdout decode: %v", err)
	}
	if decoder.Decode(&struct{}{}) == nil {
		t.Fatalf("stdout contained multiple JSON values")
	}
	var persisted ResultDocument
	file, err := os.Open(output)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.NewDecoder(file).Decode(&persisted); err != nil {
		_ = file.Close()
		t.Fatal(err)
	}
	_ = file.Close()
	if streamed.ContractVersion != ResultContractVersion || streamed.Status != "complete" || len(streamed.Results) != 1 || !streamed.Results[0].FromCheckpoint {
		t.Fatalf("streamed result=%#v", streamed)
	}
	if persisted.Results[0].BodySHA256 != streamed.Results[0].BodySHA256 {
		t.Fatalf("persisted result differs: %#v vs %#v", persisted, streamed)
	}
}

func TestCollectCommandRejectsMissingOrInvalidInput(t *testing.T) {
	for _, args := range [][]string{
		{"collect"},
		{"collect", "--input", "missing", "--output", "result", "--artifacts", "artifacts"},
	} {
		if err := run(args, &bytes.Buffer{}, &bytes.Buffer{}); err == nil {
			t.Fatalf("run(%v) unexpectedly succeeded", args)
		}
	}
	directory := t.TempDir()
	input := filepath.Join(directory, "bad.json")
	if err := os.WriteFile(input, []byte(`{"contract_version":"wrong"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	err := run([]string{"collect", "--input", input, "--output", filepath.Join(directory, "result"), "--artifacts", filepath.Join(directory, "artifacts"), "--expected-input-sha256", fileSHA256ForTest(t, input)}, &bytes.Buffer{}, &bytes.Buffer{})
	if err == nil || ErrorCode(err) == "" {
		t.Fatalf("invalid manifest error=%v code=%q", err, ErrorCode(err))
	}
}

func TestCollectCommandRequiresValidExpectedInputSHA256BeforeReadingManifest(t *testing.T) {
	for _, value := range []string{"", "ABCDEF", strings.Repeat("a", 63), strings.Repeat("G", 64)} {
		t.Run(value, func(t *testing.T) {
			args := []string{
				"collect", "--input", filepath.Join(t.TempDir(), "missing.json"),
				"--output", filepath.Join(t.TempDir(), "result.json"),
				"--artifacts", t.TempDir(),
			}
			if value != "" {
				args = append(args, "--expected-input-sha256", value)
			}
			err := run(args, &bytes.Buffer{}, &bytes.Buffer{})
			if err == nil || ErrorCode(err) != "invalid_expected_input_sha256" {
				t.Fatalf("error=%v code=%q; want invalid_expected_input_sha256", err, ErrorCode(err))
			}
		})
	}
}

func TestCollectCommandRejectsChangedInputBytesBeforeDecodeOrFactory(t *testing.T) {
	directory := t.TempDir()
	input := filepath.Join(directory, "manifest.json")
	if err := AtomicWriteJSON(input, validManifest()); err != nil {
		t.Fatal(err)
	}
	expected := fileSHA256ForTest(t, input)
	file, err := os.OpenFile(input, os.O_APPEND|os.O_WRONLY, 0)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.WriteString(" \n"); err != nil {
		_ = file.Close()
		t.Fatal(err)
	}
	if err := file.Close(); err != nil {
		t.Fatal(err)
	}
	factoryCalled := false
	output := filepath.Join(directory, "result.json")
	err = runWithCollector([]string{
		"collect", "--input", input, "--expected-input-sha256", expected,
		"--output", output, "--artifacts", filepath.Join(directory, "artifacts"),
	}, &bytes.Buffer{}, &bytes.Buffer{}, func(Manifest) *Collector {
		factoryCalled = true
		return &Collector{}
	})
	if err == nil || ErrorCode(err) != "input_sha256_mismatch" {
		t.Fatalf("error=%v code=%q; want input_sha256_mismatch", err, ErrorCode(err))
	}
	if factoryCalled {
		t.Fatal("collector factory ran before input digest validation")
	}
	if _, err := os.Stat(output); !os.IsNotExist(err) {
		t.Fatalf("output exists after digest mismatch: %v", err)
	}
}

func fileSHA256ForTest(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256(data)
	return hex.EncodeToString(digest[:])
}

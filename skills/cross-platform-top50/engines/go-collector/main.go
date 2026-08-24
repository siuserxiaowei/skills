package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
)

var lowercaseSHA256Pattern = regexp.MustCompile(`^[0-9a-f]{64}$`)

func main() {
	if err := run(os.Args[1:], os.Stdout, os.Stderr); err != nil {
		code := ErrorCode(err)
		if code == "" {
			code = "command_error"
		}
		_, _ = fmt.Fprintf(os.Stderr, "go-collector: %s: %s\n", code, safeErrorMessage(err))
		os.Exit(2)
	}
}

func run(args []string, stdout, stderr io.Writer) error {
	return runWithCollector(args, stdout, stderr, func(manifest Manifest) *Collector {
		return (&Collector{}).withDefaults(manifest)
	})
}

func runWithCollector(args []string, stdout, stderr io.Writer, factory func(Manifest) *Collector) error {
	if len(args) == 0 {
		return errors.New("expected probe or collect command")
	}
	switch args[0] {
	case "probe":
		return runProbe(args[1:], stdout, stderr)
	case "collect":
		return runCollect(args[1:], stdout, stderr, factory)
	default:
		return fmt.Errorf("unknown command %q", args[0])
	}
}

func runProbe(args []string, stdout, stderr io.Writer) error {
	flags := flag.NewFlagSet("probe", flag.ContinueOnError)
	flags.SetOutput(stderr)
	jsonOutput := flags.Bool("json", false, "emit machine-readable JSON")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 || !*jsonOutput {
		return errors.New("probe requires --json and no positional arguments")
	}
	return writeJSON(stdout, Probe{
		ContractVersion: EngineContractVersion,
		EngineID:        EngineID,
		EngineVersion:   EngineVersion,
		Status:          "ready",
		Capabilities:    append([]string(nil), capabilities...),
	})
}

func runCollect(args []string, stdout, stderr io.Writer, factory func(Manifest) *Collector) error {
	flags := flag.NewFlagSet("collect", flag.ContinueOnError)
	flags.SetOutput(stderr)
	input := flags.String("input", "", "collector manifest JSON")
	output := flags.String("output", "", "result JSON path")
	artifacts := flags.String("artifacts", "", "artifact output directory")
	checkpoint := flags.String("checkpoint", "", "optional resume checkpoint path")
	expectedInputSHA256 := flags.String("expected-input-sha256", "", "expected exact SHA-256 of input manifest bytes")
	if err := flags.Parse(args); err != nil {
		return err
	}
	if flags.NArg() != 0 || *input == "" || *output == "" || *artifacts == "" {
		return errors.New("collect requires --input, --output, --artifacts, and --expected-input-sha256")
	}
	if !lowercaseSHA256Pattern.MatchString(*expectedInputSHA256) {
		return errorf("invalid_expected_input_sha256", false, "collect requires --expected-input-sha256 as 64 lowercase hexadecimal characters")
	}
	file, err := os.Open(*input)
	if err != nil {
		return errorf("manifest_read_error", false, "open input manifest: %v", err)
	}
	inputBytes, readErr := io.ReadAll(file)
	closeErr := file.Close()
	if readErr != nil {
		return errorf("manifest_read_error", false, "read input manifest: %v", readErr)
	}
	if closeErr != nil {
		return errorf("manifest_read_error", false, "close input manifest: %v", closeErr)
	}
	actualInputSHA256 := fmt.Sprintf("%x", sha256.Sum256(inputBytes))
	if actualInputSHA256 != *expectedInputSHA256 {
		return errorf("input_sha256_mismatch", false, "input manifest SHA-256 does not match the expected digest")
	}
	manifest, decodeErr := DecodeManifest(bytes.NewReader(inputBytes))
	if decodeErr != nil {
		return decodeErr
	}
	collector := factory(manifest).withDefaults(manifest)
	result, err := collector.Collect(context.Background(), manifest, *artifacts, *checkpoint)
	if err != nil {
		return err
	}
	if err := AtomicWriteJSON(*output, result); err != nil {
		return errorf("result_write_error", false, "write result: %v", err)
	}
	return writeJSON(stdout, result)
}

func writeJSON(output io.Writer, value any) error {
	encoder := json.NewEncoder(output)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		return fmt.Errorf("encode JSON output: %w", err)
	}
	return nil
}

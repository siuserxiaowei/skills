use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

fn temp_dir(test_name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let path = std::env::temp_dir().join(format!(
        "rust-processor-{test_name}-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir(&path).unwrap();
    path
}

fn valid_input() -> Value {
    json!({
        "contract_version": "top50-processor/v1",
        "run_id": "cli-test",
        "candidates": [{
            "candidate_id": "one",
            "platform": "github",
            "url": "https://github.com/openai/codex?utm_source=test",
            "title": "Codex",
            "author": "OpenAI",
            "published_at": "2026-08-24",
            "excerpt": "A sufficiently long excerpt documents the repository, its purpose, evidence, maintenance state, limitations, and independently verifiable source details."
        }]
    })
}

fn sha256_hex(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[test]
fn probe_reports_machine_readable_contract_and_capabilities() {
    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["probe", "--json"])
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );

    let probe: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(probe["contract_version"], "top50-engine/v1");
    assert_eq!(probe["engine_id"], "rust-processor");
    assert_eq!(probe["engine_version"], "0.1.0");
    assert_eq!(probe["status"], "ready");
    let capabilities = probe["capabilities"].as_array().unwrap();
    assert!(
        capabilities
            .iter()
            .any(|value| value == "safe_url_validation")
    );
    assert!(
        capabilities
            .iter()
            .any(|value| value == "transitive_exact_clustering")
    );
}

#[test]
fn process_writes_a_complete_result_to_the_requested_path() {
    let dir = temp_dir("success");
    let input_path = dir.join("input.json");
    let output_path = dir.join("output.json");
    let input = serde_json::to_vec(&valid_input()).unwrap();
    fs::write(&input_path, &input).unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--input"])
        .arg(&input_path)
        .arg("--expected-input-sha256")
        .arg(sha256_hex(&input))
        .arg("--output")
        .arg(&output_path)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );

    let result: Value = serde_json::from_slice(&fs::read(&output_path).unwrap()).unwrap();
    assert_eq!(result["contract_version"], "top50-processor-result/v1");
    assert_eq!(result["counts"]["processed_candidates"], 1);
    assert_eq!(
        result["processed_candidates"][0]["canonical_url"],
        "https://github.com/openai/codex"
    );
    assert_eq!(
        result["processed_candidates"][0]["requires_fetch_time_dns_validation"],
        true
    );

    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn invalid_processing_never_clobbers_an_existing_output() {
    let dir = temp_dir("atomic-failure");
    let input_path = dir.join("invalid.json");
    let output_path = dir.join("output.json");
    let input = br#"{"contract_version":"wrong"}"#;
    fs::write(&input_path, input).unwrap();
    fs::write(&output_path, b"sentinel-do-not-clobber").unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--input"])
        .arg(&input_path)
        .arg("--expected-input-sha256")
        .arg(sha256_hex(input))
        .arg("--output")
        .arg(&output_path)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert_eq!(fs::read(&output_path).unwrap(), b"sentinel-do-not-clobber");
    assert_eq!(
        fs::read_dir(&dir).unwrap().count(),
        2,
        "temporary output leaked"
    );

    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn successful_processing_atomically_replaces_an_existing_output() {
    let dir = temp_dir("atomic-success");
    let input_path = dir.join("input.json");
    let output_path = dir.join("output.json");
    let input = serde_json::to_vec(&valid_input()).unwrap();
    fs::write(&input_path, &input).unwrap();
    fs::write(&output_path, b"old-output").unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--output"])
        .arg(&output_path)
        .arg("--input")
        .arg(&input_path)
        .arg("--expected-input-sha256")
        .arg(sha256_hex(&input))
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let replaced: Value = serde_json::from_slice(&fs::read(&output_path).unwrap()).unwrap();
    assert_eq!(replaced["run_id"], "cli-test");
    assert_eq!(
        fs::read_dir(&dir).unwrap().count(),
        2,
        "temporary output leaked"
    );

    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn refuses_to_overwrite_the_input_file_with_its_output() {
    let dir = temp_dir("same-input-output");
    let input_path = dir.join("input.json");
    let original = serde_json::to_vec(&valid_input()).unwrap();
    fs::write(&input_path, &original).unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--input"])
        .arg(&input_path)
        .arg("--expected-input-sha256")
        .arg(sha256_hex(&original))
        .arg("--output")
        .arg(&input_path)
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert_eq!(fs::read(&input_path).unwrap(), original);

    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn process_requires_an_expected_input_digest() {
    let dir = temp_dir("missing-expected-digest");
    let input_path = dir.join("input.json");
    let output_path = dir.join("output.json");
    fs::write(&input_path, serde_json::to_vec(&valid_input()).unwrap()).unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--input"])
        .arg(&input_path)
        .arg("--output")
        .arg(&output_path)
        .output()
        .unwrap();

    assert!(!output.status.success());
    assert!(!output_path.exists());
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("--expected-input-sha256"),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn process_rejects_same_id_content_replacement_against_expected_digest() {
    let dir = temp_dir("input-replacement");
    let input_path = dir.join("input.json");
    let output_path = dir.join("output.json");
    let authorized = serde_json::to_vec(&valid_input()).unwrap();
    let mut replacement = valid_input();
    replacement["candidates"][0]["title"] = json!("Replaced while preserving candidate ID");
    fs::write(&input_path, serde_json::to_vec(&replacement).unwrap()).unwrap();
    fs::write(&output_path, b"sentinel-do-not-clobber").unwrap();

    let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
        .args(["process", "--input"])
        .arg(&input_path)
        .arg("--expected-input-sha256")
        .arg(sha256_hex(&authorized))
        .arg("--output")
        .arg(&output_path)
        .output()
        .unwrap();

    assert!(!output.status.success());
    assert_eq!(fs::read(&output_path).unwrap(), b"sentinel-do-not-clobber");
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("SHA-256"),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    fs::remove_dir_all(dir).unwrap();
}

#[test]
fn process_rejects_noncanonical_expected_input_digests() {
    for (label, expected) in [
        ("short", "a".repeat(63)),
        ("uppercase", "A".repeat(64)),
        ("non-hex", "g".repeat(64)),
    ] {
        let dir = temp_dir(label);
        let input_path = dir.join("input.json");
        let output_path = dir.join("output.json");
        fs::write(&input_path, serde_json::to_vec(&valid_input()).unwrap()).unwrap();

        let output = Command::new(env!("CARGO_BIN_EXE_rust-processor"))
            .args(["process", "--input"])
            .arg(&input_path)
            .arg("--expected-input-sha256")
            .arg(expected)
            .arg("--output")
            .arg(&output_path)
            .output()
            .unwrap();

        assert!(!output.status.success(), "{label}");
        assert!(!output_path.exists(), "{label}");
        assert!(
            String::from_utf8_lossy(&output.stderr).contains("64 lowercase hexadecimal characters"),
            "{label}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        fs::remove_dir_all(dir).unwrap();
    }
}

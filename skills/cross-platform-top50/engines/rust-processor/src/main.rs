use rust_processor::{ENGINE_CONTRACT_VERSION, ENGINE_ID, ENGINE_VERSION, process_file_atomic};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Serialize)]
struct Probe {
    contract_version: &'static str,
    engine_id: &'static str,
    engine_version: &'static str,
    status: &'static str,
    capabilities: &'static [&'static str],
}

const CAPABILITIES: &[&str] = &[
    "candidate_normalization",
    "safe_url_validation",
    "tracking_parameter_removal",
    "http_https_identity_unification",
    "strict_content_fingerprinting",
    "transitive_exact_clustering",
    "near_duplicate_review_flags",
    "deterministic_result_digest",
    "atomic_file_output",
];

fn main() {
    if let Err(error) = run(std::env::args().skip(1).collect()) {
        eprintln!("rust-processor: {error}");
        std::process::exit(2);
    }
}

fn run(arguments: Vec<String>) -> Result<(), String> {
    match arguments.as_slice() {
        [command, json] if command == "probe" && json == "--json" => {
            let probe = Probe {
                contract_version: ENGINE_CONTRACT_VERSION,
                engine_id: ENGINE_ID,
                engine_version: ENGINE_VERSION,
                status: "ready",
                capabilities: CAPABILITIES,
            };
            println!(
                "{}",
                serde_json::to_string(&probe).map_err(|error| error.to_string())?
            );
            Ok(())
        }
        [command, rest @ ..] if command == "process" => process_command(rest),
        _ => Err(usage()),
    }
}

fn process_command(arguments: &[String]) -> Result<(), String> {
    let mut input: Option<PathBuf> = None;
    let mut output: Option<PathBuf> = None;
    let mut expected_input_sha256: Option<String> = None;
    let mut index = 0;
    while index < arguments.len() {
        let flag = &arguments[index];
        let value = arguments
            .get(index + 1)
            .ok_or_else(|| format!("missing value for {flag}\n{}", usage()))?;
        match flag.as_str() {
            "--input" if input.is_none() => input = Some(PathBuf::from(value)),
            "--output" if output.is_none() => output = Some(PathBuf::from(value)),
            "--expected-input-sha256" if expected_input_sha256.is_none() => {
                expected_input_sha256 = Some(value.to_owned())
            }
            "--input" | "--output" | "--expected-input-sha256" => {
                return Err(format!("duplicate flag {flag}"));
            }
            _ => return Err(format!("unknown flag {flag}\n{}", usage())),
        }
        index += 2;
    }
    let input = input.ok_or_else(|| format!("missing --input\n{}", usage()))?;
    let output = output.ok_or_else(|| format!("missing --output\n{}", usage()))?;
    let expected_input_sha256 = expected_input_sha256
        .ok_or_else(|| format!("missing --expected-input-sha256\n{}", usage()))?;
    let result = process_file_atomic(&input, &output, &expected_input_sha256)
        .map_err(|error| error.to_string())?;
    println!(
        "{}",
        String::from_utf8(result).map_err(|error| error.to_string())?
    );
    Ok(())
}

fn usage() -> String {
    "usage: rust-processor probe --json | rust-processor process --input <json> \
     --expected-input-sha256 <sha256> --output <json>"
        .to_owned()
}

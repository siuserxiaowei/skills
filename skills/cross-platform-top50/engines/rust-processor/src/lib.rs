use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::fmt::{Display, Formatter};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::net::{Ipv4Addr, Ipv6Addr};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use unicode_normalization::UnicodeNormalization;
use url::{Host, Url};

pub const ENGINE_CONTRACT_VERSION: &str = "top50-engine/v1";
pub const ENGINE_ID: &str = "rust-processor";
pub const ENGINE_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const INPUT_CONTRACT_VERSION: &str = "top50-processor/v1";
pub const RESULT_CONTRACT_VERSION: &str = "top50-processor-result/v1";

const MIN_EXACT_CONTENT_CHARS: usize = 80;
const MIN_DISTINCT_CONTENT_CHARS: usize = 8;
const NEAR_DUPLICATE_MIN_BASIS_POINTS: u16 = 8_500;
const SHINGLE_WIDTH: usize = 5;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProcessorError {
    message: String,
}

impl ProcessorError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }

    fn field(path: &str, message: impl Display) -> Self {
        Self::new(format!("{path}: {message}"))
    }
}

impl Display for ProcessorError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.message)
    }
}

impl std::error::Error for ProcessorError {}

impl From<std::io::Error> for ProcessorError {
    fn from(error: std::io::Error) -> Self {
        Self::new(error.to_string())
    }
}

impl From<serde_json::Error> for ProcessorError {
    fn from(error: serde_json::Error) -> Self {
        Self::new(error.to_string())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NormalizedUrl {
    pub canonical_url: String,
    pub requires_fetch_time_dns_validation: bool,
}

#[derive(Debug, Deserialize)]
struct ProcessorInput {
    contract_version: String,
    run_id: String,
    candidates: Vec<CandidateInput>,
}

#[derive(Debug, Deserialize)]
struct CandidateInput {
    candidate_id: String,
    platform: String,
    url: String,
    title: String,
    author: String,
    published_at: String,
    excerpt: String,
    #[serde(default)]
    platform_native_id: Option<String>,
    #[serde(default)]
    body_or_transcript_sha256: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProcessedCandidate {
    candidate_id: String,
    platform: String,
    url: String,
    canonical_url: String,
    canonical_url_sha256: String,
    requires_fetch_time_dns_validation: bool,
    title: String,
    author: String,
    published_at: String,
    excerpt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    platform_native_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    body_or_transcript_sha256: Option<String>,
    strict_content_fingerprint_sha256: String,
    strict_content_match_eligible: bool,
    #[serde(skip)]
    near_duplicate_text: String,
}

#[derive(Debug, Clone, Serialize)]
struct ExactCluster {
    cluster_id: String,
    representative_candidate_id: String,
    candidate_ids: Vec<String>,
    evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
struct NearDuplicateReview {
    review_id: String,
    candidate_ids: Vec<String>,
    similarity_basis_points: u16,
    method: &'static str,
    disposition: &'static str,
}

#[derive(Debug, Clone, Serialize)]
struct ResultCounts {
    input_candidates: usize,
    processed_candidates: usize,
    exact_clusters: usize,
    exact_duplicate_candidates: usize,
    near_duplicate_reviews: usize,
    dns_validation_required: usize,
}

#[derive(Debug, Serialize)]
struct DigestMaterial<'a> {
    contract_version: &'static str,
    engine_id: &'static str,
    engine_version: &'static str,
    run_id: &'a str,
    processed_candidates: &'a [ProcessedCandidate],
    exact_clusters: &'a [ExactCluster],
    near_duplicate_reviews: &'a [NearDuplicateReview],
    counts: &'a ResultCounts,
}

#[derive(Debug, Serialize)]
struct ProcessorResult<'a> {
    contract_version: &'static str,
    engine_id: &'static str,
    engine_version: &'static str,
    run_id: &'a str,
    processed_candidates: &'a [ProcessedCandidate],
    exact_clusters: &'a [ExactCluster],
    near_duplicate_reviews: &'a [NearDuplicateReview],
    counts: &'a ResultCounts,
    result_digest_sha256: &'a str,
}

pub fn process_json_slice(input: &[u8]) -> Result<Vec<u8>, ProcessorError> {
    let input: ProcessorInput =
        serde_json::from_slice(input).map_err(|error| ProcessorError::field("input", error))?;
    if input.contract_version != INPUT_CONTRACT_VERSION {
        return Err(ProcessorError::field(
            "contract_version",
            format!(
                "expected {INPUT_CONTRACT_VERSION}, got {}",
                input.contract_version
            ),
        ));
    }

    let run_id = validated_nonempty("run_id", &input.run_id)?;
    let input_count = input.candidates.len();
    let mut seen_candidate_ids = HashSet::with_capacity(input_count);
    let mut processed = Vec::with_capacity(input_count);

    for (index, candidate) in input.candidates.into_iter().enumerate() {
        let path = format!("candidates[{index}]");
        let candidate_id =
            validated_nonempty(&format!("{path}.candidate_id"), &candidate.candidate_id)?;
        if !seen_candidate_ids.insert(candidate_id.clone()) {
            return Err(ProcessorError::field(
                &format!("{path}.candidate_id"),
                format!("duplicate candidate_id {candidate_id:?}"),
            ));
        }

        let platform = normalized_for_match(&validated_nonempty(
            &format!("{path}.platform"),
            &candidate.platform,
        )?);
        let url = validated_url_input(&format!("{path}.url"), &candidate.url)?;
        let title = validated_nonempty(&format!("{path}.title"), &candidate.title)?;
        let author = validated_nonempty(&format!("{path}.author"), &candidate.author)?;
        let published_at =
            validated_nonempty(&format!("{path}.published_at"), &candidate.published_at)?;
        let excerpt = validated_nonempty(&format!("{path}.excerpt"), &candidate.excerpt)?;
        let platform_native_id = candidate
            .platform_native_id
            .as_deref()
            .map(|value| validated_nonempty(&format!("{path}.platform_native_id"), value))
            .transpose()?;
        let body_digest = candidate
            .body_or_transcript_sha256
            .as_deref()
            .map(|value| validate_sha256(&format!("{path}.body_or_transcript_sha256"), value))
            .transpose()?;

        let normalized_url = normalize_and_validate_url(&url)
            .map_err(|error| ProcessorError::field(&format!("{path}.url"), error))?;
        let normalized_excerpt = normalized_for_match(&excerpt);
        let eligible =
            body_digest.is_some() || content_is_exact_match_eligible(&normalized_excerpt);
        let content_basis = match body_digest.as_deref() {
            Some(digest) => format!("body_or_transcript_sha256:{digest}"),
            None => format!("excerpt:{normalized_excerpt}"),
        };
        let fingerprint_material = format!(
            "top50-strict-content/v1\0{}\0{}\0{}\0{}",
            normalized_for_match(&title),
            normalized_for_match(&author),
            normalized_for_match(&published_at),
            content_basis
        );

        processed.push(ProcessedCandidate {
            candidate_id,
            platform,
            url,
            canonical_url_sha256: sha256_hex(normalized_url.canonical_url.as_bytes()),
            canonical_url: normalized_url.canonical_url,
            requires_fetch_time_dns_validation: normalized_url.requires_fetch_time_dns_validation,
            title,
            author,
            published_at,
            excerpt,
            platform_native_id,
            body_or_transcript_sha256: body_digest,
            strict_content_fingerprint_sha256: sha256_hex(fingerprint_material.as_bytes()),
            strict_content_match_eligible: eligible,
            near_duplicate_text: normalized_excerpt,
        });
    }

    processed.sort_by(|left, right| left.candidate_id.cmp(&right.candidate_id));
    let (exact_clusters, roots) = build_exact_clusters(&processed);
    let near_duplicate_reviews = build_near_duplicate_reviews(&processed, &roots);
    let counts = ResultCounts {
        input_candidates: input_count,
        processed_candidates: processed.len(),
        exact_clusters: exact_clusters.len(),
        exact_duplicate_candidates: exact_clusters
            .iter()
            .map(|cluster| cluster.candidate_ids.len() - 1)
            .sum(),
        near_duplicate_reviews: near_duplicate_reviews.len(),
        dns_validation_required: processed
            .iter()
            .filter(|candidate| candidate.requires_fetch_time_dns_validation)
            .count(),
    };

    let digest_material = DigestMaterial {
        contract_version: RESULT_CONTRACT_VERSION,
        engine_id: ENGINE_ID,
        engine_version: ENGINE_VERSION,
        run_id: &run_id,
        processed_candidates: &processed,
        exact_clusters: &exact_clusters,
        near_duplicate_reviews: &near_duplicate_reviews,
        counts: &counts,
    };
    // Hash JSON object material, which is the exact result object with only the
    // digest field omitted. This keeps the digest independently reproducible.
    let digest_bytes = serde_json::to_vec(&serde_json::to_value(&digest_material)?)?;
    let digest = sha256_hex(&digest_bytes);
    let result = ProcessorResult {
        contract_version: RESULT_CONTRACT_VERSION,
        engine_id: ENGINE_ID,
        engine_version: ENGINE_VERSION,
        run_id: &run_id,
        processed_candidates: &processed,
        exact_clusters: &exact_clusters,
        near_duplicate_reviews: &near_duplicate_reviews,
        counts: &counts,
        result_digest_sha256: &digest,
    };

    serde_json::to_vec_pretty(&result).map_err(ProcessorError::from)
}

pub fn process_file_atomic(
    input_path: &Path,
    output_path: &Path,
    expected_input_sha256: &str,
) -> Result<Vec<u8>, ProcessorError> {
    if paths_resolve_to_same_file(input_path, output_path)? {
        return Err(ProcessorError::new(
            "input and output paths must identify different files",
        ));
    }
    validate_expected_input_sha256(expected_input_sha256)?;
    let input = fs::read(input_path)
        .map_err(|error| ProcessorError::field(&input_path.display().to_string(), error))?;
    let actual_input_sha256 = sha256_hex(&input);
    if actual_input_sha256 != expected_input_sha256 {
        return Err(ProcessorError::field(
            "--expected-input-sha256",
            format!(
                "input SHA-256 mismatch: expected {expected_input_sha256}, got {actual_input_sha256}"
            ),
        ));
    }
    let output = process_json_slice(&input)?;
    atomic_write(output_path, &output)?;
    Ok(output)
}

pub fn normalize_and_validate_url(input: &str) -> Result<NormalizedUrl, ProcessorError> {
    if input.is_empty() {
        return Err(ProcessorError::new("URL is empty"));
    }
    if input
        .chars()
        .any(|character| character.is_whitespace() || character.is_control())
    {
        return Err(ProcessorError::new(
            "URL contains whitespace or control characters",
        ));
    }
    if input.contains('\\') {
        return Err(ProcessorError::new("URL contains a backslash"));
    }
    if contains_encoded_unsafe_byte(input) {
        return Err(ProcessorError::new(
            "URL contains percent-encoded whitespace, control, or backslash bytes",
        ));
    }

    let scheme_separator = input
        .find("://")
        .ok_or_else(|| ProcessorError::new("URL must be absolute and include //"))?;
    let raw_scheme = &input[..scheme_separator];
    if !raw_scheme.eq_ignore_ascii_case("http") && !raw_scheme.eq_ignore_ascii_case("https") {
        return Err(ProcessorError::new("URL scheme must be http or https"));
    }
    let authority_start = scheme_separator + 3;
    let authority_end = input[authority_start..]
        .find(['/', '?', '#'])
        .map_or(input.len(), |relative| authority_start + relative);
    let authority = &input[authority_start..authority_end];
    if authority.is_empty() {
        return Err(ProcessorError::new("URL authority is empty"));
    }
    if authority.contains('@') {
        return Err(ProcessorError::new("URL userinfo is forbidden"));
    }
    let raw_host = raw_host_from_authority(authority)?;
    if raw_host.contains('%') {
        return Err(ProcessorError::new(
            "percent-encoded hostnames are forbidden",
        ));
    }
    if looks_like_legacy_ipv4(raw_host) {
        return Err(ProcessorError::new(
            "non-standard legacy IPv4 syntax is forbidden",
        ));
    }

    let mut url = Url::parse(input).map_err(|error| ProcessorError::new(error.to_string()))?;
    if url.scheme() != "http" && url.scheme() != "https" {
        return Err(ProcessorError::new("URL scheme must be http or https"));
    }
    if !url.username().is_empty() || url.password().is_some() {
        return Err(ProcessorError::new("URL userinfo is forbidden"));
    }

    let (normalized_host, requires_dns_validation) = match url
        .host()
        .ok_or_else(|| ProcessorError::new("URL host is missing"))?
    {
        Host::Ipv4(address) => {
            if !is_global_ipv4(address) {
                return Err(ProcessorError::new("IPv4 host is not globally routable"));
            }
            (address.to_string(), false)
        }
        Host::Ipv6(address) => {
            if !is_global_ipv6(address) {
                return Err(ProcessorError::new("IPv6 host is not globally routable"));
            }
            (format!("[{address}]"), false)
        }
        Host::Domain(domain) => {
            let domain = domain.trim_end_matches('.').to_ascii_lowercase();
            validate_dns_name(&domain)?;
            (
                domain.strip_prefix("www.").unwrap_or(&domain).to_owned(),
                true,
            )
        }
    };

    url.set_host(Some(&normalized_host))
        .map_err(|_| ProcessorError::new("failed to normalize URL host"))?;
    url.set_scheme("https")
        .map_err(|_| ProcessorError::new("failed to normalize URL scheme"))?;
    if matches!(url.port(), Some(80 | 443)) {
        url.set_port(None)
            .map_err(|_| ProcessorError::new("failed to normalize URL port"))?;
    }
    url.set_fragment(None);
    normalize_path(&mut url);
    normalize_query(&mut url);

    Ok(NormalizedUrl {
        canonical_url: url.to_string(),
        requires_fetch_time_dns_validation: requires_dns_validation,
    })
}

fn validated_nonempty(path: &str, value: &str) -> Result<String, ProcessorError> {
    if value.chars().any(char::is_control) {
        return Err(ProcessorError::field(path, "contains a control character"));
    }
    let normalized = normalize_display(value);
    if normalized.is_empty() {
        return Err(ProcessorError::field(
            path,
            "must not be empty or whitespace",
        ));
    }
    Ok(normalized)
}

fn validated_url_input(path: &str, value: &str) -> Result<String, ProcessorError> {
    if value.is_empty() {
        return Err(ProcessorError::field(path, "must not be empty"));
    }
    if value
        .chars()
        .any(|character| character.is_whitespace() || character.is_control())
    {
        return Err(ProcessorError::field(
            path,
            "contains whitespace or a control character",
        ));
    }
    Ok(value.to_owned())
}

fn normalize_display(value: &str) -> String {
    let normalized: String = value.nfkc().collect();
    normalized.split_whitespace().collect::<Vec<_>>().join(" ")
}

fn normalized_for_match(value: &str) -> String {
    normalize_display(value).to_lowercase()
}

fn validate_sha256(path: &str, value: &str) -> Result<String, ProcessorError> {
    let normalized = value.to_ascii_lowercase();
    if normalized.len() != 64 || !normalized.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(ProcessorError::field(
            path,
            "must contain exactly 64 hexadecimal characters",
        ));
    }
    Ok(normalized)
}

fn validate_expected_input_sha256(value: &str) -> Result<(), ProcessorError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(ProcessorError::field(
            "--expected-input-sha256",
            "must contain exactly 64 lowercase hexadecimal characters",
        ));
    }
    Ok(())
}

fn content_is_exact_match_eligible(content: &str) -> bool {
    let significant: Vec<char> = content
        .chars()
        .filter(|character| character.is_alphanumeric())
        .collect();
    if significant.len() < MIN_EXACT_CONTENT_CHARS {
        return false;
    }
    significant.into_iter().collect::<BTreeSet<_>>().len() >= MIN_DISTINCT_CONTENT_CHARS
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    format!("{digest:x}")
}

fn raw_host_from_authority(authority: &str) -> Result<&str, ProcessorError> {
    if authority.starts_with('[') {
        let close = authority
            .find(']')
            .ok_or_else(|| ProcessorError::new("unterminated IPv6 host"))?;
        let remainder = &authority[close + 1..];
        if !remainder.is_empty()
            && (!remainder.starts_with(':')
                || remainder.len() == 1
                || !remainder[1..].bytes().all(|byte| byte.is_ascii_digit()))
        {
            return Err(ProcessorError::new("invalid port syntax"));
        }
        return Ok(&authority[..=close]);
    }
    if authority.matches(':').count() > 1 {
        return Err(ProcessorError::new("IPv6 literals must be bracketed"));
    }
    if let Some((host, port)) = authority.rsplit_once(':') {
        if host.is_empty() || port.is_empty() || !port.bytes().all(|byte| byte.is_ascii_digit()) {
            return Err(ProcessorError::new("invalid host or port syntax"));
        }
        return Ok(host);
    }
    Ok(authority)
}

fn looks_like_legacy_ipv4(raw_host: &str) -> bool {
    if raw_host.starts_with('[') {
        return false;
    }
    let host = raw_host.trim_end_matches('.');
    if host.bytes().all(|byte| byte.is_ascii_digit()) {
        return !is_strict_dotted_decimal_ipv4(host);
    }
    let components: Vec<&str> = host.split('.').collect();
    if components.iter().any(|component| {
        component.len() > 2
            && component.starts_with("0x")
            && component[2..].bytes().all(|byte| byte.is_ascii_hexdigit())
    }) {
        return true;
    }
    if components.iter().all(|component| {
        !component.is_empty() && component.bytes().all(|byte| byte.is_ascii_digit())
    }) {
        return !is_strict_dotted_decimal_ipv4(host);
    }
    false
}

fn is_strict_dotted_decimal_ipv4(host: &str) -> bool {
    let components: Vec<&str> = host.split('.').collect();
    components.len() == 4
        && components.iter().all(|component| {
            !component.is_empty()
                && (component == &"0" || !component.starts_with('0'))
                && component
                    .parse::<u8>()
                    .is_ok_and(|_| component.bytes().all(|byte| byte.is_ascii_digit()))
        })
}

fn is_global_ipv4(address: Ipv4Addr) -> bool {
    let [a, b, c, _d] = address.octets();
    !(a == 0
        || a == 10
        || (a == 100 && (64..=127).contains(&b))
        || a == 127
        || (a == 169 && b == 254)
        || (a == 172 && (16..=31).contains(&b))
        || (a == 192 && b == 0 && c == 0)
        || (a == 192 && b == 0 && c == 2)
        || (a == 192 && b == 88 && c == 99)
        || (a == 192 && b == 168)
        || (a == 198 && (b == 18 || b == 19))
        || (a == 198 && b == 51 && c == 100)
        || (a == 203 && b == 0 && c == 113)
        || a >= 224)
}

fn is_global_ipv6(address: Ipv6Addr) -> bool {
    if address.is_unspecified() || address.is_loopback() || address.is_multicast() {
        return false;
    }
    let segments = address.segments();
    let first = segments[0];
    let second = segments[1];
    let is_ipv4_compatible = segments[..6].iter().all(|segment| *segment == 0);
    let is_ipv4_mapped = segments[..5].iter().all(|segment| *segment == 0) && segments[5] == 0xffff;
    !(
        // Global unicast assignments are inside 2000::/3. Keep this deliberately
        // conservative for an offline SSRF preflight.
        (first & 0xe000) != 0x2000
            // Discard-only, IPv4 transition, NAT64, unique-local, link/site-local.
            || is_ipv4_compatible
            || is_ipv4_mapped
            || (first == 0x0100 && second == 0)
            || (first == 0x0064 && second == 0xff9b)
            || (first == 0x0064 && second == 0xff9b && segments[2] == 1)
            || (first & 0xfe00) == 0xfc00
            || (first & 0xffc0) == 0xfe80
            || (first & 0xffc0) == 0xfec0
            // IETF special-purpose block, documentation, 6to4, and documentation v2.
            || (first == 0x2001 && second < 0x0200)
            || (first == 0x2001 && second == 0x0db8)
            || first == 0x2002
            || (first & 0xfff0) == 0x3ff0
    )
}

fn validate_dns_name(domain: &str) -> Result<(), ProcessorError> {
    if domain.is_empty() || domain.len() > 253 {
        return Err(ProcessorError::new("DNS hostname length is invalid"));
    }
    let labels: Vec<&str> = domain.split('.').collect();
    if labels.len() < 2 {
        return Err(ProcessorError::new("single-label hostnames are forbidden"));
    }
    for label in &labels {
        if label.is_empty()
            || label.len() > 63
            || !label
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || byte == b'-')
            || !label
                .as_bytes()
                .first()
                .is_some_and(u8::is_ascii_alphanumeric)
            || !label
                .as_bytes()
                .last()
                .is_some_and(u8::is_ascii_alphanumeric)
        {
            return Err(ProcessorError::new("DNS hostname syntax is invalid"));
        }
    }

    const LOCAL_OR_RESERVED_SUFFIXES: &[&str] = &[
        "localhost",
        "local",
        "localdomain",
        "internal",
        "intranet",
        "home",
        "lan",
        "corp",
        "test",
        "invalid",
        "example",
        "onion",
        "arpa",
    ];
    let final_label = labels.last().copied().unwrap_or_default();
    if LOCAL_OR_RESERVED_SUFFIXES.contains(&final_label) {
        return Err(ProcessorError::new(
            "local or reserved DNS hostname suffix is forbidden",
        ));
    }
    Ok(())
}

fn contains_encoded_unsafe_byte(input: &str) -> bool {
    let bytes = input.as_bytes();
    let mut index = 0;
    while index + 2 < bytes.len() {
        if bytes[index] == b'%'
            && let (Some(high), Some(low)) =
                (hex_value(bytes[index + 1]), hex_value(bytes[index + 2]))
        {
            let decoded = high * 16 + low;
            if decoded <= 0x20 || decoded == 0x5c || decoded == 0x7f {
                return true;
            }
            index += 3;
            continue;
        }
        index += 1;
    }
    false
}

fn hex_value(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    }
}

fn normalize_query(url: &mut Url) {
    let mut pairs: Vec<(String, String)> = url
        .query_pairs()
        .filter(|(key, _)| !is_tracking_parameter(key))
        .map(|(key, value)| (key.into_owned(), value.into_owned()))
        .collect();
    pairs.sort();
    url.set_query(None);
    if !pairs.is_empty() {
        let mut serializer = url.query_pairs_mut();
        for (key, value) in pairs {
            serializer.append_pair(&key, &value);
        }
    }
}

fn normalize_path(url: &mut Url) {
    let mut path = String::with_capacity(url.path().len());
    let mut previous_was_slash = false;
    for character in url.path().chars() {
        if character == '/' {
            if previous_was_slash {
                continue;
            }
            previous_was_slash = true;
        } else {
            previous_was_slash = false;
        }
        path.push(character);
    }
    if path.is_empty() {
        path.push('/');
    }
    while path.len() > 1 && path.ends_with('/') {
        path.pop();
    }
    url.set_path(&path);
}

fn is_tracking_parameter(parameter: &str) -> bool {
    let parameter = parameter.to_ascii_lowercase();
    parameter.starts_with("utm_")
        || matches!(
            parameter.as_str(),
            "fbclid"
                | "gclid"
                | "igshid"
                | "mc_cid"
                | "mc_eid"
                | "ref"
                | "ref_src"
                | "spm"
                | "xhstrackerid"
        )
}

fn paths_resolve_to_same_file(left: &Path, right: &Path) -> Result<bool, ProcessorError> {
    if left == right {
        return Ok(true);
    }
    let left = fs::canonicalize(left)
        .map_err(|error| ProcessorError::field(&left.display().to_string(), error))?;
    match fs::canonicalize(right) {
        Ok(right) => Ok(left == right),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(error) => Err(ProcessorError::field(&right.display().to_string(), error)),
    }
}

fn build_exact_clusters(processed: &[ProcessedCandidate]) -> (Vec<ExactCluster>, Vec<usize>) {
    let mut keys: BTreeMap<String, Vec<usize>> = BTreeMap::new();
    for (index, candidate) in processed.iter().enumerate() {
        keys.entry(format!("canonical_url:{}", candidate.canonical_url))
            .or_default()
            .push(index);
        if let Some(native_id) = &candidate.platform_native_id {
            keys.entry(format!(
                "platform_native_id:{}:{}",
                candidate.platform,
                normalized_for_match(native_id)
            ))
            .or_default()
            .push(index);
        }
        if candidate.strict_content_match_eligible {
            keys.entry(format!(
                "strict_content_fingerprint_sha256:{}",
                candidate.strict_content_fingerprint_sha256
            ))
            .or_default()
            .push(index);
        }
    }

    let mut disjoint_set = DisjointSet::new(processed.len());
    for indexes in keys.values().filter(|indexes| indexes.len() > 1) {
        for &index in &indexes[1..] {
            disjoint_set.union(indexes[0], index);
        }
    }
    let roots: Vec<usize> = (0..processed.len())
        .map(|index| disjoint_set.find(index))
        .collect();

    let mut groups: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
    for (index, &root) in roots.iter().enumerate() {
        groups.entry(root).or_default().push(index);
    }
    let mut evidence_by_root: BTreeMap<usize, BTreeSet<String>> = BTreeMap::new();
    for (key, indexes) in &keys {
        if indexes.len() > 1 {
            let root = roots[indexes[0]];
            if indexes.iter().all(|&index| roots[index] == root) {
                evidence_by_root
                    .entry(root)
                    .or_default()
                    .insert(key.clone());
            }
        }
    }

    let mut clusters = Vec::new();
    for (root, indexes) in groups.into_iter().filter(|(_, indexes)| indexes.len() > 1) {
        let candidate_ids: Vec<String> = indexes
            .iter()
            .map(|&index| processed[index].candidate_id.clone())
            .collect();
        let cluster_material = format!("top50-exact-cluster/v1\0{}", candidate_ids.join("\0"));
        clusters.push(ExactCluster {
            cluster_id: format!("exact-{}", &sha256_hex(cluster_material.as_bytes())[..16]),
            representative_candidate_id: candidate_ids[0].clone(),
            candidate_ids,
            evidence: evidence_by_root
                .remove(&root)
                .unwrap_or_default()
                .into_iter()
                .collect(),
        });
    }
    clusters.sort_by(|left, right| left.candidate_ids.cmp(&right.candidate_ids));
    (clusters, roots)
}

fn build_near_duplicate_reviews(
    processed: &[ProcessedCandidate],
    roots: &[usize],
) -> Vec<NearDuplicateReview> {
    let shingles: Vec<BTreeSet<String>> = processed
        .iter()
        .map(|candidate| content_shingles(&candidate.near_duplicate_text))
        .collect();
    let mut reviews = Vec::new();
    for left in 0..processed.len() {
        if shingles[left].is_empty() {
            continue;
        }
        for right in left + 1..processed.len() {
            if roots[left] == roots[right] || shingles[right].is_empty() {
                continue;
            }
            let intersection = shingles[left].intersection(&shingles[right]).count();
            let union = shingles[left].union(&shingles[right]).count();
            let similarity = ((intersection * 10_000 + union / 2) / union) as u16;
            if similarity < NEAR_DUPLICATE_MIN_BASIS_POINTS {
                continue;
            }
            let candidate_ids = vec![
                processed[left].candidate_id.clone(),
                processed[right].candidate_id.clone(),
            ];
            let review_material = format!("top50-near-review/v1\0{}", candidate_ids.join("\0"));
            reviews.push(NearDuplicateReview {
                review_id: format!("near-{}", &sha256_hex(review_material.as_bytes())[..16]),
                candidate_ids,
                similarity_basis_points: similarity,
                method: "normalized_alphanumeric_5gram_jaccard/v1",
                disposition: "manual_review_only",
            });
        }
    }
    reviews.sort_by(|left, right| left.candidate_ids.cmp(&right.candidate_ids));
    reviews
}

fn content_shingles(content: &str) -> BTreeSet<String> {
    let characters: Vec<char> = content
        .chars()
        .filter(|character| character.is_alphanumeric())
        .collect();
    if characters.len() < MIN_EXACT_CONTENT_CHARS {
        return BTreeSet::new();
    }
    characters
        .windows(SHINGLE_WIDTH)
        .map(|window| window.iter().collect())
        .collect()
}

fn atomic_write(output_path: &Path, contents: &[u8]) -> Result<(), ProcessorError> {
    let parent = output_path
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let filename = output_path
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| ProcessorError::new("output path must end in a UTF-8 filename"))?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| ProcessorError::new(error.to_string()))?
        .as_nanos();
    let temporary_path: PathBuf = parent.join(format!(
        ".{filename}.rust-processor-{}-{nonce}.tmp",
        std::process::id()
    ));

    let write_result = (|| -> Result<(), ProcessorError> {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary_path)?;
        file.write_all(contents)?;
        file.sync_all()?;
        drop(file);
        fs::rename(&temporary_path, output_path)?;
        File::open(parent)?.sync_all()?;
        Ok(())
    })();
    if write_result.is_err() {
        let _ = fs::remove_file(&temporary_path);
    }
    write_result
}

struct DisjointSet {
    parent: Vec<usize>,
    rank: Vec<u8>,
}

impl DisjointSet {
    fn new(size: usize) -> Self {
        Self {
            parent: (0..size).collect(),
            rank: vec![0; size],
        }
    }

    fn find(&mut self, item: usize) -> usize {
        if self.parent[item] != item {
            self.parent[item] = self.find(self.parent[item]);
        }
        self.parent[item]
    }

    fn union(&mut self, left: usize, right: usize) {
        let left_root = self.find(left);
        let right_root = self.find(right);
        if left_root == right_root {
            return;
        }
        match self.rank[left_root].cmp(&self.rank[right_root]) {
            std::cmp::Ordering::Less => self.parent[left_root] = right_root,
            std::cmp::Ordering::Greater => self.parent[right_root] = left_root,
            std::cmp::Ordering::Equal => {
                self.parent[right_root] = left_root;
                self.rank[left_root] += 1;
            }
        }
    }
}

#[cfg(test)]
mod unit_tests {
    use super::*;

    #[test]
    fn query_tracking_detection_is_narrow_and_case_insensitive() {
        assert!(is_tracking_parameter("UTM_Source"));
        assert!(is_tracking_parameter("fbclid"));
        assert!(!is_tracking_parameter("source"));
        assert!(!is_tracking_parameter("from"));
    }

    #[test]
    fn eligibility_rejects_short_or_degenerate_content() {
        assert!(!content_is_exact_match_eligible("read more"));
        assert!(!content_is_exact_match_eligible(&"a".repeat(100)));
        assert!(content_is_exact_match_eligible(
            "A sufficiently varied explanation with methods, evidence, limitations, dates, sources, and reproducible details for an independent reviewer."
        ));
    }
}

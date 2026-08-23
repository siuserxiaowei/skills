use rust_processor::{normalize_and_validate_url, process_json_slice};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

const LONG_EXCERPT: &str = "A reproducible investigation records the source, method, evidence, limitations, and result so an independent reviewer can verify every material claim.";

fn candidate(id: &str, platform: &str, url: &str, excerpt: &str) -> Value {
    json!({
        "candidate_id": id,
        "platform": platform,
        "url": url,
        "title": "Evidence-first research workflow",
        "author": "Research Team",
        "published_at": "2026-08-24",
        "excerpt": excerpt
    })
}

fn input(candidates: Vec<Value>) -> Vec<u8> {
    serde_json::to_vec(&json!({
        "contract_version": "top50-processor/v1",
        "run_id": "run-20260824",
        "candidates": candidates
    }))
    .unwrap()
}

fn process(candidates: Vec<Value>) -> Value {
    let bytes = process_json_slice(&input(candidates)).expect("processing should succeed");
    serde_json::from_slice(&bytes).unwrap()
}

#[test]
fn obeys_the_reusable_cross_language_canonical_url_fixture() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/canonical-url-v1.json")).unwrap();
    assert_eq!(
        fixture["contract_version"],
        "top50-canonical-url-fixture/v1"
    );
    for case in fixture["accepted"].as_array().unwrap() {
        let normalized = normalize_and_validate_url(case["input"].as_str().unwrap())
            .unwrap_or_else(|error| panic!("fixture case {} failed: {error}", case["name"]));
        assert_eq!(
            normalized.canonical_url, case["canonical_url"],
            "fixture case {}",
            case["name"]
        );
        assert_eq!(
            normalized.requires_fetch_time_dns_validation,
            case["requires_fetch_time_dns_validation"]
                .as_bool()
                .unwrap(),
            "fixture case {}",
            case["name"]
        );
    }
}

#[test]
fn canonicalizes_urls_and_unifies_http_https_identity() {
    let http = normalize_and_validate_url(
        "http://Example.COM:80/a/../b/?utm_source=newsletter&b=2&a=1#section",
    )
    .unwrap();
    let https = normalize_and_validate_url("https://example.com:443/b/?a=1&b=2").unwrap();

    assert_eq!(http.canonical_url, "https://example.com/b?a=1&b=2");
    assert_eq!(http.canonical_url, https.canonical_url);
    assert!(http.requires_fetch_time_dns_validation);

    let public_ip = normalize_and_validate_url("https://8.8.8.8/path").unwrap();
    assert!(!public_ip.requires_fetch_time_dns_validation);
}

#[test]
fn canonical_identity_matches_ranker_path_and_www_rules() {
    let first =
        normalize_and_validate_url("https://www.example.com/a//b///?utm_campaign=x&z=9").unwrap();
    let second = normalize_and_validate_url("http://example.com/a/b?z=9").unwrap();

    assert_eq!(first.canonical_url, "https://example.com/a/b?z=9");
    assert_eq!(first.canonical_url, second.canonical_url);
}

#[test]
fn rejects_even_leading_or_trailing_whitespace_in_candidate_urls() {
    let leading = candidate(
        "a",
        "github",
        " https://github.com/openai/codex",
        LONG_EXCERPT,
    );
    let trailing = candidate(
        "b",
        "github",
        "https://github.com/openai/codex ",
        LONG_EXCERPT,
    );

    assert!(process_json_slice(&input(vec![leading])).is_err());
    assert!(process_json_slice(&input(vec![trailing])).is_err());
}

#[test]
fn removes_known_tracking_parameters_but_preserves_content_parameters() {
    let normalized = normalize_and_validate_url(
        "https://example.com/watch?utm_medium=social&v=42&fbclid=secret&lang=zh-CN",
    )
    .unwrap();

    assert_eq!(
        normalized.canonical_url,
        "https://example.com/watch?lang=zh-CN&v=42"
    );
}

#[test]
fn rejects_unsafe_schemes_credentials_whitespace_and_local_names() {
    let rejected = [
        "ftp://example.com/file",
        "https://user:password@example.com/private",
        "https://example.com/a b",
        "https://example.com/a\\b",
        "https://localhost/path",
        "https://api.localhost/path",
        "https://printer.local/path",
        "https://service.internal/path",
        "https://intranet/path",
        "https://bad_label.example.com/path",
        "https://-bad.example.com/path",
    ];

    for url in rejected {
        assert!(
            normalize_and_validate_url(url).is_err(),
            "unsafe URL was accepted: {url}"
        );
    }
}

#[test]
fn rejects_private_special_and_legacy_ipv4_forms() {
    let rejected = [
        "http://0.0.0.0/",
        "http://10.0.0.1/",
        "http://100.64.0.1/",
        "http://127.0.0.1/",
        "http://169.254.1.1/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://192.0.2.1/",
        "http://198.18.0.1/",
        "http://198.51.100.1/",
        "http://203.0.113.1/",
        "http://224.0.0.1/",
        "http://240.0.0.1/",
        "http://127.1/",
        "http://2130706433/",
        "http://0177.0.0.1/",
        "http://0x7f.0.0.1/",
        "http://1.2.3/",
    ];

    for url in rejected {
        assert!(
            normalize_and_validate_url(url).is_err(),
            "special or legacy IPv4 URL was accepted: {url}"
        );
    }
}

#[test]
fn rejects_non_global_ipv6_literals() {
    let rejected = [
        "http://[::]/",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
        "http://[ff02::1]/",
        "http://[2001:db8::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://[4000::1]/",
        "http://[5f00::1]/",
    ];

    for url in rejected {
        assert!(
            normalize_and_validate_url(url).is_err(),
            "non-global IPv6 URL was accepted: {url}"
        );
    }

    assert!(normalize_and_validate_url("https://[2606:4700:4700::1111]/").is_ok());
}

#[test]
fn rejects_ipv4_compatible_ipv6_literals() {
    let rejected = [
        "http://[::192.0.2.1]/",
        "http://[::8.8.8.8]/",
        "http://[64:ff9b::8.8.8.8]/",
    ];

    for url in rejected {
        assert!(
            normalize_and_validate_url(url).is_err(),
            "special IPv4 transition URL was accepted: {url}"
        );
    }
}

#[test]
fn rejects_missing_empty_and_duplicate_candidate_ids() {
    let mut missing = candidate("a", "github", "https://github.com/a/repo", LONG_EXCERPT);
    missing.as_object_mut().unwrap().remove("candidate_id");
    assert!(process_json_slice(&input(vec![missing])).is_err());

    let empty = candidate(" ", "github", "https://github.com/a/repo", LONG_EXCERPT);
    assert!(process_json_slice(&input(vec![empty])).is_err());

    let duplicate_a = candidate("same", "github", "https://github.com/a/a", LONG_EXCERPT);
    let duplicate_b = candidate(
        "same",
        "youtube",
        "https://youtube.com/watch?v=1",
        LONG_EXCERPT,
    );
    assert!(process_json_slice(&input(vec![duplicate_a, duplicate_b])).is_err());
}

#[test]
fn rejects_wrong_contract_and_invalid_body_digest() {
    let wrong_contract = serde_json::to_vec(&json!({
        "contract_version": "top50-processor/v2",
        "run_id": "run",
        "candidates": []
    }))
    .unwrap();
    assert!(process_json_slice(&wrong_contract).is_err());

    let mut bad_digest = candidate("a", "github", "https://github.com/a/a", LONG_EXCERPT);
    bad_digest["body_or_transcript_sha256"] = json!("not-a-sha256");
    assert!(process_json_slice(&input(vec![bad_digest])).is_err());
}

#[test]
fn accepts_forward_compatible_extra_metadata() {
    let mut with_extra = candidate("a", "github", "https://github.com/a/a", LONG_EXCERPT);
    with_extra["engagement"] = json!({"likes": 42});
    with_extra["language"] = json!("en");

    let output = process(vec![with_extra]);
    assert_eq!(output["counts"]["processed_candidates"], 1);
}

#[test]
fn supplied_body_digests_are_not_enough_to_merge_different_metadata() {
    let mut first = candidate("a", "github", "https://github.com/a/a", LONG_EXCERPT);
    let mut second = candidate(
        "b",
        "youtube",
        "https://youtube.com/watch?v=body",
        LONG_EXCERPT,
    );
    first["body_or_transcript_sha256"] =
        json!("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    second["body_or_transcript_sha256"] =
        json!("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    second["author"] = json!("Different Author");

    let output = process(vec![first, second]);
    assert_eq!(output["exact_clusters"], json!([]));
}

#[test]
fn fingerprint_includes_metadata_and_content_to_prevent_false_exact_merges() {
    let first = candidate(
        "a",
        "github",
        "https://github.com/org/one",
        "This first report contains a long, independently verifiable description of alpha findings, collection methods, evidence, and limitations.",
    );
    let second = candidate(
        "b",
        "youtube",
        "https://youtube.com/watch?v=different",
        "This second report contains a long, independently verifiable description of beta findings, interview methods, counterevidence, and conclusions.",
    );

    let output = process(vec![first, second]);
    assert_eq!(output["exact_clusters"], json!([]));
    assert_ne!(
        output["processed_candidates"][0]["strict_content_fingerprint_sha256"],
        output["processed_candidates"][1]["strict_content_fingerprint_sha256"]
    );
}

#[test]
fn identical_cross_posts_form_an_exact_cluster_without_deleting_candidates() {
    let first = candidate(
        "a",
        "csdn",
        "https://blog.csdn.net/a/article/1",
        LONG_EXCERPT,
    );
    let second = candidate(
        "b",
        "zhihu",
        "https://zhuanlan.zhihu.com/p/999",
        LONG_EXCERPT,
    );

    let output = process(vec![first, second]);
    assert_eq!(output["processed_candidates"].as_array().unwrap().len(), 2);
    assert_eq!(output["exact_clusters"].as_array().unwrap().len(), 1);
    assert_eq!(
        output["exact_clusters"][0]["candidate_ids"],
        json!(["a", "b"])
    );
    assert_eq!(output["counts"]["exact_duplicate_candidates"], 1);
}

#[test]
fn native_ids_are_scoped_to_platform() {
    let mut first = candidate("a", "github", "https://github.com/org/a", LONG_EXCERPT);
    let mut second = candidate(
        "b",
        "github",
        "https://github.com/org/b",
        "A completely different and sufficiently long report about beta systems and their measured operational behavior in production.",
    );
    let mut third = candidate(
        "c",
        "youtube",
        "https://youtube.com/watch?v=123",
        "Another unrelated and sufficiently long transcript about gamma systems, deployment risks, and practical maintenance lessons.",
    );
    first["platform_native_id"] = json!("shared-42");
    second["platform_native_id"] = json!("shared-42");
    third["platform_native_id"] = json!("shared-42");

    let output = process(vec![first, second, third]);
    assert_eq!(output["exact_clusters"].as_array().unwrap().len(), 1);
    assert_eq!(
        output["exact_clusters"][0]["candidate_ids"],
        json!(["a", "b"])
    );
}

#[test]
fn exact_evidence_is_merged_transitively() {
    let first = candidate(
        "a",
        "csdn",
        "http://blog.csdn.net/author/post?utm_source=x",
        "A different but long source excerpt that deliberately prevents a strict content match while retaining enough material for reliable processing.",
    );
    let second = candidate(
        "b",
        "zhihu",
        "https://blog.csdn.net/author/post",
        LONG_EXCERPT,
    );
    let third = candidate(
        "c",
        "youtube",
        "https://youtube.com/watch?v=transitive",
        LONG_EXCERPT,
    );

    let output = process(vec![third, first, second]);
    assert_eq!(output["exact_clusters"].as_array().unwrap().len(), 1);
    assert_eq!(
        output["exact_clusters"][0]["candidate_ids"],
        json!(["a", "b", "c"])
    );
    assert!(
        output["exact_clusters"][0]["evidence"]
            .as_array()
            .unwrap()
            .len()
            >= 2
    );
}

#[test]
fn near_duplicates_are_review_flags_and_are_not_auto_deleted() {
    let first = candidate(
        "a",
        "bilibili",
        "https://www.bilibili.com/video/BV1aaa",
        "The benchmark measures discovery coverage, source traceability, publication date, author identity, evidence quality, and reproducibility across twenty-eight platforms before ranking every candidate.",
    );
    let second = candidate(
        "b",
        "youtube",
        "https://youtube.com/watch?v=near",
        "The benchmark measures discovery coverage, source traceability, publication date, author identity, evidence strength, and reproducibility across twenty-eight platforms before ranking every candidate.",
    );

    let output = process(vec![first, second]);
    assert_eq!(output["exact_clusters"], json!([]));
    assert_eq!(
        output["near_duplicate_reviews"].as_array().unwrap().len(),
        1
    );
    assert_eq!(output["processed_candidates"].as_array().unwrap().len(), 2);
    assert_eq!(
        output["near_duplicate_reviews"][0]["disposition"],
        "manual_review_only"
    );
}

#[test]
fn output_and_digest_are_deterministic_independent_of_input_order() {
    let a = candidate(
        "a",
        "github",
        "https://github.com/org/a?utm_source=x",
        LONG_EXCERPT,
    );
    let b = candidate(
        "b",
        "youtube",
        "https://youtube.com/watch?v=deterministic",
        "A distinct and sufficiently detailed transcript used to demonstrate deterministic ordering, hashing, comparison, and serialization behavior.",
    );

    let forward: Value =
        serde_json::from_slice(&process_json_slice(&input(vec![a.clone(), b.clone()])).unwrap())
            .unwrap();
    let reverse: Value =
        serde_json::from_slice(&process_json_slice(&input(vec![b, a])).unwrap()).unwrap();

    assert_eq!(forward, reverse);
    assert_eq!(forward["contract_version"], "top50-processor-result/v1");
    assert_eq!(forward["result_digest_sha256"].as_str().unwrap().len(), 64);
    let declared = forward["result_digest_sha256"].as_str().unwrap().to_owned();
    let mut digest_material = forward.clone();
    digest_material
        .as_object_mut()
        .unwrap()
        .remove("result_digest_sha256");
    let recomputed = format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&digest_material).unwrap())
    );
    assert_eq!(declared, recomputed);
}

#[test]
fn short_generic_excerpts_do_not_create_content_exact_clusters() {
    let first = candidate("a", "csdn", "https://blog.csdn.net/a/1", "Read more");
    let second = candidate("b", "zhihu", "https://zhihu.com/question/1", "Read more");

    let output = process(vec![first, second]);
    assert_eq!(output["exact_clusters"], json!([]));
    assert_eq!(
        output["processed_candidates"][0]["strict_content_match_eligible"],
        false
    );
}

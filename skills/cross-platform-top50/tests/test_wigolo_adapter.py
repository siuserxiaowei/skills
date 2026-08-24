from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import jsonschema


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "wigolo_adapter.py"
SCHEMAS = ROOT / "assets" / "engine-contracts"
SPEC = importlib.util.spec_from_file_location("wigolo_adapter_v2_test", SCRIPT)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def request(operation: str = "discovery", payload: dict[str, object] | None = None):
    defaults = {
        "discovery": {"query": "agent research", "max_results": 5},
        "fetch": {"url": "https://example.com/article", "max_chars": 5000},
        "cache": {"action": "stats"},
        "watch": {"action": "list"},
    }
    return {
        "contract_version": adapter.REQUEST_CONTRACT,
        "run_id": "run-wigolo-v2",
        "enabled": True,
        "selection_mode": "explicit",
        "operation": operation,
        "allow_experimental_cjk": False,
        "timeout_seconds": 30,
        "payload": payload if payload is not None else defaults[operation],
    }


def completed(payload: object, returncode: int = 0):
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=json.dumps(payload), stderr=""
    )


def probe_runner(calls: list[dict[str, object]] | None = None):
    def run(argv, **kwargs):
        if calls is not None:
            calls.append({"argv": list(argv), **kwargs})
        if argv[1:] == ["doctor", "--json"]:
            return completed({"status": "ok", "exitCode": 0, "version": "0.2.1"})
        if argv[1:] == ["search", "--json"]:
            return completed({"results": [], "error": "missing query"}, 1)
        if argv[1:] == ["fetch", "--json"]:
            return completed({"url": "", "error": "missing url"}, 1)
        if argv[1:] == ["cache", "stats", "--json"]:
            return completed({"stats": {}})
        if argv[1:] == ["watch", "list", "--json"]:
            return completed({"jobs": []})
        raise AssertionError(argv)
    return run


def make_executable(root: Path) -> Path:
    path = root / "wigolo"
    source = Path(sys.executable).resolve()
    if not source.is_file():
        raise unittest.SkipTest("a native host executable is required")
    shutil.copyfile(source, path)
    path.chmod(0o755)
    return path


def make_node_package_executable(root: Path) -> tuple[Path, Path]:
    package = root / "node_modules" / "wigolo"
    entry = package / "dist" / "index.js"
    dependency = package / "dist" / "cli" / "index.js"
    dependency.parent.mkdir(parents=True)
    (package / "package.json").write_text(
        json.dumps({"name": "wigolo", "version": "0.2.1", "type": "module"}),
        encoding="utf-8",
    )
    entry.write_text(
        "#!/usr/bin/env node\nimport { emit } from './cli/index.js';\nemit();\n",
        encoding="utf-8",
    )
    dependency.write_text(
        "export function emit() {\n"
        "  process.stdout.write(JSON.stringify({\n"
        "    query: 'agent research',\n"
        "    results: [{title: 'Research result', url: 'https://example.com/article', "
        "snippet: 'A useful public result.', relevance_score: 0.9}],\n"
        "    engines_used: ['core'], total_time_ms: 12, error: ''\n"
        "  }));\n"
        "}\n",
        encoding="utf-8",
    )
    entry.chmod(0o755)
    dependency.chmod(0o644)
    return entry, dependency


def make_auth_key(root: Path, name: str = "wigolo-auth.key") -> Path:
    path = root / name
    path.write_bytes(b"test-only-wigolo-hmac-key-material-32-bytes")
    path.chmod(0o600)
    return path


def signed_plan(root: Path, operation: str = "discovery", payload=None):
    executable = make_executable(root)
    plan = adapter.plan_request(
        request(operation, payload), command=str(executable), runner=probe_runner()
    )
    if plan.get("contract_version") != adapter.PLAN_CONTRACT:
        raise AssertionError(plan)
    return plan


def discovery_output(**extra):
    value = {
        "query": "agent research",
        "results": [
            {
                "title": "Research result",
                "url": "https://example.com/article",
                "snippet": "A useful public result.",
                "relevance_score": 0.9,
            }
        ],
        "engines_used": ["core"],
        "total_time_ms": 12,
        "error": "",
    }
    value.update(extra)
    return value


def fetch_output(**extra):
    value = {
        "url": "https://example.com/article",
        "title": "Fetched article",
        "markdown": "# Fetched article\n\nUseful public content.",
        "metadata": {"content_type": "text/html"},
        "cached": False,
        "fetch_method": "http",
        "links": ["https://example.com/reference"],
        "images": [{"url": "https://example.com/image.png"}],
        "http_status": 200,
    }
    value.update(extra)
    return value


def reseal_result(value, auth_key=None):
    value["result_digest_sha256"] = adapter._digest(
        {
            key: item
            for key, item in value.items()
            if key not in {"result_digest_sha256", "result_hmac_sha256"}
        }
    )
    if "result_hmac_sha256" in value:
        key = adapter._PROCESS_AUTH_KEY if auth_key is None else auth_key
        value["result_hmac_sha256"] = adapter._hmac_digest(
            key,
            adapter.RESULT_HMAC_CONTEXT,
            {field: item for field, item in value.items() if field != "result_hmac_sha256"},
        )
    return value


class WigoloV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_audited_digests = adapter.AUDITED_NATIVE_RELEASE_SHA256
        adapter.AUDITED_NATIVE_RELEASE_SHA256 = frozenset(
            {hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()}
        )

    @classmethod
    def tearDownClass(cls):
        adapter.AUDITED_NATIVE_RELEASE_SHA256 = cls._original_audited_digests

    def test_four_contract_schemas_meta_validate_and_match_runtime_versions(self):
        expected = {
            "wigolo-probe.schema.json": adapter.PROBE_CONTRACT,
            "wigolo-request.schema.json": adapter.REQUEST_CONTRACT,
            "wigolo-plan.schema.json": adapter.PLAN_CONTRACT,
            "wigolo-result.schema.json": adapter.RESULT_CONTRACT,
        }
        for filename, contract in expected.items():
            schema = json.loads((SCHEMAS / filename).read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
            self.assertEqual(schema["$id"], contract)

    def test_signed_probe_plan_and_result_validate_against_schemas(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            probe = adapter.probe(command=str(executable), runner=probe_runner())
            plan = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner()
            )
            result = adapter.execute_plan(
                plan, runner=lambda argv, **kw: completed(discovery_output())
            )
            values = (
                ("wigolo-probe.schema.json", probe),
                ("wigolo-request.schema.json", request()),
                ("wigolo-plan.schema.json", plan),
                ("wigolo-result.schema.json", result),
            )
            for filename, value in values:
                schema = json.loads((SCHEMAS / filename).read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator(schema).validate(value)

    def test_every_success_operation_matches_the_published_result_schema(self):
        schema = json.loads(
            (SCHEMAS / "wigolo-result.schema.json").read_text(encoding="utf-8")
        )
        validator = jsonschema.Draft202012Validator(schema)
        fixtures = (
            ("discovery", None, discovery_output()),
            ("fetch", None, fetch_output()),
            (
                "cache",
                {"action": "stats"},
                {
                    "stats": {
                        "total_urls": 3,
                        "total_size_mb": 1.25,
                        "oldest": "2026-07-01T00:00:00Z",
                        "newest": "2026-07-31T00:00:00Z",
                    }
                },
            ),
            (
                "cache",
                {"action": "search", "query": "agent research"},
                {
                    "results": [
                        {
                            "url": "https://example.com/article",
                            "title": "Cached article",
                            "markdown": "Cached public content.",
                            "fetched_at": "2026-07-30T10:00:00Z",
                        }
                    ]
                },
            ),
            (
                "watch",
                {"action": "list"},
                {
                    "jobs": [
                        {
                            "id": "watch-1",
                            "url": "https://example.com/article",
                            "interval_seconds": 60,
                            "status": "active",
                            "notification": None,
                            "created_at": "2026-07-30T10:00:00Z",
                            "selector": None,
                        }
                    ]
                },
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for operation, payload, output in fixtures:
                with self.subTest(operation=operation, payload=payload):
                    plan = signed_plan(root, operation, payload)
                    result = adapter.execute_plan(
                        plan,
                        runner=lambda argv, output=output, **kwargs: completed(output),
                    )
                    self.assertEqual(result["outcome"], "success")
                    validator.validate(result)

    def test_executable_sha_is_bound_and_rewrite_is_rejected_before_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            Path(plan["executable"]["path"]).write_text(
                "#!/bin/sh\nexit 9\n", encoding="utf-8"
            )
            calls = []
            result = adapter.execute_plan(
                plan, runner=lambda *a, **k: calls.append((a, k))
            )
            self.assertEqual(result["outcome"], "executable_mismatch")
            self.assertEqual(calls, [])

    def test_verified_executable_is_snapshotted_before_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = signed_plan(root)
            original_path = Path(plan["executable"]["path"])
            seen = []

            def runner(argv, **kwargs):
                seen.append(
                    {
                        "argv": list(argv),
                        "bytes": Path(argv[0]).read_bytes(),
                        "original": original_path.read_bytes(),
                    }
                )
                return completed(discovery_output())

            result = adapter.execute_plan(plan, runner=runner)
            self.assertEqual(result["outcome"], "success")
            self.assertNotEqual(seen[0]["argv"][0], str(original_path))
            self.assertEqual(
                hashlib.sha256(seen[0]["bytes"]).hexdigest(),
                plan["executable"]["sha256"],
            )
            self.assertEqual(seen[0]["bytes"], seen[0]["original"])

    def test_node_package_is_rejected_before_any_probe_or_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable, _dependency = make_node_package_executable(root)
            calls = []
            plan = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner(calls)
            )
            self.assertEqual(plan["outcome"], "backend_not_ready")
            self.assertEqual(calls, [])

    def test_probe_rejects_scripts_before_calling_runner(self):
        fixtures = {
            "dist/index.js": b"import './outside.mjs';\n",
            "plain-script": b"#!/bin/sh\nexit 0\n",
            "extensionless-node": b"#!/usr/bin/env node\nrequire('/outside.cjs');\n",
            "dynamic-import.mjs": b"const p='/outside.mjs'; import(p);\n",
            "dynamic-require.cjs": b"const p='/outside.cjs'; require(p);\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative, raw in fixtures.items():
                with self.subTest(relative=relative):
                    executable = root / relative
                    executable.parent.mkdir(parents=True, exist_ok=True)
                    executable.write_bytes(raw)
                    executable.chmod(0o755)
                    calls = []
                    observed = adapter.probe(
                        command=str(executable), runner=probe_runner(calls)
                    )
                    self.assertEqual(observed["outcome"], "executable_unavailable")
                    self.assertEqual(calls, [])

    def test_unaudited_native_digest_is_rejected_before_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = make_executable(Path(directory))
            calls = []
            with patch.object(adapter, "AUDITED_NATIVE_RELEASE_SHA256", frozenset()):
                observed = adapter.probe(
                    command=str(executable), runner=probe_runner(calls)
                )
            self.assertEqual(observed["outcome"], "executable_unavailable")
            self.assertEqual(calls, [])

    def test_renamed_native_interpreter_is_rejected_by_release_digest_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            interpreter = make_executable(root)
            renamed = root / "wigolo-renamed"
            interpreter.rename(renamed)
            calls = []
            with patch.object(adapter, "AUDITED_NATIVE_RELEASE_SHA256", frozenset()):
                observed = adapter.probe(
                    command=str(renamed), runner=probe_runner(calls)
                )
            self.assertEqual(observed["outcome"], "executable_unavailable")
            self.assertEqual(calls, [])

    def test_command_symlink_binds_final_native_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = make_executable(root)
            command = root / "wigolo-command"
            command.symlink_to(target)
            plan = adapter.plan_request(
                request(), command=str(command), runner=probe_runner()
            )
            self.assertEqual(plan["contract_version"], adapter.PLAN_CONTRACT)
            self.assertEqual(plan["executable"]["path"], str(target.resolve()))
            self.assertEqual(
                plan["executable"]["sha256"],
                hashlib.sha256(target.read_bytes()).hexdigest(),
            )

    def test_command_symlink_to_native_package_runner_is_rejected_before_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = make_executable(root)
            node_target = root / "node"
            target.rename(node_target)
            command = root / "wigolo"
            command.symlink_to(node_target)
            calls = []

            observed = adapter.probe(
                command=str(command), runner=probe_runner(calls)
            )

            self.assertEqual(observed["outcome"], "auto_install_command_forbidden")
            self.assertEqual(calls, [])

    def test_node_package_cannot_create_a_plan_to_rewrite_afterward(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable, dependency = make_node_package_executable(root)
            result = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner()
            )
            dependency.write_text(
                "throw new Error('attacker replacement');\n", encoding="utf-8"
            )
            self.assertEqual(result["outcome"], "backend_not_ready")

    def test_node_package_symlink_is_rejected_when_binding_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable, dependency = make_node_package_executable(root)
            external = root / "outside.js"
            external.write_text("export function emit() {}\n", encoding="utf-8")
            dependency.unlink()
            dependency.symlink_to(external)

            result = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner()
            )

            self.assertEqual(result["outcome"], "backend_not_ready")
            self.assertEqual(
                [row["code"] for row in result["diagnostics"]],
                ["backend_not_ready"],
            )

    def test_node_package_with_hoisted_bare_dependency_is_not_claimed_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable, dependency = make_node_package_executable(root)
            dependency.write_text(
                "import Database from 'better-sqlite3';\n"
                "export function emit() { new Database(':memory:'); }\n",
                encoding="utf-8",
            )
            hoisted = root / "node_modules" / "better-sqlite3" / "index.js"
            hoisted.parent.mkdir(parents=True)
            hoisted.write_text("export default class Database {}\n", encoding="utf-8")

            result = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner()
            )

            self.assertEqual(result["outcome"], "backend_not_ready")
            self.assertEqual(
                [row["code"] for row in result["diagnostics"]],
                ["backend_not_ready"],
            )

    def test_node_package_side_effect_import_cannot_escape_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, specifier in enumerate(
                ("bare-module", str(root / "outside.mjs")), start=1
            ):
                with self.subTest(specifier=specifier):
                    executable, dependency = make_node_package_executable(
                        root / f"case-{index}"
                    )
                    dependency.write_text(
                        f"import {json.dumps(specifier)};\n"
                        "export function emit() {}\n",
                        encoding="utf-8",
                    )

                    result = adapter.plan_request(
                        request(), command=str(executable), runner=probe_runner()
                    )

                    self.assertEqual(result["outcome"], "backend_not_ready")
                    self.assertEqual(
                        [row["code"] for row in result["diagnostics"]],
                        ["backend_not_ready"],
                    )

    def test_node_package_variable_module_load_cannot_escape_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = (
                "const p = '/tmp/outside.mjs'; await import(p);\n",
                "const p = '/tmp/outside.cjs'; require(p);\n",
                "await import('./cli/' + 'outside.js');\n",
            )
            for index, loader in enumerate(cases, start=1):
                with self.subTest(loader=loader):
                    executable, dependency = make_node_package_executable(
                        root / f"case-{index}"
                    )
                    dependency.write_text(
                        loader + "export function emit() {}\n",
                        encoding="utf-8",
                    )

                    result = adapter.plan_request(
                        request(), command=str(executable), runner=probe_runner()
                    )

                    self.assertEqual(result["outcome"], "backend_not_ready")
                    self.assertEqual(
                        [row["code"] for row in result["diagnostics"]],
                        ["backend_not_ready"],
                    )

    def test_node_package_literal_relative_dynamic_import_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable, dependency = make_node_package_executable(root)
            dependency.write_text(
                "export function emit() {\n"
                "  return import('./payload.js').then(({ payload }) => "
                "process.stdout.write(JSON.stringify(payload)));\n"
                "}\n",
                encoding="utf-8",
            )
            (dependency.parent / "payload.js").write_text(
                "export const payload = " + json.dumps(discovery_output()) + ";\n",
                encoding="utf-8",
            )

            result = adapter.plan_request(
                request(), command=str(executable), runner=probe_runner()
            )
            self.assertEqual(result["outcome"], "backend_not_ready")

    def test_node_script_is_rejected_without_a_preopen_closure_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable_path, _dependency = make_node_package_executable(root)
            outside = root / "outside.mjs"
            outside.write_text("export function emit() {}\n", encoding="utf-8")
            replacement = (
                "#!/usr/bin/env node\n"
                f"import {json.dumps(str(outside))};\n"
            )
            original_open = adapter._opened_file
            replaced = False

            def replace_before_open(path, *, executable=False):
                nonlocal replaced
                if Path(path) == executable_path and not replaced:
                    Path(path).write_text(replacement, encoding="utf-8")
                    Path(path).chmod(0o755)
                    replaced = True
                return original_open(path, executable=executable)

            with patch.object(adapter, "_opened_file", side_effect=replace_before_open):
                result = adapter.plan_request(
                    request(), command=str(executable_path), runner=probe_runner()
                )

            self.assertFalse(replaced)
            self.assertEqual(result.get("outcome"), "backend_not_ready")

    def test_command_replacement_between_resolution_and_open_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable_path = make_executable(root)
            calls = []
            replaced = False

            original_resolve = adapter._resolved_native_source

            def replace_after_resolution(path, *, allow_command_symlink=False):
                nonlocal replaced
                resolved = original_resolve(
                    path, allow_command_symlink=allow_command_symlink
                )
                if resolved == executable_path.resolve() and not replaced:
                    executable_path.write_bytes(
                        b"#!/usr/bin/env node\nprocess.exit(0);\n"
                    )
                    executable_path.chmod(0o755)
                    replaced = True
                return resolved

            with patch.object(
                adapter,
                "_resolved_native_source",
                side_effect=replace_after_resolution,
            ):
                result = adapter.plan_request(
                    request(),
                    command=str(executable_path),
                    runner=probe_runner(calls),
                )

            self.assertTrue(replaced)
            self.assertEqual(result.get("outcome"), "backend_not_ready")
            self.assertEqual(calls, [])

    def test_native_probe_runs_only_the_private_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            seen = []

            result = adapter.probe(
                command=str(executable), runner=probe_runner(seen)
            )

            self.assertTrue(result["dispatch_ready"])
            self.assertEqual(len(seen), 5)
            self.assertTrue(
                all(Path(call["argv"][0]) != executable for call in seen)
            )
            self.assertEqual(
                {Path(call["argv"][0]).name for call in seen}, {"wigolo-native"}
            )

    def test_extensionless_node_shebang_is_not_treated_as_standalone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "wigolo"
            raw = b"#!/usr/bin/env node\nprocess.exit(0);\n"
            executable.write_bytes(raw)
            executable.chmod(0o755)

            with self.subTest(stage="plan"):
                result = adapter.plan_request(
                    request(), command=str(executable), runner=probe_runner()
                )
                self.assertEqual(result.get("outcome"), "backend_not_ready")

            with self.subTest(stage="snapshot"):
                binding = {
                    "path": str(executable),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
                with self.assertRaisesRegex(adapter.ContractError, "native"):
                    adapter._snapshot_bound_executable(binding, directory)

    def test_child_environment_is_allowlisted_and_uses_isolated_home_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            calls = []

            def runner(argv, **kwargs):
                calls.append((list(argv), kwargs))
                return completed(discovery_output())

            result = adapter.execute_plan(
                plan,
                runner=runner,
                environ={
                    "PATH": "/usr/bin",
                    "LANG": "C",
                    "SECRET_TOKEN": "never-pass",
                    "HOME": "/sensitive/home",
                    "USER_AGENT": "OAI-SearchBot",
                },
            )
            self.assertEqual(result["outcome"], "success")
            env = calls[0][1]["env"]
            self.assertNotIn("SECRET_TOKEN", env)
            self.assertNotEqual(env["HOME"], "/sensitive/home")
            self.assertEqual(env["HOME"], env["WIGOLO_DATA_DIR"])
            self.assertTrue(Path(env["HOME"]).name.startswith("top50-wigolo-run-"))
            self.assertEqual(env["WIGOLO_STEALTH"], "off")
            self.assertEqual(env["RESPECT_ROBOTS_TXT"], "true")
            self.assertEqual(
                env["USER_AGENT"],
                "TopFiftyWigoloAdapter/2.1 (+https://github.com/siuserxiaowei/skills)",
            )
            self.assertNotIn("OAI-SearchBot", env.values())

    def test_plan_tamper_fails_and_execute_does_not_reprobe(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            tampered = copy.deepcopy(plan)
            tampered["argv"].append("--stealth")
            calls = []
            result = adapter.execute_plan(
                tampered, runner=lambda *a, **k: calls.append((a, k))
            )
            self.assertEqual(result["outcome"], "invalid_plan")
            self.assertEqual(calls, [])

            execute_calls = []
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kw: (
                    execute_calls.append(list(argv)) or completed(discovery_output())
                ),
            )
            self.assertEqual(result["outcome"], "success")
            self.assertEqual(len(execute_calls), 1)
            self.assertNotEqual(execute_calls[0][0], plan["argv"][0])
            self.assertEqual(execute_calls[0][1:], plan["argv"][1:])

    def test_discovery_plan_uses_only_the_fixed_read_only_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {
                "query": "agent research",
                "max_results": 17,
                "from_date": "2026-07-01",
                "to_date": "2026-07-31",
                "include_domains": ["example.com", "example.org"],
                "exclude_domains": ["spam.example.net"],
            }
            plan = signed_plan(Path(directory), "discovery", payload)
            self.assertEqual(
                plan["argv"],
                [
                    plan["executable"]["path"],
                    "search",
                    "agent research",
                    "--max-results=17",
                    "--from-date=2026-07-01",
                    "--to-date=2026-07-31",
                    "--include-domains=example.com,example.org",
                    "--exclude-domains=spam.example.net",
                    "--no-content",
                    "--no-cache",
                    "--json",
                ],
            )

    def test_fetch_plan_forces_direct_non_js_refresh_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = {
                "url": "https://example.com/article",
                "max_chars": 12345,
                "section": "results",
            }
            plan = signed_plan(Path(directory), "fetch", payload)
            self.assertEqual(
                plan["argv"],
                [
                    plan["executable"]["path"],
                    "fetch",
                    "https://example.com/article",
                    "--render-js=never",
                    "--force-refresh",
                    "--max-chars=12345",
                    "--section=results",
                    "--json",
                ],
            )

    def test_watch_is_list_only_and_mutations_are_rejected_before_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            plan = signed_plan(root, "watch", {"action": "list"})
            self.assertEqual(
                plan["argv"],
                [plan["executable"]["path"], "watch", "list", "--json"],
            )

            for action in ("create", "delete", "pause", "resume"):
                with self.subTest(action=action):
                    calls = []
                    result = adapter.plan_request(
                        request("watch", {"action": action}),
                        command=str(executable),
                        runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                    )
                    self.assertEqual(result["outcome"], "policy_rejected")
                    self.assertEqual(
                        [row["code"] for row in result["diagnostics"]],
                        ["watch_read_only"],
                    )
                    self.assertEqual(calls, [])

    def test_discovery_output_is_strictly_downgraded_to_unreviewed_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            result = adapter.execute_plan(
                plan, runner=lambda argv, **kw: completed(discovery_output())
            )
            self.assertEqual(result["outcome"], "success")
            data = result["data"]
            self.assertEqual(data["evidence_authority"], "none")
            self.assertEqual(data["curator_authority"], "none")
            self.assertEqual(data["query"], "agent research")
            self.assertEqual(len(data["candidates"]), 1)
            candidate = data["candidates"][0]
            self.assertEqual(candidate["source_rank"], 1)
            self.assertEqual(candidate["evidence_status"], "discovery_only")
            self.assertIs(candidate["curator_accepted"], False)
            self.assertRegex(candidate["candidate_id"], r"^wigolo-[0-9a-f]{24}$")

    def test_discovery_backend_authority_claims_are_not_propagated(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            output = discovery_output(
                evidence_authority="strong",
                curator_authority="accepted",
                reviewer_status="accepted",
                evidence_grade="strong",
            )
            output["results"][0].update(
                reviewer_status="accepted",
                evidence_grade="strong",
                curator_accepted=True,
                evidence_status="accepted",
            )
            result = adapter.execute_plan(
                plan, runner=lambda argv, **kw: completed(output)
            )
            self.assertEqual(result["outcome"], "success")
            data = result["data"]
            self.assertEqual(
                set(data),
                {
                    "evidence_authority",
                    "curator_authority",
                    "query",
                    "engines_used",
                    "total_time_ms",
                    "candidates",
                },
            )
            candidate = data["candidates"][0]
            self.assertNotIn("reviewer_status", candidate)
            self.assertNotIn("evidence_grade", candidate)
            self.assertEqual(candidate["evidence_status"], "discovery_only")
            self.assertIs(candidate["curator_accepted"], False)

    def test_fetch_output_is_direct_http_discovery_only_without_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory), "fetch")
            result = adapter.execute_plan(
                plan, runner=lambda argv, **kw: completed(fetch_output())
            )
            self.assertEqual(result["outcome"], "success")
            data = result["data"]
            self.assertEqual(data["evidence_authority"], "none")
            self.assertEqual(data["curator_authority"], "none")
            self.assertEqual(data["evidence_status"], "discovery_only")
            self.assertEqual(data["requested_url"], "https://example.com/article")
            self.assertEqual(
                data["acquisition"],
                {
                    "method": "direct_http",
                    "backend_id": "wigolo",
                    "render_js": "never",
                },
            )
            self.assertIs(data["cached"], False)
            self.assertEqual(data["links"], ["https://example.com/reference"])
            self.assertEqual(data["images"], ["https://example.com/image.png"])

    def test_malformed_or_non_object_backend_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            bad_outputs = [
                subprocess.CompletedProcess([], 0, "{", ""),
                completed([]),
                completed({}),
            ]
            for output in bad_outputs:
                with self.subTest(stdout=output.stdout):
                    result = adapter.execute_plan(
                        plan, runner=lambda argv, output=output, **kw: output
                    )
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["outcome"], "invalid_backend_output")

    def test_empty_discovery_results_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kw: completed(discovery_output(results=[])),
            )
            self.assertEqual(result["outcome"], "invalid_backend_output")
            self.assertIsNone(result["data"])

    def test_duplicate_discovery_urls_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            first = discovery_output()["results"][0]
            second = dict(first, title="Duplicate result")
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kw: completed(
                    discovery_output(results=[first, second])
                ),
            )
            self.assertEqual(result["outcome"], "invalid_backend_output")

    def test_discovery_query_must_match_the_signed_request(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kw: completed(
                    discovery_output(query="different query")
                ),
            )
            self.assertEqual(result["outcome"], "invalid_backend_output")

    def test_cache_stats_and_search_remain_read_only_discovery_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stats_plan = signed_plan(root, "cache", {"action": "stats"})
            stats_result = adapter.execute_plan(
                stats_plan,
                runner=lambda argv, **kw: completed(
                    {
                        "stats": {
                            "total_urls": 3,
                            "total_size_mb": 1.25,
                            "oldest": "2026-07-01T00:00:00Z",
                            "newest": "2026-07-31T00:00:00Z",
                        }
                    }
                ),
            )
            self.assertEqual(stats_result["outcome"], "success")
            self.assertEqual(stats_result["data"]["evidence_authority"], "none")
            self.assertEqual(stats_result["data"]["curator_authority"], "none")
            self.assertEqual(stats_result["data"]["action"], "stats")
            self.assertEqual(stats_result["data"]["stats"]["total_urls"], 3)

            search_payload = {
                "action": "search",
                "query": "agent research",
                "url_pattern": "example.com",
                "since": "2026-07-01",
                "limit": 4,
                "max_tokens_out": 8000,
            }
            search_plan = signed_plan(root, "cache", search_payload)
            self.assertEqual(
                search_plan["argv"][1:],
                [
                    "cache",
                    "search",
                    "agent research",
                    "--mode=fts",
                    "--url-pattern=example.com",
                    "--since=2026-07-01",
                    "--limit=4",
                    "--max-tokens-out=8000",
                    "--json",
                ],
            )
            search_result = adapter.execute_plan(
                search_plan,
                runner=lambda argv, **kw: completed(
                    {
                        "results": [
                            {
                                "url": "https://example.com/article",
                                "title": "Cached article",
                                "markdown": "Cached public content.",
                                "fetched_at": "2026-07-30T10:00:00Z",
                                "reviewer_status": "accepted",
                            }
                        ]
                    }
                ),
            )
            self.assertEqual(search_result["outcome"], "success")
            row = search_result["data"]["results"][0]
            self.assertEqual(row["evidence_status"], "discovery_only")
            self.assertNotIn("reviewer_status", row)

    def test_fetch_challenge_solver_escalation_or_non_http_method_is_policy_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory), "fetch")
            banned = (
                {"challenge_class": "cloudflare"},
                {"solve_method": "ai"},
                {"escalated": True},
                {"fetch_method": "browser"},
            )
            for mutation in banned:
                with self.subTest(mutation=mutation):
                    result = adapter.execute_plan(
                        plan,
                        runner=lambda argv, mutation=mutation, **kw: completed(
                            fetch_output(**mutation)
                        ),
                    )
                    self.assertEqual(result["outcome"], "policy_rejected")
                    self.assertEqual(
                        [row["code"] for row in result["diagnostics"]],
                        ["banned_backend_feature_observed"],
                    )
                    self.assertIsNone(result["data"])

    def test_nested_forbidden_fetch_capabilities_are_policy_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory), "fetch")
            nested = (
                {"metadata": {"solve_method": "ai"}},
                {"metadata": {"fetch_method": "browser"}},
                {"metadata": {"security": {"escalated": True}}},
                {"metadata": {"user_agent": "OAI-SearchBot"}},
                {"metadata": {"challenge": {"solved": True}}},
                {"metadata": {"solveMethod": "ai"}},
                {"metadata": {"tls_tier": "chrome"}},
                {"metadata": {"render_js": "playwright"}},
                {"metadata": {"user-agent": "OAI-SearchBot"}},
            )
            for mutation in nested:
                with self.subTest(mutation=mutation):
                    result = adapter.execute_plan(
                        plan,
                        runner=lambda argv, mutation=mutation, **kwargs: completed(
                            fetch_output(**mutation)
                        ),
                    )
                    self.assertEqual(result["outcome"], "policy_rejected")
                    self.assertIsNone(result["data"])

    def test_fetch_rejects_cached_or_empty_content(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory), "fetch")
            for mutation in ({"cached": True}, {"markdown": ""}):
                with self.subTest(mutation=mutation):
                    result = adapter.execute_plan(
                        plan,
                        runner=lambda argv, mutation=mutation, **kw: completed(
                            fetch_output(**mutation)
                        ),
                    )
                    self.assertEqual(result["outcome"], "invalid_backend_output")
                    self.assertIsNone(result["data"])

    def test_validate_result_rejects_digest_and_authority_escalation(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = signed_plan(Path(directory))
            valid = adapter.execute_plan(
                plan, runner=lambda argv, **kw: completed(discovery_output())
            )

            bad_digest = copy.deepcopy(valid)
            bad_digest["duration_ms"] += 1
            with self.assertRaisesRegex(adapter.ContractError, "digest"):
                adapter.validate_result(bad_digest)

            elevated_authority = copy.deepcopy(valid)
            elevated_authority["data"]["evidence_authority"] = "strong"
            reseal_result(elevated_authority)
            with self.assertRaisesRegex(adapter.ContractError, "authority"):
                adapter.validate_result(elevated_authority)

            accepted_candidate = copy.deepcopy(valid)
            accepted_candidate["data"]["candidates"][0]["curator_accepted"] = True
            reseal_result(accepted_candidate)
            with self.assertRaisesRegex(adapter.ContractError, "accepted evidence"):
                adapter.validate_result(accepted_candidate)

    def test_cli_execute_consumes_a_signed_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            stdout = io.StringIO()
            with patch.object(
                adapter,
                "_RUNNER",
                lambda argv, **kw: completed(discovery_output()),
            ), patch("sys.stdout", stdout):
                exit_code = adapter.main(
                    [
                        "execute", "--plan", str(plan_path),
                        "--auth-key-file", str(key_file),
                    ]
                )
            self.assertEqual(exit_code, 0)
            emitted = json.loads(stdout.getvalue())
            self.assertEqual(emitted["outcome"], "success")
            self.assertEqual(emitted["plan_digest_sha256"], plan["plan_digest_sha256"])

    def test_cli_execute_json_read_failure_is_an_authenticated_v3_result(self):
        schema = json.loads(
            (SCHEMAS / "wigolo-result.schema.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key_file = make_auth_key(root)
            malformed_plan = root / "malformed-plan.json"
            malformed_plan.write_text("{not-json", encoding="utf-8")

            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                exit_code = adapter.main(
                    [
                        "execute",
                        "--plan",
                        str(malformed_plan),
                        "--auth-key-file",
                        str(key_file),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stderr.getvalue(), "")
            emitted = json.loads(stdout.getvalue())
            self.assertEqual(emitted["contract_version"], adapter.RESULT_CONTRACT)
            self.assertEqual(emitted["outcome"], "invalid_plan")
            self.assertIn("auth_key_id", emitted)
            self.assertIn("result_hmac_sha256", emitted)
            adapter.validate_result(emitted, auth_key_file=str(key_file))
            jsonschema.Draft202012Validator(schema).validate(emitted)

    def test_cli_keyed_commands_without_auth_key_use_stderr_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload_path = root / "payload.json"
            payload_path.write_text(
                json.dumps({"run_id": "run-no-key", "operation": "discovery"}),
                encoding="utf-8",
            )
            cases = (
                ["execute", "--plan", str(payload_path)],
                ["plan", "--input", str(payload_path)],
            )
            for argv in cases:
                with self.subTest(argv=argv):
                    stdout = io.StringIO()
                    stderr = io.StringIO()
                    with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                        exit_code = adapter.main(argv)

                    self.assertEqual(exit_code, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn("--auth-key-file", stderr.getvalue())
                    self.assertNotIn(adapter.RESULT_CONTRACT, stderr.getvalue())

    def test_cli_unusable_auth_key_never_produces_an_unsigned_v3_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed_plan = root / "malformed-plan.json"
            malformed_plan.write_text("{not-json", encoding="utf-8")
            key_file = make_auth_key(root)
            key_file.chmod(0o644)
            stdout = io.StringIO()
            stderr = io.StringIO()

            with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
                exit_code = adapter.main(
                    [
                        "execute",
                        "--plan",
                        str(malformed_plan),
                        "--auth-key-file",
                        str(key_file),
                    ]
                )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("auth key", stderr.getvalue().lower())
            self.assertNotIn(adapter.RESULT_CONTRACT, stderr.getvalue())

    def test_cli_execute_rejects_raw_request_command_override_or_missing_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps(request()), encoding="utf-8")
            rejected_argv = (
                ["execute", "--input", str(request_path)],
                ["execute", "--command", "wigolo", "--plan", str(request_path)],
                ["execute"],
            )
            for argv in rejected_argv:
                with self.subTest(argv=argv), patch("sys.stderr", io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        adapter.main(argv)
                    self.assertNotEqual(raised.exception.code, 0)

    def test_plan_hmac_rejects_an_attacker_who_recomputes_plain_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            tampered = copy.deepcopy(plan)
            tampered["normalized_request"]["payload"]["query"] = "attacker query"
            tampered["argv"][2] = "attacker query"
            tampered["request_digest_sha256"] = adapter._digest(
                tampered["normalized_request"]
            )
            tampered["plan_digest_sha256"] = adapter._digest(
                {
                    key: value
                    for key, value in tampered.items()
                    if key not in {"plan_digest_sha256", "plan_hmac_sha256"}
                }
            )
            calls = []
            result = adapter.execute_plan(
                tampered,
                runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                auth_key_file=str(key_file),
            )
            self.assertEqual(result["outcome"], "invalid_plan")
            self.assertEqual(calls, [])

    def test_wrong_or_overexposed_auth_key_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            wrong_key = make_auth_key(root, "wrong.key")
            wrong_key.write_bytes(b"different-test-only-key-material-at-least-32")
            calls = []
            result = adapter.execute_plan(
                plan,
                runner=lambda *args, **kwargs: calls.append((args, kwargs)),
                auth_key_file=str(wrong_key),
            )
            self.assertEqual(result["outcome"], "invalid_plan")
            self.assertEqual(calls, [])

            key_file.chmod(0o644)
            with self.assertRaisesRegex(adapter.ContractError, "permissions"):
                adapter.execute_plan(plan, auth_key_file=str(key_file))

    def test_auth_key_never_reaches_plan_argv_result_or_child_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            secret = key_file.read_bytes()
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            calls = []
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kwargs: (
                    calls.append((list(argv), kwargs))
                    or completed(discovery_output())
                ),
                auth_key_file=str(key_file),
            )
            serialized = json.dumps(
                {"plan": plan, "result": result}, ensure_ascii=False
            ).encode("utf-8")
            self.assertNotIn(secret, serialized)
            self.assertNotIn(str(key_file), serialized.decode("utf-8"))
            child_argv, child_kwargs = calls[0]
            self.assertNotIn(str(key_file), child_argv)
            self.assertNotIn(str(key_file), child_kwargs["env"].values())
            self.assertNotIn(secret.decode("utf-8"), child_kwargs["env"].values())

    def test_authenticated_result_rejects_unknown_nested_authority_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kwargs: completed(discovery_output()),
                auth_key_file=str(key_file),
            )
            injected = copy.deepcopy(result)
            injected["data"]["candidates"][0]["reviewer_status"] = "accepted"
            injected["result_digest_sha256"] = adapter._digest(
                {
                    key: value
                    for key, value in injected.items()
                    if key not in {"result_digest_sha256", "result_hmac_sha256"}
                }
            )
            injected["result_hmac_sha256"] = adapter._hmac_digest(
                adapter._read_auth_key_file(str(key_file)),
                adapter.RESULT_HMAC_CONTEXT,
                {
                    key: value
                    for key, value in injected.items()
                    if key != "result_hmac_sha256"
                },
            )
            with self.assertRaisesRegex(adapter.ContractError, "fields"):
                adapter.validate_result(injected, auth_key_file=str(key_file))

    def test_result_hmac_cannot_be_stripped_and_replaced_by_a_plain_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kwargs: completed(discovery_output()),
                auth_key_file=str(key_file),
            )
            stripped = copy.deepcopy(result)
            stripped.pop("auth_key_id")
            stripped.pop("result_hmac_sha256")
            stripped["data"]["candidates"][0]["title"] = "attacker title"
            stripped["result_digest_sha256"] = adapter._digest(
                {
                    key: value
                    for key, value in stripped.items()
                    if key != "result_digest_sha256"
                }
            )
            with self.assertRaisesRegex(adapter.ContractError, "fields|HMAC"):
                adapter.validate_result(stripped, auth_key_file=str(key_file))

            schema = json.loads(
                (SCHEMAS / "wigolo-result.schema.json").read_text(encoding="utf-8")
            )
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.Draft202012Validator(schema).validate(stripped)

    def test_discovery_cannot_return_more_than_the_signed_maximum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = make_executable(root)
            key_file = make_auth_key(root)
            plan = adapter.plan_request(
                request(payload={"query": "agent research", "max_results": 1}),
                command=str(executable),
                runner=probe_runner(),
                auth_key_file=str(key_file),
            )
            first = discovery_output()["results"][0]
            second = dict(
                first,
                title="Second result",
                url="https://example.org/second",
            )
            result = adapter.execute_plan(
                plan,
                runner=lambda argv, **kwargs: completed(
                    discovery_output(results=[first, second])
                ),
                auth_key_file=str(key_file),
            )
            self.assertEqual(result["outcome"], "invalid_backend_output")
            self.assertIsNone(result["data"])


if __name__ == "__main__":
    unittest.main()

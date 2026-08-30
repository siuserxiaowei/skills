#!/usr/bin/env python3
"""Build the isolated web/ecosystem discovery shard from curator-read public pages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "research/run-pi-platform10-20260826/workers/web-ecosystem-candidates.jsonl"
ACCESSED_AT = "2026-08-26"


def row(
    candidate_id: str,
    platform_id: str,
    title: str,
    canonical_url: str,
    creator_name: str,
    published_at: str,
    date_basis: str,
    content_type: str,
    content_track: str,
    summary: str,
    why_useful: str,
    query_id: str,
    readback_evidence: str,
    *,
    language: str = "en",
    evidence_status: str = "curator_review_ready",
    discovery_backend: str = "external_exact_alias_discovery",
    readback_backend: str = "public_canonical_page_readback",
    limitations: str = "Worker-level original-page readback only; the primary curator must independently verify relevance, version drift, and near duplicates before acceptance.",
) -> dict:
    return {
        "candidate_id": candidate_id,
        "platform_id": platform_id,
        "title": title,
        "canonical_url": canonical_url,
        "creator_name": creator_name,
        "published_at": published_at,
        "date_basis": date_basis,
        "accessed_at": ACCESSED_AT,
        "language": language,
        "content_type": content_type,
        "content_track": content_track,
        "summary": summary,
        "why_useful": why_useful,
        "discovery_backend": discovery_backend,
        "readback_backend": readback_backend,
        "evidence_status": evidence_status,
        "limitations": limitations,
        "query_id": query_id,
        "readback_evidence": readback_evidence,
    }


def official_rows() -> list[dict]:
    releases = [
        ("0.84.3", "2026-08-24", "PowerShell tool, atomic managed updates, and session-scoped model/thinking controls", "official-release-features"),
        ("0.84.2", "2026-08-14", "fullscreen transcript search, configurable default tools, and configurable fullscreen exit output", "official-release-features"),
        ("0.84.1", "2026-08-07", "Qwen Token Plan Individual, authentication readiness checks, and improved fullscreen interaction", "official-release-features"),
        ("0.84.0", "2026-08-06", "fullscreen TUI, Mermaid/LaTeX rendering, and per-directory AGENTS.override.md context", "official-release-features"),
        ("0.83.0", "2026-07-29", "credential export, headless OpenRouter sign-in, and Claude Opus 5 through GitHub Copilot", "official-release-features"),
        ("0.82.1", "2026-07-25", "Claude Opus 5 support, Anthropic gateway bearer authentication, and resilient model catalogs", "official-release-features"),
        ("0.82.0", "2026-07-24", "constrained tool sampling, OpenRouter/Kimi sign-in, and session-aware streaming bash integrations", "official-release-features"),
        ("0.81.1", "2026-07-21", "deterministic source archives and retryable compaction/branch summaries", "official-runtime-safety"),
        ("0.81.0", "2026-07-21", "local llama.cpp management, full provider extensions, and Qwen Token Plan providers", "official-release-features"),
        ("0.80.10", "2026-07-16", "Kimi Coding adaptive-thinking compatibility and corrected Kimi K3 metadata", "official-runtime-safety"),
        ("0.80.9", "2026-07-16", "Kimi K3 support and deferred extension-tool loading", "official-release-features"),
        ("0.80.8", "2026-07-16", "unified ModelRuntime, provider-owned login, live catalogs, and xAI device-code OAuth", "official-release-features"),
        ("0.80.7", "2026-07-14", "session-affinity migration, cache-friendly dynamic tools, and transcript message copy", "official-runtime-safety"),
        ("0.80.6", "2026-07-09", "max thinking level and input-based long-context pricing tiers", "official-release-features"),
        ("0.80.4", "2026-07-09", "prompt-cache miss visibility, project-local resources, and extension lifecycle/provider hooks", "official-runtime-safety"),
    ]
    return [
        row(
            f"web-official-release-{version.replace('.', '-')}",
            "official_web",
            f"Pi {version}",
            f"https://pi.dev/news/releases/{version}",
            "Pi / Earendil Works",
            date,
            "pi.dev news RSS pubDate and canonical release page",
            "official release notes",
            "进阶" if intent == "official-release-features" else "批评与风险",
            f"Pi 官方发布说明列出 {features}。",
            "提供固定版本的一手变更记录，可用于核对教程、扩展和部署建议的适用版本。",
            intent,
            f"pi.dev/news.xml item and canonical page were read; title=Pi {version}; pubDate={date}; first change groups={features}",
            discovery_backend="pi.dev_public_news_rss",
            readback_backend="pi.dev_public_rss_and_canonical_release_page",
            limitations="Release notes are first-party change records, not independent performance or security validation; sibling versions remain separate versioned content objects.",
        )
        for version, date, features, intent in releases
    ]


def composio_rows() -> list[dict]:
    content = [
        ("pi-vs-opencode", "Pi vs OpenCode: After 100 Hours, Which Open-Source Coding Agent Should You Use?", "2026-08-21", "对照 Pi 与 OpenCode 的成本、速度、token 开销、安全与扩展性。", "composio-pi-comparisons"),
        ("top-pi-agent-skills", "Top 11 Pi Agent Skills Every Developer Must Use", "2026-08-19", "按开发、测试、安全、调试与代码审查整理 Pi skills。", "composio-pi-extensions"),
        ("top-pi-extensions", "Top 10 Pi Agent Extensions Every Developers Must Install", "2026-08-17", "整理 MCP、sub-agent、网页、安全和规划类 Pi extensions。", "composio-pi-extensions"),
        ("pi-agent-vs-claude-code", "Pi Agent vs Claude Code in 2026", "2026-08-10", "基于作者声称的 100 小时使用比较成本、工作流、能力和安全。", "composio-pi-comparisons"),
        ("best-agent-harness-deepseek-v4-flash", "Finding the Best Harness for DeepSeek V4 Flash", "2026-08-11", "Composio Golden Eval 比较八个 harness，报告 Pi 完成 30 项中的 20 项。", "composio-harness-benchmarks"),
        ("best-ai-agent-harnesses", "8 Best AI Agent Harnesses in 2026", "2026-08-04", "以 25 个 Kimi K3 任务比较包括 Pi 在内的八个 harness。", "composio-harness-benchmarks"),
    ]
    rows = [
        row(
            f"web-composio-content-{slug}", "composio", title,
            f"https://composio.dev/content/{slug}", "Composio", date,
            "canonical page datePublished JSON-LD", "first-party article", "生态与案例",
            summary, "提供 Composio 对 Pi 的一手集成经验或自有基准结果，适合与代码和独立测试交叉核对。",
            intent,
            f"canonical page HTML read; title={title}; datePublished={date}; body and section headings explicitly discuss Pi",
            limitations="First-party vendor-authored comparison; benchmark and usage claims require independent reproduction and should not be treated as neutral rankings.",
        ) for slug, title, date, summary, intent in content
    ]
    docs = [
        ("docs-provider-pi", "Pi | Composio", "https://docs.composio.dev/docs/providers/pi", "说明如何在 Pi session 中使用 Composio tools。"),
        ("docs-example-general-agent", "Build a Slack bot that can do work with you and your team", "https://docs.composio.dev/examples/general-agent-with-pi", "用 Pi 与 Composio 构建 Slack agent，覆盖触发器、用户会话、共享连接和重定向授权。"),
    ]
    rows += [
        row(cid, "composio", title, url, "Composio", "unknown", "publication date not exposed on canonical docs page", "official documentation", "技巧", summary,
            "直接展示 Pi 与授权工具平台的集成边界和代码结构。", "composio-pi-docs",
            f"canonical public documentation body read; title={title}; Pi-specific code/integration narrative present",
            discovery_backend="composio_public_llms_txt_and_sitemap", readback_backend="composio_public_docs_page",
            limitations="Documentation asks for API credentials/OAuth; no account was connected and no tool or downstream action was executed.")
        for cid, title, url, summary in docs
    ]
    toolkits = [
        ("github", "GitHub", "labels, collaborators and repository actions"),
        ("slack", "Slack", "reminders, reactions and team messages"),
        ("virustotal", "Virustotal", "file-hash and suspicious-URL analysis"),
        ("linkup", "Linkup", "web research and news retrieval"),
        ("digital_ocean", "Digital ocean", "droplets and managed database operations"),
        ("cloudflare", "Cloudflare", "DNS and firewall operations"),
        ("pagerduty", "Pagerduty", "audit history and incident reporting"),
    ]
    rows += [
        row(
            f"web-composio-toolkit-{toolkit}", "composio", f"How to integrate {label} with Pi",
            f"https://composio.dev/toolkits/{toolkit}/framework/pi-agent", "Composio", "2026-08-26",
            "canonical page datePublished JSON-LD observed at access time", "integration guide", "生态与案例",
            f"Composio 的 Pi 专属页面说明通过 MCP 将 {label} 接入 Pi，并示例 {actions}。",
            "展示同一 Pi harness 在不同外部系统上的权限与工具表面；适合审查最小权限和连接隔离。",
            "composio-pi-toolkit-integrations",
            f"canonical page HTML read; title=How to integrate {label} with Pi; Pi-specific MCP setup and example actions visible",
            limitations="The page describes potentially mutating actions, but research was read-only: no login, OAuth grant, credential entry, or tool execution occurred.",
        ) for toolkit, label, actions in toolkits
    ]
    return rows


def zenn_rows() -> list[dict]:
    specs = [
        ("kimuson-opencode", "OpenCode Go + pi-coding-agent のすゝめ", "https://zenn.dev/kimuson/articles/pi-coding-agent-with-opencode-go", "きむそん", "2026-05-06", "模型/订阅选择与 provider 独立性，并明确 Pi 无内置审批、sandbox 需自行配置。", "zenn-pi-provider-practice"),
        ("53able-runtime", "pi-monoは完成品のAIコーディングツールというより、自作エージェント基盤として見ると強い。", "https://zenn.dev/53able/articles/c619b3f3cabf4e", "53able", "2026-04-27", "实际 build、test 和最小 extension 实验后评估包结构与可扩展运行时。", "zenn-pi-architecture"),
        ("okuoku-tools", "nag：各種コーディングエージェントのtoolを見てみる会", "https://zenn.dev/okuoku/scraps/2913c3752e1bf0", "okuoku", "2026-04-23", "逐项比较多种 coding agent 工具表面，其中单独记录 Pi 的默认工具和扩展入口。", "zenn-pi-architecture"),
        ("53able-capability", "AI-nativeなWebアプリは route ではなく capability から設計したほうがいい", "https://zenn.dev/53able/articles/5e32c6e5a4b511", "53able", "2026-05-16", "把 Pi 的四种模式和分层包结构迁移为 capability-first Web 应用层设计。", "zenn-pi-design-transfer"),
        ("omniwired-toolkit", "pi-mono：ハッカーのための最強AIコーディングエージェントツールキット", "https://zenn.dev/omniwired/articles/2640a8301dd9c4", "omniwired", "2026-03-06", "介绍 Pi monorepo 的 API、runtime、CLI、TUI 与 Web UI 分层。", "zenn-pi-architecture"),
        ("masahide-openclaw", "OpenClawを支えるAIエージェント pi-coding-agent について", "https://zenn.dev/masahide/articles/ab93620ca9353e", "masahide", "2026-02-14", "从 OpenClaw 底层 harness 视角解释 Pi 的极简 prompt、四工具、上下文交接与扩展。", "zenn-pi-architecture"),
        ("tanadeyu-memory", "pi-coding-agent用拡張記憶pi-gl-mem を作ってみました", "https://zenn.dev/tanadeyu/articles/7d39bad0afffb5", "tanadeyu", "2026-06-22", "给 Pi 增加全局/项目记忆，并讨论零依赖、目录隔离和多进程风险。", "zenn-pi-extension-practice"),
        ("tanadeyu-linux", "pi-coding-agentをLinux 側で構築するメモ", "https://zenn.dev/tanadeyu/articles/f68dbb546eab58", "tanadeyu", "2026-06-17", "在 WSL2 Ubuntu 中用 nvm/Node 安装 Pi，并记录环境验证和卸载注意。", "zenn-pi-provider-practice"),
        ("knaka-install", "pi-coding-agent インストール Skillsメモ", "https://zenn.dev/knaka0209/scraps/c3404402ce39a9", "knaka Tech-Blog", "2026-07-02", "记录安装、OpenRouter 登录、模型选择与 skills 测试。", "zenn-pi-provider-practice"),
        ("kun432-quickstart", "Pi Agentを試す ①Quickstart", "https://zenn.dev/kun432/scraps/408aa9657ca24e", "kun432", "2026-05-11", "按官方站梳理 extensions、skills、templates、themes、packages 和多模型入口。", "zenn-pi-provider-practice"),
    ]
    return [
        row(f"web-zenn-{cid}", "zenn", title, url, author, date, "visible Zenn article/scrap timestamp", "article" if "/articles/" in url else "scrap", "技巧", summary,
            "提供日语社区的实操、源码阅读或设计迁移视角。", intent,
            f"ordinary public Zenn page read; visible title={title}; author={author}; date={date}; Pi-specific body sections observed",
            language="ja", discovery_backend="external_search_exact_alias_then_direct_url", readback_backend="ordinary_public_zenn_page",
            limitations="Some pages reference the former badlogic/pi-mono name or an older Pi version; commands and package names must be mapped to current pi.dev documentation.")
        for cid, title, url, author, date, summary, intent in specs
    ]


def note_rows() -> list[dict]:
    specs = [
        ("imds-low-cost", "Maxプランのトークン使い切ったので5ドルでPi Coding Agentはじめる", "https://note.com/immmmmmmu/n/nac57bcd1a239", "imds", "2026-08-19", "从低成本模型选择、配置和 OpenCode Go 切入 Pi 实践。", "note-pi-setup"),
        ("keity-textbook", "AIエージェントの設計を1から学べる Pi Agent 教科書", "https://note.com/keity717/n/n4a42309e93d0", "KeiTy", "2026-08-10", "面向初学者解释 Pi 的减法设计与按需扩展。", "note-pi-design"),
        ("keity-extensions", "Pi Agentの35個の拡張を全解説", "https://note.com/keity717/n/ndd6623e4ff5f", "KeiTy", "2026-08-10", "逐项整理官方示例中的生命周期、安全、上下文和 UI 扩展。", "note-pi-extensions"),
        ("yuimaru-ohmypi", "pi と Rust 製 oh-my-pi がもたらす開発革命", "https://note.com/humble_bobcat51/n/n02a214f85d8c", "ゆいまる", "2026-05-21", "比较 Pi 与 oh-my-pi 的扩展结构、Hashline 编辑和作者声称的 benchmark。", "note-pi-design"),
        ("yui-session", "Pi Coding Agentのセッション操作＆コンテキスト強制コンパクト拡張", "https://note.com/deft_gecko6923/n/n795a6edc6e7c", "YUI", "2026-06-22", "提供 session-export 与 force-compact 扩展，并补足跨平台 Node.js 处理。", "note-pi-extensions"),
        ("kiki-subtraction", "pi — 引き算で設計されたコーディングエージェント", "https://note.com/_kihonushi/n/n4e4bd035c453", "KiKi@AIx個人開発", "2026-03-10", "解释 pi-ai、agent-core、coding-agent 与树状会话的减法设计。", "note-pi-design"),
        ("yui-provider", "Pi Coding Agentのカスタムプロバイダー拡張スクリプト", "https://note.com/deft_gecko6923/n/nbf91fe098cf9", "YUI", "2026-06-21", "为 Ollama 等本地模型与自定义代理提供 provider extension，并说明修复点。", "note-pi-extensions"),
        ("eiji-private", "次世代の主権型AI Pi Agent 究極のプライベート・インテリジェンス構築", "https://note.com/eiji71/n/n5d2925a554b9", "エイじー", "2026-05-30", "以官方 Earendil 仓库为起点讨论私有部署、模型和数据控制。", "note-pi-setup"),
        ("shali-context", "AIコーディングエージェントは足すから削るへ", "https://note.com/shali_note/n/n552f152a14cb", "しゃり", "2026-08-07", "讨论 Pi 的最小工具集、上下文管理和可扩展性。", "note-pi-design"),
        ("lazy-radar", "今日のAI注目リポジトリ TOP3", "https://note.com/lazy_engineer/n/n843134c41ee6", "楽したいAI自動化エンジニア", "2026-08-11", "聚合页把 pi-book 列为首项，并以源码分析资料解释 Pi Agent 设计。", "note-pi-ecosystem"),
    ]
    rows = []
    for cid, title, url, author, date, summary, intent in specs:
        ready = cid != "lazy-radar"
        rows.append(row(
            f"web-note-{cid}", "note", title, url, author, date, "visible note publication timestamp", "public note", "技巧", summary,
            "提供日语长文中的 Pi 入门、扩展与设计观点。", intent,
            f"ordinary public note page read; visible title={title}; creator={author}; date={date}; {'Pi-primary body' if ready else 'Pi appears as one section of a three-repository roundup'}",
            language="ja", evidence_status="curator_review_ready" if ready else "not_ready",
            discovery_backend="external_search_exact_alias_then_direct_url", readback_backend="ordinary_public_free_note_page",
            limitations="Public free body was read without login; claims, generated code, versions, and benchmark numbers require independent verification." if ready else "Original page was read, but Pi is only one item in a broader repository roundup; retain as a rejected discovery outcome unless the curator finds enough Pi-primary depth.",
        ))
    return rows


def restricted_platform_rows() -> list[dict]:
    rows = [
        row("web-hackernoon-ssh", "hackernoon", "How I Manage My VPS With Pi’s SSH Extension", "https://hackernoon.com/how-i-manage-my-vps-with-pis-ssh-extension", "Ekky Armandi", "2026-07-16", "visible HackerNoon byline date", "article", "技巧", "逐步安装 Pi 与 pi-ssh-tools，展示远程 VPS 工具集、会话非持久化和防止 SSH 锁死的安全教训。", "给出一个可审计的第三方 extension 真实运维案例和明确失败风险。", "hackernoon-pi-extensions", "ordinary Chrome read; 352 reads, full byline/date/body, install commands, ssh tool names and safety section visible", readback_backend="ordinary_user_visible_hackernoon_page", discovery_backend="external_exact_alias_search_then_user_browser", limitations="Do not execute the VPS commands from the article without an isolated test server; third-party extension source and current Pi package version still require review."),
        row("web-hackernoon-vt-theme", "hackernoon", "Decent Colors for pi.dev on a Bare Linux VT", "https://hackernoon.com/decent-colors-for-pidev-on-a-bare-linux-vt", "gmaz42", "2026-07-09", "visible HackerNoon byline date", "article", "技巧", "分析 Pi truecolor theme 在裸 Linux VT 上的限制，并用仅含八种 ANSI 颜色的 vt8.json 映射 51 个 token。", "补足 TUI 主题在旧终端环境的兼容性边界和可复现修复。", "hackernoon-pi-tui", "ordinary Chrome read; 143 reads, full byline/date/body, Pi theme assumptions and vt8 JSON visible", readback_backend="ordinary_user_visible_hackernoon_page", discovery_backend="external_pi_dev_search_then_user_browser", limitations="The proposed palette is a practitioner workaround, not an official Pi support guarantee; generic crawler access was not used."),
        row("web-hashnode-gary-tools", "hashnode", "7 Essential Tools in the badlogic/pi-mono AI Agent Toolkit", "https://gary-parker.hashnode.dev/7-essential-tools-in-the-badlogicpi-mono-ai-agent-toolkit", "Gary Parker", "2026-02-15", "visible Hashnode publication date", "article", "not applicable", "标题命中 badlogic/pi-mono，但正文实际讨论 LangChain、Playwright、Zod、Retryable、TypeScript、Jest 和 Git LFS。", "作为同名误召回负例，防止标题匹配直接进入主审。", "hashnode-exact-old-name", "ordinary Chrome full body read; title says badlogic/pi-mono but body contains generic AI testing tools and no specified Pi runtime internals", evidence_status="not_ready", readback_backend="ordinary_user_visible_hashnode_page", limitations="Rejected same-name/misleading-title result; it must not be promoted without new evidence tying the body to earendil-works/pi."),
        row("web-hashnode-gary-components", "hashnode", "7 Essential pi-mono Components for Streamlining Test Automation", "https://gary-parker.hashnode.dev/7-essential-pi-mono-components-for-streamlining-test-automation", "Gary Parker", "2026-02-13", "visible Hashnode publication date", "article", "not applicable", "标题命中 pi-mono，但正文虚构通用 lint/test/build/typecheck/format 命令，并非指定 Pi 项目结构。", "作为误认同名 monorepo 的负例，保护候选集主题边界。", "hashnode-exact-old-name", "ordinary Chrome full body read; invented @pi-mono/lint-style examples do not match the specified repository", evidence_status="not_ready", readback_backend="ordinary_user_visible_hashnode_page", limitations="Rejected unrelated same-name article; do not count it toward Pi coverage."),
        row("web-hashnode-channels", "hashnode", "Claude Code Channels Are Here - OpenClaw Was Already Doing This", "https://ai-agent-economy.hashnode.dev/claude-code-channels-are-here-openclaw-was-already-doing-this", "Up2itnow Bill Wilson", "2026-03-20", "visible Hashnode publication date", "article", "生态与案例", "正文有独立 Pi Coding Agent 小节，比较 Pi 多通道/包生态与 Claude Code Channels，但主文聚焦 OpenClaw。", "可作 Pi 多通道生态的邻接发现线索。", "hashnode-pi-ecosystem", "ordinary Chrome full body read; a named Pi Coding Agent section and explicit ecosystem comparison are visible, but Pi is not primary", evidence_status="metadata_only", readback_backend="ordinary_user_visible_hashnode_page", limitations="Pi is a secondary section, so this is not curator ready under the Pi-primary acceptance rule."),
        row("web-hashnode-symphony", "hashnode", "Symphony: Why OpenAI's PRs Jumped 500% in 3 Weeks", "https://plzai.hashnode.dev/2026-04-30-openai-symphony-codex-orchestration-linear", "jidonglab", "2026-04-30", "visible Hashnode publication date", "article", "生态与案例", "正文说明 Symphony 通过基于 pi-coding-agent 的 Kata CLI 获得模型无关执行能力，但主文聚焦 Symphony。", "提供 Pi 作为第三方 orchestration executor 底座的发现线索。", "hashnode-pi-orchestration", "ordinary Chrome full body read; one explicit pi-coding-agent/Kata passage visible in a Symphony-primary article", evidence_status="metadata_only", readback_backend="ordinary_user_visible_hashnode_page", limitations="Pi is incidental rather than the primary subject; keep metadata-only unless curator policy explicitly admits adjacent ecosystem cases."),
        row("web-producthunt-overview", "product_hunt", "Pi Coding Agent", "https://www.producthunt.com/products/pi-coding-agent-3", "Zac Zuo / Product Hunt launch team", "unknown", "visible relative time only (3mo ago); exact launch date not asserted", "product launch page", "商业化", "产品页将 Pi 定位为可定制的极简 terminal harness，列出 extensions、skills、templates、themes、npm/git packages 和刻意省略的功能。", "提供发布定位、maker 信息、评论和采用信号。", "producthunt-pi-launch", "ordinary Chrome product page read; product title/tagline, description, website, maker, 233 followers, comments and relative time visible", readback_backend="ordinary_user_visible_product_hunt_page", discovery_backend="external_exact_alias_search_then_user_browser", limitations="Product Hunt engagement is mutable and not independent technical validation; exact launch date was not visible and no vote/comment/follow action was taken."),
        row("web-producthunt-reviews", "product_hunt", "Pi Coding Agent Reviews (2026)", "https://www.producthunt.com/products/pi-coding-agent-3/reviews", "Product Hunt users", "unknown", "review collection exposes relative times, not a stable publication date", "review collection", "生态与案例", "独立 reviews 页汇集三条用户评论，涉及本地开源模型、可定制工作流、聊天分叉和期望的 session diff。", "作为采用体验线索补充正式 launch 文案。", "producthunt-pi-adoption", "ordinary Chrome review collection read; three reviews and user names visible through normal public page", evidence_status="metadata_only", readback_backend="ordinary_user_visible_product_hunt_page", discovery_backend="product_page_navigation_in_user_browser", limitations="The reviews are user claims and overlap the product overview; curator must decide near-duplicate handling. No interaction occurred."),
    ]
    return rows


def all_rows() -> list[dict]:
    return official_rows() + composio_rows() + zenn_rows() + note_rows() + restricted_platform_rows()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = all_rows()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in rows), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "items": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

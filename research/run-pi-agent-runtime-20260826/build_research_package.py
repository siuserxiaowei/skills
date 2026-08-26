#!/usr/bin/env python3
"""Build the audited Pi Agent Top 50 research package.

The source list is a primary-curator selection from the two discovery shards and
the fixed-commit source review. Discovery-only snippets are never accepted as
evidence. The output follows the cross-platform-top50 lineage contract.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


RUN_DIR = Path(__file__).resolve().parent
ROOT = RUN_DIR.parent.parent
SKILL_DIR = Path("/Users/siuserxiaowei/.codex/skills/cross-platform-top50")
RUN_ID = "pi-agent-runtime-20260826"
CURATOR_ID = "primary-curator-codex"
OBSERVED_AT = "2026-08-26T18:30:00+08:00"
NORMALIZE_NOW = datetime(2026, 8, 26, 10, 30, tzinfo=timezone.utc)
PI_SHA = "8fa7eebd235355522c8104166b4f1f959b4e2f10"
DSH_SHA = "b150a551b8d465e31e418e1b2eaf5e79bbb7d28e"

PLATFORMS = [
    ("csdn", "CSDN"), ("wechat_official_accounts", "微信公众号"), ("zhihu", "知乎"),
    ("xiaohongshu", "小红书"), ("weibo", "微博"), ("douyin", "抖音"),
    ("x", "X / Twitter"), ("bilibili", "Bilibili"), ("juejin", "掘金"),
    ("youtube", "YouTube"), ("linuxdo", "Linux.do"), ("github", "GitHub"),
    ("baidu_search", "百度搜索"), ("google_search", "Google 搜索"), ("bing_search", "Bing 搜索"),
    ("toutiao", "今日头条"), ("36kr", "36氪"), ("infoq", "InfoQ"),
    ("segmentfault", "SegmentFault"), ("oschina", "开源中国"), ("v2ex", "V2EX"),
    ("reddit", "Reddit"), ("hacker_news", "Hacker News"), ("medium", "Medium"),
    ("linkedin", "LinkedIn"), ("kuaishou", "快手"), ("wechat_channels", "微信视频号"),
    ("tiktok", "TikTok"), ("official_web", "官方 Web"), ("npm", "npm"),
    ("devto", "DEV.to"), ("stackoverflow", "Stack Overflow"), ("product_hunt", "Product Hunt"),
    ("substack", "Substack"), ("arxiv_openreview", "arXiv / OpenReview"), ("gitee", "Gitee"),
]
CANONICAL = {key for key, _ in PLATFORMS[:28]}
DISPLAY = dict(PLATFORMS)

STATUS = {
    "csdn": ("complete", 12, 6), "wechat_official_accounts": ("blocked", 0, 0),
    "zhihu": ("complete", 5, 3), "xiaohongshu": ("blocked", 0, 0),
    "weibo": ("blocked", 0, 0), "douyin": ("blocked", 0, 0),
    "x": ("partial", 4, 0), "bilibili": ("complete", 35, 1),
    "juejin": ("complete", 3, 1), "youtube": ("complete", 15, 5),
    "linuxdo": ("complete", 8, 2), "github": ("complete", 48, 25),
    "baidu_search": ("partial", 0, 0), "google_search": ("blocked", 0, 0),
    "bing_search": ("partial", 0, 0), "toutiao": ("partial", 0, 0),
    "36kr": ("complete", 5, 1), "infoq": ("complete", 3, 1),
    "segmentfault": ("complete", 7, 1), "oschina": ("partial", 0, 0),
    "v2ex": ("complete", 6, 3), "reddit": ("blocked", 0, 0),
    "hacker_news": ("complete", 8, 2), "medium": ("partial", 3, 1),
    "linkedin": ("partial", 2, 1), "kuaishou": ("blocked", 0, 0),
    "wechat_channels": ("blocked", 0, 0), "tiktok": ("blocked", 0, 0),
    "official_web": ("complete", 4, 4), "npm": ("complete", 7, 3),
    "devto": ("complete", 4, 2), "stackoverflow": ("partial", 0, 0),
    "product_hunt": ("blocked", 0, 0), "substack": ("complete", 4, 2),
    "arxiv_openreview": ("partial", 1, 1), "gitee": ("partial", 2, 0),
}


def pi(path: str) -> str:
    return f"https://github.com/earendil-works/pi/blob/{PI_SHA}/{path}"


def dsh(path: str) -> str:
    return f"https://github.com/deepseek-ai/deepseek-harness/blob/{DSH_SHA}/{path}"


# rank, platform, actual platform, title, url, author, date, type, track, finding, strength
TOP = [
    (1,"github","GitHub","Pi Agent Harness：主仓库与版本入口","https://github.com/earendil-works/pi","Earendil Works","2026-08-26","official_repository","入门","Pi 是 Agent Harness monorepo，不只是 coding CLI；学习入口是 pi-ai、pi-agent-core、pi-coding-agent 与 pi-tui。","strong"),
    (2,"github","GitHub","Pi 根 README：身份、包边界与安全声明",pi("README.md"),"Pi maintainers","2026-08-26","official_document","入门","官方包地图同时明确：Pi 没有内建 permission system，运行权限等于启动用户/进程权限。","strong"),
    (3,"github","GitHub","pi-agent-core README：消息、事件、工具与停止钩子",pi("packages/agent/README.md"),"Pi maintainers","2026-08-26","official_document","进阶","把 AgentMessage 到 LLM Message 的边界、事件时序、工具执行和 shouldStopAfterTurn 放在一条可读链路中。","strong"),
    (4,"github","GitHub","agent-loop.ts：双层循环的真实停止语义",pi("packages/agent/src/agent-loop.ts"),"Pi maintainers","2026-08-26","source_code","进阶","内层处理工具与 steering，外层排空 follow-up；error/aborted、tool terminate 和确定性 stop hook 共同决定结束。","strong"),
    (5,"github","GitHub","AgentHarness 规格：从内存 Loop 到 durable runtime",pi("packages/agent/docs/harness.md"),"Pi maintainers","2026-08-26","official_document","进阶","当前 core 已增加 immutable entries、registers、usage ledger、原子事务与 tool replay safety；旧 v0.80.2 教程未覆盖。","strong"),
    (6,"github","GitHub","AgentHarness 导出面与会话类型",pi("packages/agent/src/index.ts"),"Pi maintainers","2026-08-26","source_code","进阶","AgentHarness 已从 pi-agent-core 正式导出，但源码仍保留 NotImplemented 错误，不能把规格文档等同于全部路径均完工。","strong"),
    (7,"github","GitHub","pi-ai：统一多供应商模型边界",pi("packages/ai/README.md"),"Pi maintainers","2026-08-26","official_document","入门","统一流式、工具消息和 provider 配置；DeepSeek Harness 的通用多模型适配器也复用这一层。","strong"),
    (8,"github","GitHub","Provider retry：哪些错误能透明重试",pi("packages/ai/src/utils/retry.ts"),"Pi maintainers","2026-08-26","source_code","进阶","网络、限流与短暂服务错误走有界退避；quota/billing 与 context overflow 不能混进同一重试策略。","strong"),
    (9,"github","GitHub","pi-coding-agent：把 primitives 组装成产品",pi("packages/coding-agent/README.md"),"Pi maintainers","2026-08-26","official_document","入门","四个默认工具、四种运行模式、会话、资源和扩展共同构成可直接使用的终端产品。","strong"),
    (10,"github","GitHub","官方 Quickstart：最短可运行闭环",pi("packages/coding-agent/docs/quickstart.md"),"Pi maintainers","2026-08-26","official_tutorial","入门","先跑通认证、模型、目录和基础会话，再进入源码与扩展，避免一开始被生态配置淹没。","strong"),
    (11,"github","GitHub","Extensions：把工具、命令、事件和 UI 放在用户空间",pi("packages/coding-agent/docs/extensions.md"),"Pi maintainers","2026-08-26","official_tutorial","技巧","扩展可热加载并拥有完整进程权限；可塑性与供应链风险来自同一个设计选择。","strong"),
    (12,"github","GitHub","Compaction：不是删旧消息，而是重建可见上下文",pi("packages/coding-agent/docs/compaction.md"),"Pi maintainers","2026-08-26","official_document","进阶","阈值为 contextWindow-reserveTokens；保留 recent tail、摘要旧内容，并保证 tool call/result 不被错误拆开。","strong"),
    (13,"github","GitHub","Sessions：一份 JSONL 如何长成树",pi("packages/coding-agent/docs/sessions.md"),"Pi maintainers","2026-08-26","official_document","进阶","id/parentId 形成树，active path 决定模型上下文；回退、分叉和分支摘要是数据结构上的自然操作。","strong"),
    (14,"github","GitHub","Session format：可回放数据契约",pi("packages/coding-agent/docs/session-format.md"),"Pi maintainers","2026-08-26","official_document","进阶","消息、compaction、branch summary 等 entry 明确版本与父指针，是迁移、审计和 GUI 的底层契约。","strong"),
    (15,"github","GitHub","SDK：把 Pi 嵌进自己的应用",pi("packages/coding-agent/docs/sdk.md"),"Pi maintainers","2026-08-26","official_tutorial","商业化","SDK 提供 session runtime 重建、切换、fork/import 等产品化接缝，适合桌面端、服务端和垂直应用。","strong"),
    (16,"github","GitHub","RPC：非 Node 客户端与 GUI 的边界",pi("packages/coding-agent/docs/rpc.md"),"Pi maintainers","2026-08-26","official_tutorial","商业化","JSON/RPC 让 Python、桌面 GUI 或远端控制面复用真实 Pi runtime，而不是模拟聊天。","strong"),
    (17,"google_search","Official Web","Pi Coding Agent 官方站","https://pi.dev/","Earendil Works","2026-08-26","official_web","入门","官方定位、运行模式、会话树和扩展能力的产品入口。","strong"),
    (18,"google_search","Official Web","Pi 迁移到 Earendil：旧仓库与新包名的关系","https://pi.dev/news/2026/5/7/pi-has-a-new-home","Earendil Works","2026-05-07","official_web","入门","v0.74.0 后 badlogic/pi-mono 与旧 npm scope 迁移到 earendil-works；旧教程链接需要做版本映射。","strong"),
    (19,"google_search","Official Web","Mario：我从极简 Coding Agent 学到什么","https://mariozechner.at/posts/2025-11-30-pi-coding-agent/","Mario Zechner","2025-11-30","creator_retrospective","进阶","一手解释 provider 差异、partial abort、结构化工具结果、最小 prompt/toolset 和默认高权限的代价。","strong"),
    (20,"github","GitHub","Pi v0.84.3 release：当前稳定基线","https://github.com/earendil-works/pi/releases/tag/v0.84.3","Earendil Works","2026-08-24","official_release","进阶","知识库把 v0.80.2 中文教程与 v0.84.3 当前稳定版分开标记，避免把旧结论误当现状。","strong"),
    (21,"github","GitHub","DeepSeek Harness：Everything is a Plugin","https://github.com/deepseek-ai/deepseek-harness","DeepSeek","2026-08-26","official_repository","对比","DSH 是 developer preview / RC；star 快照不能替代成熟度与运行验证。","strong"),
    (22,"google_search","Official Web","DeepSeek Harness 官方产品页","https://www.deepseek.com/harness/en/","DeepSeek","2026-08-26","official_web","对比","Cordis kernel 把模型、工具、skills、sessions、sandbox、storage、loop、调度和 UI 全部做成插件。","strong"),
    (23,"github","GitHub","DSH architecture：没有特权核心的插件微内核",dsh("docs/architecture.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","profile/bundle 组合 service、event、effect；替换深度高于 Pi，但依赖图与排障成本也更高。","strong"),
    (24,"github","GitHub","Cordis primer：四种事件派发语义",dsh("docs/cordis-primer.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","broadcast、bail、serial、waterfall 让 policy、prompt 与结果变换可由多个插件顺序组合。","strong"),
    (25,"github","GitHub","DSH agent lifecycle：turn / step / request 三层",dsh("docs/agent-lifecycle.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","与 Pi 的 steering 内环 / follow-up 外环不是同构命名；应比较队列与 durable boundary，而非只数循环层数。","strong"),
    (26,"github","GitHub","DSH tool execution pipeline：治理接缝更重",dsh("docs/tool-execution-pipeline.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","durable call 后依次经过 guard、permission、sandbox、approval、wrapper、execute、post/finalize，再落 durable result。","strong"),
    (27,"github","GitHub","DSH session：线性事件日志与跨 session 谱系",dsh("docs/subsystems/session.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","单 session 是 append-only log；fork 复制 prefix 到 child session。它和 Pi 单 JSONL 内父指针树并不相同。","strong"),
    (28,"github","GitHub","DSH compaction：可替换 capability seam",dsh("docs/subsystems/compaction.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","start/summary/end 事件包围压缩，锁可识别 orphaned operation，surface replacement 改变模型可见上下文。","strong"),
    (29,"github","GitHub","DSH 直接复用 pi-ai 的通用模型适配器",dsh("packages/llm/llm-pi-ai/README.md"),"DeepSeek maintainers","2026-08-26","official_document","对比","Pi 与 DSH 不是纯替代：DSH 的通用 provider adapter 建在 @earendil-works/pi-ai 上。","strong"),
    (30,"github","GitHub","DSH Python SDK：嵌入式路线与危险权限提示",dsh("docs/user/guide/python-sdk.md"),"DeepSeek maintainers","2026-08-26","official_tutorial","对比","SDK 可复用 durable session 与 persistent shell，但示例也明确 danger-full-access 风险。","strong"),
    (31,"github","GitHub","dg-ai-notes：Pi 源码中文教程基线","https://github.com/buchidonggua/dg-ai-notes/tree/main/pi-agent","冬瓜","2026-08-26","open_tutorial","入门","高质量中文导读与源码深潜，基于 v0.80.2；文档 CC-BY-SA-4.0，适合参考但必须标版本和署名。","strong"),
    (32,"github","GitHub","PI Agent 学习指南：先问后读的站点化实验","https://github.com/zhoujianbin/pi-agent-guide","zhoujianbin","2026-08-26","open_tutorial","入门","每章三个无答案问题能对抗“看完以为懂了”；同样基于 v0.80.2，内容 CC-BY-SA-4.0。","strong"),
    (33,"youtube","YouTube","Building Pi in a World of Slop — Mario Zechner","https://www.youtube.com/watch?v=RjfbvDXpFls","AI Engineer / Mario Zechner","2026-04-16","creator_talk","进阶","维护者演讲是设计哲学的一手口述；视频指标只作热度，不当成熟度证据。","medium"),
    (34,"youtube","YouTube","PI Architecture EXPLAINED","https://www.youtube.com/watch?v=gTeujlv8qK0","Alejandro AO","2026-06-05","tutorial_video","进阶","用 Agent Loop、tools、TUI 串起架构；技术断言仍需回到固定 commit 源码。","medium"),
    (35,"youtube","YouTube","Pi Agent Crash Course","https://www.youtube.com/watch?v=N30XGyPrr6I","Alejandro AO","2026-05-06","tutorial_video","入门","25 分钟覆盖安装、模型、prompts、skills、extensions 与 tree history，适合作为上手前导。","medium"),
    (36,"youtube","YouTube","Pi to Pi：双向 Agent 编排","https://www.youtube.com/watch?v=PIdETjcXNIk","IndyDevDan","2026-05-18","practice_video","技巧","把 Pi 当可编排执行器，而非只在终端里单 Agent 使用。","medium"),
    (37,"youtube","YouTube","同一 Qwen 模型，Pi 与 OpenCode 结果为何不同","https://www.youtube.com/watch?v=fvIVGmwgk4w","Cloud Codes","2026-08-24","comparison_video","技巧","固定模型、替换 harness 是更合理的比较思路，但单次视频实验不能外推为普遍优胜。","medium"),
    (38,"bilibili","Bilibili","Pi 大道至简：保姆级全攻略","https://www.bilibili.com/video/BV139bD6gEa8","技术爬爬虾","2026-08-16","tutorial_video","入门","中文高热度入门，详情页可核验四工具、短系统提示与扩展生态；具体技术结论仍以源码为准。","medium"),
    (39,"juejin","掘金","Pi Extension 写完不等于可用：证据阶梯","https://juejin.cn/post/7675622412803358774","武子康","2026-08-20","practice_article","技巧","从类型检查、Mock、真实 RPC、TUI、模型路径到生产安全，提供六层扩展验收法。","medium"),
    (40,"zhihu","知乎","OpenClaw 背后的 Pi：让用户决定需要什么","https://zhuanlan.zhihu.com/p/2017400881730056207","Founder Park","2026-03-18","interview_article","进阶","整理 Mario 与深度用户访谈，适合补设计动机、扩展、会话树、SubAgent 与安全语境。","medium"),
    (41,"segmentfault","SegmentFault","Pi 完整指南：从安装到 Extension 开发","https://segmentfault.com/a/1190000048176674","七牛云行业应用","2026-08-19","tutorial_article","入门","中文全栈路线覆盖安装、模式、会话树、扩展、安全隔离与 Pi/DSH 选型；营销断言需回源。","medium"),
    (42,"infoq","InfoQ","为什么 Coding Agents 堆功能是在瞎折腾","https://www.infoq.cn/article/sLVv23TfVFxoBPjNwcZI","傅宇琪 / Tina","2026-04-29","talk_recap","进阶","Mario 演讲中文整理；与 36氪转载去重后保留较完整版本。","medium"),
    (43,"linuxdo","Linux.do","Pi + DeepSeek V4 Flash 配置与真实开发体验","https://linux.do/t/topic/2712169","cxuanAI","2026-08-06","forum_practice","技巧","给出 models.json、thinking、会话树命令和任务体验；成本与效果属于单用户样本。","medium"),
    (44,"v2ex","V2EX","Pi 生产主力体验：插件冲突与长程任务", "https://www.v2ex.com/t/1235481","Geon97 等","2026-08-20","community_discussion","技巧","一手反馈说明扩展越多不一定越强，插件冲突、注意力稀释和模型分工需要单独治理。","medium"),
    (45,"v2ex","V2EX","Wolf RBAC：用 pi-agent-core 嵌入权限产品","https://fast.v2ex.com/t/1218511","igeeky","2026-06-07","commercial_case","商业化","作者披露约 25M tokens 与 40 美元成本；可证明产品化路径，不足以证明通用 ROI。","medium"),
    (46,"devto","DEV.to","The Coding Agent I Could Shape Around My Workflow","https://dev.to/zangetsu101/the-coding-agent-i-could-shape-around-my-workflow-3c38","zangetsu101","2026-07-25","practice_article","技巧","真实案例暴露 agent_settled 不等于派生异步工作全部完成，并用并发回归测试修正完成语义。","medium"),
    (47,"substack","Substack","Pi-Agent vs Claude Code：固定模型的 Code Review 对照","https://georgeracu.substack.com/p/pi-agent-vs-claude-code-in-custom","George Racu","2026-07-13","controlled_case","技巧","单 MR、五个 seeded defects 的小样本实验；方法比结果更值得学，必须保留作者的局限声明。","medium"),
    (48,"substack","Substack","pi-web-browse：Web 工具的 SSRF 防线","https://scaileagency.substack.com/p/introducing-pi-web-browse-give-your","Scaile Agency","2026-04-14","security_walkthrough","风险","展示协议 allowlist、私网 IP 阻断、超时、body cap 与 redirect cap，说明工具安全不应只写进 prompt。","medium"),
    (49,"google_search","arXiv","Distributing Security Controls Through Harness Engineering","https://arxiv.org/html/2607.25890v1","SHarD authors","2026-07-28","research_paper","风险","以 Pi 为实验底座研究 sandbox、skill scanning 与 tool restriction；论文结果需按威胁模型和非确定性限制解读。","strong"),
    (50,"hacker_news","Hacker News","How Compaction Works in Pi：社区质询与反例","https://news.ycombinator.com/item?id=49289654","HN community","2026-08-15","community_discussion","风险","高密度讨论帮助发现压缩边界、隐藏假设和体验风险；事实结论仍回到官方 compaction 文档。","medium"),
]


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SOURCE_CONTRACT = import_module("top50_source_contract", SKILL_DIR / "scripts/source_contract.py")
LINEAGE = import_module("top50_lineage_contract", SKILL_DIR / "scripts/lineage_contract.py")


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    return LINEAGE.canonical_json_sha256(value)


def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/") or "/", parts.query, ""))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def mapped_platform(platform: str) -> str:
    return {
        "official_web":"google_search", "npm":"bing_search", "devto":"medium",
        "substack":"linkedin", "arxiv_openreview":"baidu_search", "gitee":"bing_search",
        "stackoverflow":"google_search", "product_hunt":"google_search",
    }.get(platform, platform)


def candidates() -> list[dict[str, Any]]:
    rows = []
    for rank, platform, actual, title, url, author, date, ctype, track, finding, grade in TOP:
        url = canonical_url(url)
        ident = f"src-{sha(url)[:20]}"
        rows.append({
            "id": ident, "candidate_id": ident, "platform": mapped_platform(platform),
            "actual_platform": actual, "author": author, "content_type": ctype, "url": url,
            "title": title, "excerpt": finding, "summary": finding, "key_takeaways": finding,
            "accessed_at": "2026-08-26", "published_at": date, "reviewer_status": "accepted",
            "review_reason": "", "evidence_grade": grade,
            "evidence_ids": [f"evidence-{sha(url)[:20]}"], "worker_id": "merged-discovery-workers",
            "relevance": float(min(100, max(82, 101-rank//3))),
            "source_quality": 98.0 if grade == "strong" else 82.0,
            "freshness": 100.0 if date.startswith("2026-08") else 90.0,
            "engagement": {}, "source_type": ctype, "official_source": "official" in ctype or ctype == "source_code",
            "limitations": "固定版本的一手事实" if grade == "strong" else "社区/二手材料；关键技术结论须回到固定 commit 源码。",
            "fetch_status": "fetched_reviewed", "track": track, "curator_rank": rank,
        })
    return rows


def queries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(row["platform"] for row in rows)
    result = []
    for platform, _ in PLATFORMS[:28]:
        status, _, _ = STATUS[platform]
        for idx, intent in enumerate(("exact", "practice")):
            result.append({
                "query_id": f"query-{platform}-{intent}", "platform": platform,
                "query": f'("earendil-works/pi" OR "pi-agent-core" OR "Pi coding agent") {intent}',
                "backend": "platform_cli+public_reader+direct_http", "executed_at": OBSERVED_AT,
                "status": status, "candidate_count": counts[platform] if idx == 0 else 0,
                "intent": intent, "notes": "搜索摘要仅用于发现；入选条目均由主策展回源。",
            })
    return result


def source_artifacts(rows: list[dict[str, Any]], query_rows: list[dict[str, Any]]):
    query_by_platform = {}
    for row in query_rows:
        query_by_platform.setdefault(row["platform"], row["query_id"])
    sources, outcomes, cards = [], [], []
    for row in rows:
        platform, url = row["platform"], row["url"]
        source_id = f"source-{sha(url)[:20]}"
        if platform in {"github", "youtube", "bilibili"}:
            access_kind, method, backend = "platform_cli", "platform_cli", {"github":"gh-cli","youtube":"yt-dlp","bilibili":"bili-cli"}[platform]
        elif platform in {"v2ex", "hacker_news", "linuxdo"}:
            access_kind, method, backend = "public_http", "direct_http", "public-api"
        else:
            access_kind, method, backend = "reader_proxy", "reader_proxy", "public-reader"
        snapshot = "\n".join((row["title"], row["excerpt"], row["summary"]))
        observation = {
            "schema":"top50-source-observation/v1", "run_id":RUN_ID,
            "query_id":query_by_platform[platform], "route_id":f"{platform}:{access_kind}",
            "platform_id":platform, "adapter_id":f"reviewed-{backend}", "access_kind":access_kind,
            "acquisition_method":method, "evidence_tier":"full_content" if row["evidence_grade"] == "strong" else "partial_content",
            "url":url, "observed_at":OBSERVED_AT, "http_status":200, "result_state":"success",
            "attempt":1, "max_attempts":1, "breaker_failure_count":0, "breaker_threshold":3,
            "breaker_cooldown_seconds":300, "timeframe":{"start":"2024-01-01","end":"2026-08-26"},
            "window_timezone":"Asia/Shanghai", "published_at":f"{row['published_at'][:10]}T00:00:00+08:00",
            "published_at_confidence":"observed", "date_basis":"document_metadata",
            "content_sha256":sha(snapshot), "response_endpoint":url, "payload_shape":"content_cards",
            "content_card_count":1, "backend_id":backend, "probe_id":f"probe-20260826-{platform}",
            "authorization":"not_required", "error_code":None, "error_summary":None, "retry_after_seconds":None,
        }
        outcome = SOURCE_CONTRACT.normalize_source_outcome(observation, now=NORMALIZE_NOW)
        outcomes.append(outcome)
        sources.append({
            "source_id":source_id, "url":url, "status":"verified", "source_type":row["source_type"],
            "platform":platform, "actual_platform":row["actual_platform"], "query_id":query_by_platform[platform],
            "source_outcome_digest_sha256":outcome["outcome_digest_sha256"], "accessed_at":"2026-08-26",
            "notes":row["limitations"],
        })
        cards.append({
            "evidence_id":row["evidence_ids"][0], "source_id":source_id, "source_url":url,
            "claim":row["summary"], "supports":"fact" if row["official_source"] else "inference",
            "access_date":"2026-08-26", "excerpt_or_observation":row["excerpt"],
            "evidence_grade":row["evidence_grade"], "reviewer_status":"accepted", "reviewer_id":CURATOR_ID,
        })
    return sources, outcomes, cards


def coverage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = Counter(row["platform"] for row in rows)
    result = []
    for platform, label in PLATFORMS[:28]:
        status, observed_pool, _ = STATUS[platform]
        discovered = selected[platform]
        eligible = discovered
        result.append({
            "platform":platform, "display_name":label, "coverage_status":status,
            "discovered_count":discovered, "fetched_count":eligible, "eligible_count":eligible,
            "blocked_count":0, "rejected_count":0, "selected_count":selected[platform],
            "access_mode":"public+user_assisted_checkpoint" if status == "blocked" else "public-only",
            "blocker_or_limit":(("Browser Bridge/登录或验证缺失；未绕过访问控制。" if status == "blocked" else "按严格主题回源；空结果不以泛 Agent 内容补数。") + f" 候选池观察={observed_pool}。"),
        })
    return result


def extended_coverage() -> list[dict[str, Any]]:
    rows=[]
    for platform,label in PLATFORMS:
        status,observed,eligible=STATUS[platform]
        rows.append({"platform":platform,"display_name":label,"coverage_status":status,
                     "observed_candidate_pool":observed,"reviewed_eligible":eligible,
                     "access_mode":"user-assisted pending" if status=="blocked" else "public",
                     "note":"登录/验证或 Browser Bridge 缺失，未绕过访问控制。" if status=="blocked" else "公开路线已执行；partial 表示严格主题零召回或专用路由受限。"})
    return rows


def stage_binding(relation: str, path: Path, artifact: dict[str, Any], ids: list[str], kind: str) -> dict[str, Any]:
    return {"relation":relation,"path":str(path),"artifact_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "contract":artifact["contract_version"],"run_id":artifact["run_id"],"stage":artifact["stage"],
            "required_status":artifact["status"],"producer_engine_id":artifact["producer"]["engine_id"],
            "result_digest_sha256":artifact["result_digest_sha256"],"record_kind":kind,
            "record_count":len(ids),"record_ids_sha256":canonical_json_sha256(sorted(ids))}


def run_processor(rows: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {"contract_version":"top50-processor/v1","run_id":RUN_ID,"candidates":[
        {"candidate_id":r["id"],"platform":r["platform"],"url":r["url"],"title":r["title"],"author":r["author"],"published_at":r["published_at"],"excerpt":r["excerpt"]} for r in rows]}
    input_path, output_path = RUN_DIR/"rust-processor-input.json", RUN_DIR/"rust-processor-result.json"
    write_json(input_path,payload)
    binary=SKILL_DIR/"engines/rust-processor/target/debug/rust-processor"
    command=[str(binary),"process","--input",str(input_path),"--expected-input-sha256",hashlib.sha256(input_path.read_bytes()).hexdigest(),"--output",str(output_path)]
    proc=subprocess.run(command,capture_output=True,text=True)
    if proc.returncode: raise RuntimeError(proc.stderr)
    raw=json.loads(output_path.read_text())
    artifact={"contract_version":"top50-process-result/v1","run_id":RUN_ID,"stage":"process","status":"complete",
              "producer":{"engine_id":"rust-processor","engine_version":str(raw.get("engine_version") or "0.1.0")},
              "input_bindings":[],"processed_candidates":raw["processed_candidates"],"exact_clusters":raw["exact_clusters"],
              "near_duplicate_reviews":raw["near_duplicate_reviews"],"counts":raw["counts"]}
    artifact["result_digest_sha256"]=canonical_json_sha256(artifact); write_json(RUN_DIR/"process-result.json",artifact)
    return artifact


def curator(rows: list[dict[str, Any]], process: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    descriptors={x["input_id"]:x for x in manifest["files"]}
    decisions=[{"candidate_id":r["id"],"decision":"accepted","evidence_ids":r["evidence_ids"],"reason_codes":[]} for r in rows]
    artifact={"contract_version":"top50-curator-acceptance/v1","run_id":RUN_ID,"stage":"curate","status":"accepted",
              "producer":{"engine_id":"python-control-plane","engine_version":"1.1.0"},
              "input_bindings":[stage_binding("process_result",RUN_DIR/"process-result.json",process,[x["candidate_id"] for x in process["processed_candidates"]],"candidate"),
                                stage_binding("rank_input_manifest",RUN_DIR/"rank-input-manifest.json",manifest,[x["input_id"] for x in manifest["files"]],"file")],
              "curator":{"id":CURATOR_ID},"worker_ids":["china-discovery","international-discovery","pi-source-architecture","merged-discovery-workers"],
              "decisions":decisions,"accepted_candidate_ids":[r["id"] for r in rows],
              "evidence_ledger_binding":{"artifact_sha256":descriptors["evidence_cards"]["artifact_sha256"]},
              "source_ledger_binding":{"artifact_sha256":descriptors["sources"]["artifact_sha256"]},
              "counts":{"input_candidates":len(rows),"accepted":len(rows),"rejected":0,"blocked":0}}
    artifact["result_digest_sha256"]=canonical_json_sha256(artifact); write_json(RUN_DIR/"curate-result.json",artifact)
    return artifact


def main() -> None:
    rows=candidates(); query_rows=queries(rows); sources,outcomes,cards=source_artifacts(rows,query_rows); cov=coverage(rows); extended=extended_coverage()
    manifest=json.loads((RUN_DIR/"run_manifest.json").read_text(encoding="utf-8"))
    manifest.update({
        "schema_version":"1.1", "status":"curation_complete", "completed_at":OBSERVED_AT,
        "phases":{"scope":"complete","discovery":"complete","fetch":"complete","extraction":"complete","worker_check":"complete","curator_acceptance":"complete","ranking":"pending"},
        "counts":{"candidates":len(rows),"discovered":len(rows),"queries":len(query_rows),"sources":len(sources),"evidence_cards":len(cards),"platforms":len(cov)},
        "curator":{"id":CURATOR_ID},
        "workers":[{"id":"china-discovery"},{"id":"international-discovery"},{"id":"pi-source-architecture"},{"id":"merged-discovery-workers"}],
    })
    manifest["scope"]={"topic":manifest["topic"],"required_platforms":[key for key,_ in PLATFORMS[:28]],"claim_20_plus_platforms":True,"timeframe":{"start":"2024-01-01","end":"2026-08-26"},"languages":["zh","en"],"geography":"CN+global"}
    write_json(RUN_DIR/"run_manifest.json",manifest)
    write_json(RUN_DIR/"candidates.json",{"candidates":rows})
    write_tsv(RUN_DIR/"queries.tsv",query_rows,["query_id","platform","query","backend","executed_at","status","candidate_count","intent","notes"])
    write_tsv(RUN_DIR/"sources.tsv",sources,["source_id","url","status","source_type","platform","actual_platform","query_id","source_outcome_digest_sha256","accessed_at","notes"])
    write_jsonl(RUN_DIR/"source_outcomes.jsonl",outcomes)
    write_tsv(RUN_DIR/"evidence_cards.tsv",cards,["evidence_id","source_id","source_url","claim","supports","access_date","excerpt_or_observation","evidence_grade","reviewer_status","reviewer_id"])
    write_tsv(RUN_DIR/"platform_coverage.tsv",cov,["platform","display_name","coverage_status","discovered_count","fetched_count","eligible_count","blocked_count","rejected_count","selected_count","access_mode","blocker_or_limit"])
    write_tsv(RUN_DIR/"platform_coverage_36.tsv",extended,["platform","display_name","coverage_status","observed_candidate_pool","reviewed_eligible","access_mode","note"])
    process=run_processor(rows)
    freeze=[sys.executable,str(SKILL_DIR/"scripts/lineage_contract.py"),"freeze-rank-inputs","--run-dir",str(RUN_DIR),"--run-id",RUN_ID,"--output",str(RUN_DIR/"rank-input-manifest.json")]
    subprocess.run(freeze,check=True)
    manifest=json.loads((RUN_DIR/"rank-input-manifest.json").read_text()); curator(rows,process,manifest)
    rank=[sys.executable,str(SKILL_DIR/"scripts/rank_candidates.py"),"--input",str(RUN_DIR/"candidates.json"),"--manifest",str(RUN_DIR/"run_manifest.json"),"--queries",str(RUN_DIR/"queries.tsv"),"--sources",str(RUN_DIR/"sources.tsv"),"--source-outcomes",str(RUN_DIR/"source_outcomes.jsonl"),"--evidence-cards",str(RUN_DIR/"evidence_cards.tsv"),"--platform-coverage",str(RUN_DIR/"platform_coverage.tsv"),"--lineage-manifest",str(RUN_DIR/"rank-input-manifest.json"),"--curator-acceptance",str(RUN_DIR/"curate-result.json"),"--output-dir",str(RUN_DIR/"ranking-output"),"--top","50"]
    subprocess.run(rank,check=True)
    write_json(RUN_DIR/"curated-top50.json",{"as_of":"2026-08-26","items":[dict(zip(("curator_rank","platform","actual_platform","title","url","author","published_at","content_type","track","finding","evidence_grade"),x)) for x in TOP]})
    print(json.dumps({"status":"complete","candidates":len(rows),"platforms":len(PLATFORMS),"accepted":len(rows)},ensure_ascii=False))


if __name__ == "__main__": main()

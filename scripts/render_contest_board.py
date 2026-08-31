#!/usr/bin/env python3
"""Render the fixed 1920x1080 Goal Compiler contest board.

This is a deterministic presentation renderer for existing demo evidence. It
does not generate semantic content or claim a live model call.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


WIDTH = 1920
HEIGHT = 1080
INK = "#101828"
MUTED = "#667085"
PAPER = "#FFFDF6"
PAGE = "#EFEEE8"
LIME = "#D9FF57"
VIOLET = "#7557FF"
RED = "#FF5C5C"
GREEN = "#2DD4A7"
AMBER = "#FFBF47"

FONT_CANDIDATES = (
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = list(FONT_CANDIDATES)
    if bold:
        candidates.insert(0, "/System/Library/Fonts/STHeiti Medium.ttc")
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def draw_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    step: str,
    title: str,
    body: str,
    state: str,
    state_color: str,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1 + 7, y1 + 7, x2 + 7, y2 + 7), radius=26, fill=INK)
    draw.rounded_rectangle(box, radius=26, fill=PAPER, outline=INK, width=3)
    draw.text((x1 + 28, y1 + 24), step, font=font(20, bold=True), fill=VIOLET)
    draw.multiline_text((x1 + 28, y1 + 76), title, font=font(31, bold=True), fill=INK, spacing=7)
    draw.multiline_text((x1 + 28, y1 + 180), body, font=font(20), fill=MUTED, spacing=7)
    state_width = int(draw.textlength(state, font=font(18, bold=True))) + 28
    draw.rounded_rectangle((x1 + 28, y2 - 54, x1 + 28 + state_width, y2 - 18), radius=9, fill=state_color)
    state_ink = INK if state_color in {LIME, GREEN, AMBER} else "#FFFFFF"
    draw.text((x1 + 42, y2 - 48), state, font=font(18, bold=True), fill=state_ink)


def render(output: Path) -> None:
    if output.exists():
        raise ValueError(f"refusing to overwrite existing file: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), PAGE)
    draw = ImageDraw.Draw(image)
    draw.text((80, 58), "VIBEWORK  /  EXECUTABLE AGENT SKILL", font=font(23, bold=True), fill=VIOLET)
    draw.rounded_rectangle((1582, 48, 1840, 98), radius=25, fill=LIME, outline=INK, width=3)
    draw.text((1610, 59), "liveAiClaimed:false", font=font(18, bold=True), fill=INK)

    draw.multiline_text(
        (74, 126),
        "GOAL COMPILER\n需求编译器",
        font=font(78, bold=True),
        fill=INK,
        spacing=-4,
    )
    draw.multiline_text(
        (760, 145),
        "把“越快越好”编译成\n能 FAIL、能反证、知道何时停止的契约。",
        font=font(44, bold=True),
        fill=INK,
        spacing=12,
    )

    card_y1 = 390
    card_y2 = 840
    gap = 22
    card_width = 424
    left = 78
    cards = (
        ("01 / AGENT RESULT", "完整语义\n进入 CLI", "website / 模糊想法\n路由 · 策略 · 反证\nliveAiClaimed:false", "AGENT RESULT", VIOLET),
        ("02 / METRIC GATE", "“看起来\n足够好看”", "statement 主观\nmethod 主观\n只写 FAIL.log", "VALIDATOR FAIL", RED),
        ("03 / EVIDENCE", "研究来源\n不能跳过", "缺 sources + claims\n不允许审批\n不伪造市场证据", "EVIDENCE PENDING", AMBER),
        ("04 / HUMAN", "精确指标\n与执行范围", "四项 acknowledgment\napproved payload SHA-256\n本次未执行", "HUMAN PENDING", AMBER),
    )
    for index, card in enumerate(cards):
        x1 = left + index * (card_width + gap)
        draw_card(draw, (x1, card_y1, x1 + card_width, card_y2), *card)

    draw.rounded_rectangle((78, 900, 1842, 1000), radius=18, fill=INK)
    draw.text((110, 921), "AGENT / SKILL", font=font(20, bold=True), fill=LIME)
    draw.text((110, 954), "语义编译与默认假设", font=font(21), fill="#FFFFFF")
    draw.text((620, 921), "HUMAN", font=font(20, bold=True), fill=LIME)
    draw.text((620, 954), "修改指标并审批", font=font(21), fill="#FFFFFF")
    draw.text((1040, 921), "CLI VALIDATOR / EXECUTOR", font=font(20, bold=True), fill=LIME)
    draw.text((1040, 954), "确定性验证、审批绑定与白名单调度", font=font(21), fill="#FFFFFF")
    draw.text((80, 1030), "github.com/siuserxiaowei/xiaowei-goal  ·  v0.13.0  ·  HUMAN_PENDING  ·  MIT", font=font(18), fill=MUTED)

    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", "Goal Compiler contest board")
    metadata.add_text("Author", "Xiaowei project")
    metadata.add_text("Provenance", "Deterministic rendering of first-party contest demo evidence")
    image.save(output, format="PNG", optimize=True, pnginfo=metadata)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new PNG output path")
    args = parser.parse_args()
    try:
        render(Path(args.output).expanduser().resolve())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Rendered {WIDTH}x{HEIGHT} board -> {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

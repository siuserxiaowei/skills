# Third-Party Notices

## qiaomu-goal-meta-skill

- Repository: https://github.com/joeseesun/qiaomu-goal-meta-skill
- Referenced commit: `f29e0189f2ea03392c50b4f1c7230886bd838a13`
- License reported by GitHub: MIT
- Relationship: directional inspiration for the public `/goal` meta-skill case.
- Bundled code/assets: none.

## Agent Reach

- Repository: https://github.com/Panniantong/Agent-Reach
- Relationship: optional external capability named in research-routing
  instructions.
- Bundled code/assets: none.
- Runtime requirement for the fixed contest demo: none; the fixture does not
  browse or claim that Agent Reach was invoked.

## Python

The runtime uses only Python standard-library modules. No PyPI package, remote
script, third-party JavaScript, font, image, audio, or video asset is bundled.

The checked-in 1920x1080 contest board was rendered locally with Pillow and a
system font. Pillow is not bundled or required by the Goal Compiler runtime or
CI; `scripts/render_contest_board.py` is an optional reproducibility helper.

Synthetic URLs under `tests/fixtures/` exist only to exercise deterministic
evidence validation. They are not third-party content or real research claims.

The repository's own MIT license remains in `LICENSE`. This notice preserves
source relationships; it does not change third-party license terms.

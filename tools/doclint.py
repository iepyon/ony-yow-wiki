#!/usr/bin/env python3
"""doclint — 規約の写しがずれていないかを機械で見つける。

実行:  uv run --with pyyaml --no-project python3 tools/doclint.py
終了コード: error があれば 1、無ければ 0。

oylint がカードを ontology.yaml に照らすのと同じことを、**規約そのもの**に対してやる。
「ここにしか無い規約だけを書く」（CLAUDE.md 冒頭）は人間にも AI にも守れなかったので、
守れたかどうかを機械が見る（20260816-01）。

見るもの:
  1. templates/{ony,yow}.md の frontmatter キー・節見出しが ontology.yaml の宣言と一致するか。
     宣言に無いキーは**死んだ規約** — 廃止した昇格フラグ `slide` がテンプレだけに
     残り続けていた（2026-08-16 に発見）。コメントアウトされた行も見る。
  2. ドキュメントに書かれた `uv run ... tools/X.py` が実在するツールを指すか。
     tools/gen_slide_svg.py を消したとき、コマンド行が残れば落ちる。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ONT = yaml.safe_load((ROOT / "ontology.yaml").read_text(encoding="utf-8"))

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
# コメントアウトされた宣言（`# relates: [...]`）も拾う — 死んだキーはそこに残るため
KEY_RE = re.compile(r"^\s*#?\s*([A-Za-z_][A-Za-z0-9_]*)\s*:")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
# `uv run ... tools/X.py` の X。実行行だけを見る（散文中の言及は対象外）
CMD_RE = re.compile(r"uv run [^\n`]*?(tools/[A-Za-z0-9_]+\.py)")

# 生成物・ローカル専用は対象外
SKIP_DIRS = {"wiki", "origin", "out", "node_modules", ".git"}


def docs() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md")
                  if not (SKIP_DIRS & set(p.relative_to(ROOT).parts)))


def check_templates(add) -> None:
    """テンプレートが ontology.yaml の宣言からずれていないか。"""
    for ctype, decl in ONT["cards"].items():
        path = ROOT / "templates" / f"{ctype}.md"
        name = f"templates/{ctype}.md"
        if not path.exists():
            add("error", name, f"{ctype} カードのテンプレートが無い")
            continue
        text = path.read_text(encoding="utf-8")

        m = FM_RE.match(text)
        if not m:
            add("error", name, "frontmatter が無い（--- で始まっていない）")
            continue
        declared = set(decl["fields"])
        found = {k for line in m.group(1).splitlines() if (k := (KEY_RE.match(line) or [None, None])[1])}
        for key in sorted(found - declared):
            add("error", name, f"ontology.yaml の {ctype}.fields に無いキー '{key}' — "
                               "廃止された規約がテンプレに残っている（コメントアウトも含めて消す）")
        for key in sorted({k for k, d in decl["fields"].items() if d.get("required")} - found):
            add("error", name, f"必須フィールド '{key}' がテンプレに無い")

        declared_h = {s["heading"] for s in decl["sections"]}
        found_h = set(HEADING_RE.findall(text))
        for h in sorted(found_h - declared_h):
            add("error", name, f"ontology.yaml の {ctype}.sections に無い節 '## {h}'")
        for h in sorted({s["heading"] for s in decl["sections"] if s.get("required")} - found_h):
            add("error", name, f"必須の節 '## {h}' がテンプレに無い")


def check_commands(add) -> None:
    """ドキュメントのコマンド行が実在するツールを指しているか。"""
    for path in docs():
        name = str(path.relative_to(ROOT))
        for tool in sorted(set(CMD_RE.findall(path.read_text(encoding="utf-8")))):
            if not (ROOT / tool).exists():
                add("error", name, f"`uv run ... {tool}` — そのツールは存在しない")


def main() -> int:
    problems = []

    def add(sev, name, msg):
        problems.append((sev, name, msg))

    check_templates(add)
    check_commands(add)

    errors = sum(1 for s, _, _ in problems if s == "error")
    for sev, name, msg in problems:
        print(f"{'❌' if sev == 'error' else '⚠️ '} [{sev}] {name} | {msg}")
    print(f"{'❌' if errors else '✅'} 規約の写しを検査 — error {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

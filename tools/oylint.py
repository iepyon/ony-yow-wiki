#!/usr/bin/env python3
"""oylint — ontology.yaml の宣言に照らしてカードを機械検査する。

実行:  uv run --with pyyaml python3 tools/oylint.py [--pending]
終了コード: error があれば 1、無ければ 0（info/warning は落とさない）。
語彙・診断名はここに書かない — 正本は ontology.yaml。
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ONT = yaml.safe_load((ROOT / "ontology.yaml").read_text(encoding="utf-8"))

FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def parse_card(path: Path):
    """frontmatter dict と {節見出し: 本文} を返す。壊れていれば (None, None, 理由)。"""
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return None, None, "frontmatter が無い（--- で始まっていない）"
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, None, f"frontmatter が YAML として読めない: {e}"
    body = text[m.end():]
    sections = {}
    cur = None
    for line in body.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    sections = {h: "\n".join(ls).strip() for h, ls in sections.items()}
    return fm, sections, None


def main() -> int:
    problems = []          # (severity, card, message)
    cards = {}             # (type, id) -> (fm, sections)

    def add(sev, name, msg):
        problems.append((sev, name, msg))

    # ── 収集と単体検査 ────────────────────────────────────────
    for ctype, decl in ONT["cards"].items():
        cdir = ROOT / decl["dir"]
        for path in sorted(cdir.glob("*.md")) if cdir.exists() else []:
            name = f"{decl['dir']}/{path.name}"
            fm, sections, err = parse_card(path)
            if err:
                add("error", name, err)
                continue
            cards[(ctype, path.stem)] = (fm, sections)

            # id = ファイル名 / type = ディレクトリ
            if fm.get("id") != path.stem:
                add("error", name, f"id '{fm.get('id')}' がファイル名と一致しない")
            if fm.get("type") != ctype:
                add("error", name, f"type '{fm.get('type')}' が置き場 ({ctype}) と一致しない")

            # フィールド: 必須・pattern・語彙・宣言外キー
            for fname, fdecl in decl["fields"].items():
                val = fm.get(fname)
                if fdecl.get("required") and val is None:
                    add("error", name, f"必須フィールド '{fname}' が無い")
                    continue
                if val is None:
                    continue
                if "pattern" in fdecl and not re.fullmatch(fdecl["pattern"], str(val)):
                    add("error", name, f"'{fname}: {val}' が書式 {fdecl['pattern']} に合わない")
                if "vocab" in fdecl and val not in ONT["vocabularies"][fdecl["vocab"]]:
                    add("error", name, f"'{fname}: {val}' が語彙 {ONT['vocabularies'][fdecl['vocab']]} に無い")
                if "const" in fdecl and val != fdecl["const"]:
                    add("error", name, f"'{fname}' は '{fdecl['const']}' 固定")
            for key in fm:
                if key not in decl["fields"]:
                    add("warning", name, f"宣言に無いキー '{key}'（タイポ?）")

            # 節: 必須見出しの存在（中身は自由 — 規律を課さない）
            declared = {s["heading"] for s in decl["sections"]}
            for s in decl["sections"]:
                if s.get("required") and s["heading"] not in sections:
                    add("error", name, f"必須の節 '## {s['heading']}' が無い")
            for h in sections:
                if h not in declared:
                    add("warning", name, f"宣言に無い節 '## {h}'")

    # ── つながり ──────────────────────────────────────────────
    for link in ONT["links"]:
        for (ctype, cid), (fm, _) in cards.items():
            if ctype != link["from"]:
                continue
            raw = fm.get(link["name"])
            if raw is None:
                if link.get("required"):
                    add("error", f"{ctype}/{cid}", f"必須のつながり '{link['name']}' が無い")
                continue
            targets = raw if isinstance(raw, list) else [raw]
            for t in targets:
                if (link["to"], str(t)) not in cards:
                    add("error", f"{ctype}/{cid}", f"{link['name']}: '{t}' — 参照先の {link['to']} カードが存在しない")
                if link.get("rule") == "same-id" and str(t) != cid:
                    add("error", f"{ctype}/{cid}", f"{link['name']} は自分と同じ ID を指す規約（'{t}' ≠ '{cid}'）")

    # ── 引き算診断（info・記録は止めない） ─────────────────────
    for (ctype, cid), (fm, sections) in cards.items():
        if ctype != "ony":
            continue
        decl = ONT["cards"]["ony"]
        empty = set()
        empty_cp = set()
        for s in decl["sections"]:
            filled = bool(sections.get(s["heading"], "").strip().strip("—"))
            if not filled:
                (empty_cp if s.get("actor") == "counterpart" else empty).add(s["element"])
        act = fm.get("activity")
        for rule in ONT["diagnostics"]["rules"]:
            if rule["activity"] != act:
                continue
            if set(rule.get("missing", [])) <= empty and set(rule.get("missing-counterpart", [])) <= empty_cp \
               and (rule.get("missing") or rule.get("missing-counterpart")):
                add("info", f"ony/{cid}", f"〈{act}〉で {'・'.join(rule.get('missing', rule.get('missing-counterpart')))} が空 → **{rule['name']}**（p150。分類であって禁止ではない）")

    # ── 未検証一覧（--pending） ───────────────────────────────
    if "--pending" in sys.argv:
        for (ctype, cid), (fm, _) in sorted(cards.items()):
            if ctype == "ony" and ("yow", cid) not in cards:
                add("info", f"ony/{cid}", f"未検証（YOW カード待ち）: {fm.get('title', '')}")

    # ── 報告 ──────────────────────────────────────────────────
    errors = sum(1 for s, _, _ in problems if s == "error")
    for sev, name, msg in problems:
        mark = {"error": "❌", "warning": "⚠️ ", "info": "ℹ️ "}[sev]
        print(f"{mark} [{sev}] {name} | {msg}")
    total = len(cards)
    print(f"{'❌' if errors else '✅'} カード {total} 件を検査 — error {errors} / warning "
          f"{sum(1 for s, _, _ in problems if s == 'warning')} / info {sum(1 for s, _, _ in problems if s == 'info')}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

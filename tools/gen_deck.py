#!/usr/bin/env python3
"""gen_deck — 全カードから週デッキ（サマリー + 日々のループスライド）を合成する。

実行:  uv run --with pyyaml --no-project python3 tools/gen_deck.py [--check]
生成物: wiki/<owner>-<YYYY>-w<WW>.md（週1ファイル。冒頭に週サマリー、続けて1ループ=1枚）
        wiki/img/<ID>.svg（ループスライドの画像 — PR 本文が貼る。描画は gen_slide_svg.py）
        wiki/order.yaml
すべて手編集禁止。構成・セル並び・埋め文字の正本は ontology.yaml の deck 節。
--check は差分があれば非0（週明けは前週 status の stable 化で必ず差分が出る = 週締め PR の種）。
"""
import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_slide_svg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ONT = yaml.safe_load((ROOT / "ontology.yaml").read_text(encoding="utf-8"))
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
PER_SLIDE = 5   # W カタログ・未検証一覧の1枚あたりループ数（1000字制限対策）


def parse(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    fm = yaml.safe_load(m.group(1))
    sections, cur = {}, None
    for line in text[m.end():].splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return fm, {h: "\n".join(v).strip() for h, v in sections.items()}


def card_date(fm) -> dt.date:
    return dt.date.fromisoformat(fm["date"][:10])


def week_of(d: dt.date):
    y, w, _ = d.isocalendar()
    return y, w


def deck_name(owner: str, y: int, w: int) -> str:
    return f"{owner}-{y}-w{w:02d}"


def week_of_card_id(cid: str):
    d = dt.datetime.strptime(str(cid).split("-")[0], "%Y%m%d").date()
    return week_of(d)


def chunk(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def loop_cells(osec, ysec):
    """ループスライドの6セルを行優先で [(見出し, 本文)] にする。
    デッキ本文・SVG（gen_slide_svg）・PR 本文（gen_pr_body）はここだけを源にする。"""
    decl = ONT["deck"]["loop-slides"]
    cells = []
    for c in decl["cells"]:
        src = osec if c["source"] == "ony" else (ysec or {})
        body = src.get(c["section"], "").strip() or decl["unverified-fill"]
        if c.get("merge-yow") and ysec:
            done = ysec.get(c["merge-yow"], "").strip()
            if done and done != body:
                body = f"{body} → {done}"
        cells.append((c["heading"], body))
    return cells


def gen_week(owner, y, w, loops, today):
    """loops: [(ony_fm, ony_sec, yow_fm|None, yow_sec|None)] を週デッキ1本の md にする。"""
    decl = ONT["deck"]
    fill = decl["loop-slides"]["unverified-fill"]
    mon = dt.date.fromisocalendar(y, w, 1)
    sun = mon + dt.timedelta(days=6)
    status = "draft" if (y, w) >= week_of(today) else "stable"
    created = min(card_date(fm).isoformat() for fm, _, _, _ in loops)
    name = deck_name(owner, y, w)
    verified = [t for t in loops if t[2]]
    pending = [t for t in loops if not t[2]]

    out = ["---", "type: deck", f"title: {owner} {y}-W{w:02d}", f"short: W{w:02d}",
           # 値に ": " を入れない（frontmatter が YAML として壊れ、外部ツールが読めなくなる）
           f"description: {mon}〜{sun} の ONY-YOW（{owner}）— 週サマリーと日々のループ",
           f"tags: [ony-yow, {owner}, {mon.year}-{mon.month:02d}]",
           f"status: {status}", f"author: {owner}", f"created: {created}", "---",
           "", f"# {owner} {y}-W{w:02d}",
           f"{mon} 〜 {sun}（gen_deck.py の生成物 — 手編集しない）"]

    # ── 週サマリー: 今週の数字（Table） ──
    by_day = {}
    for t in loops:
        by_day.setdefault(card_date(t[0]), []).append(t)
    out += ["", "---", "", "## 今週の数字", "<!--table-->", f"<!--id:stats-->",
            "| 日付 | ループ | 検証済 | 活動 |", "| --- | --- | --- | --- |"]
    for d in sorted(by_day):
        ls = by_day[d]
        acts = "、".join(f"{a}{c}" for a, c in Counter(t[0]["activity"] for t in ls).items())
        out.append(f"| {d.strftime('%m-%d')} | {len(ls)} | {sum(1 for t in ls if t[2])} | {acts} |")
    out += ["<!--takeaway-->",
            f"計 {len(loops)} ループ / 検証済 {len(verified)} / 未検証 {len(pending)}"]

    # ── 週サマリー: W カタログ（同デッキ内リンク） ──
    for i, page in enumerate(chunk(verified, PER_SLIDE)):
        suffix = f"（{i + 1}）" if len(verified) > PER_SLIDE else ""
        out += ["", "---", "", f"## W カタログ{suffix}", f"<!--id:w-catalog-{i + 1}-->"]
        for ofm, _, _, ysec in page:
            out += [f"### {ofm['title']}",
                    (ysec.get("W 分かったこと", "").strip() or fill)
                    + f"（[{ofm['id']}]({name}.md#{ofm['id']})）"]

    # ── 週サマリー: 未検証（回しっぱなし検知） ──
    if pending:
        out += ["", "---", "", "## 未検証", "<!--id:pending-->"]
        for ofm, osec, _, _ in pending[:PER_SLIDE * 2]:
            out += [f"### {ofm['title']}",
                    f"O2: {osec.get('O2 起きそうなこと', '').strip() or fill}"
                    f"（[{ofm['id']}]({name}.md#{ofm['id']})）"]

    # ── 日々のループスライド（1日単位の記録・日付順） ──
    for ofm, osec, yfm, ysec in loops:
        out += ["", "---", "", f"## {ofm['title']}",
                f"<!--{decl['loop-slides']['layout']}-->", f"<!--id:{ofm['id']}-->"]
        for heading, body in loop_cells(osec, ysec):
            out += [f"### {heading}", body]
        parts = [ofm["id"], ofm["activity"], "検証済" if yfm else "未検証"]
        for rel in (ofm.get("relates") or []):
            ry, rw = week_of_card_id(rel)
            parts.append(f"関連 [{rel}]({deck_name(owner, ry, rw)}.md#{rel})")
        out += ["<!--takeaway-->", " / ".join(parts)]
    return "\n".join(out) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    today = dt.date.today()

    onys = {p.stem: parse(p) for p in sorted((ROOT / ONT["cards"]["ony"]["dir"]).glob("*.md"))}
    yows = {p.stem: parse(p) for p in sorted((ROOT / ONT["cards"]["yow"]["dir"]).glob("*.md"))}

    weeks = {}
    for cid, (fm, sec) in onys.items():
        yfm, ysec = yows.get(cid, (None, None))
        y, w = week_of(card_date(fm))
        weeks.setdefault((fm["owner"], y, w), []).append((fm, sec, yfm, ysec))

    outputs = {}
    month_groups = {}
    for (owner, y, w), loops in sorted(weeks.items()):
        loops.sort(key=lambda t: t[0]["id"])
        name = deck_name(owner, y, w)
        outputs[ROOT / "wiki" / f"{name}.md"] = gen_week(owner, y, w, loops, today)
        for ofm, osec, yfm, ysec in loops:   # ループスライドの画像（PR 本文が貼る）
            outputs[ROOT / "wiki" / "img" / f"{ofm['id']}.svg"] = \
                gen_slide_svg.render(ofm, loop_cells(osec, ysec), yfm is not None)
        mon = dt.date.fromisocalendar(y, w, 1)
        month_groups.setdefault(f"{mon.year}-{mon.month:02d}", []).append(name)

    order = ["groups: # 生成物（gen_deck.py）— 手編集しない。グループ = 週の月曜が属する月"]
    for month in sorted(month_groups):
        order += [f"  - title: {month}", f"    decks: [{', '.join(month_groups[month])}]"]
    outputs[ROOT / "wiki" / "order.yaml"] = "\n".join(order) + "\n"

    # 生成対象外になった古いデッキ md・スライド画像（カード削除・粒度変更の残骸）。
    # 掃除は gen_deck が作る種類（wiki/*.md と wiki/img/*.svg）だけに限る —
    # wiki/ には gen-okf-index.ts など他のツールの生成物も同居するので巻き添えで消さない。
    keep = set(outputs) | {ROOT / "wiki" / n for n in ("index.md", "log.md")}
    mine = [*(ROOT / "wiki").glob("*.md"), *(ROOT / "wiki" / "img").glob("*.svg")]
    stale = [p for p in mine if p not in keep]

    drift = 0
    for path, content in outputs.items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != content:
            drift += 1
            if check:
                print(f"❌ 鮮度切れ: {path.relative_to(ROOT)}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                print(f"生成: {path.relative_to(ROOT)}")
    for p in stale:
        drift += 1
        if check:
            print(f"❌ 生成対象外の残骸: {p.relative_to(ROOT)}")
        else:
            p.unlink()
            print(f"削除: {p.relative_to(ROOT)}")
    if check:
        print("✅ デッキはカードと一致している" if drift == 0 else f"❌ {drift} 件の再生成が必要")
        return 1 if drift else 0
    if drift == 0:
        print("✅ 変更なし（デッキはカードと一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

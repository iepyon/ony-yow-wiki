#!/usr/bin/env python3
"""gen_pr_body — その日のループを PR 本文（A3 ライト = 1ループ1枚）に合成する。

実行:  uv run --with pyyaml --no-project python3 tools/gen_pr_body.py [YYYY-MM-DD] > /tmp/pr-body.md
出力:  標準出力に PR 本文の Markdown（gh pr create/edit --body-file で渡す）

デッキのループスライドと同じ grid:2x3 を Markdown 表で写す。セルの並び・見出し・
埋め文字の正本は ontology.yaml の deck.loop-slides（gen_deck.py と同じ宣言を読む）。

**画像ではなく表で描く。** private リポジトリでは PR 本文の画像が壊れる
（GitHub は本文中の画像を camo プロキシ経由で匿名取得するため、raw.githubusercontent の
private コンテンツに届かない）。表なら通知メール・モバイルアプリでも同じに見え、
diff にも残り、grep もできる。理由は CLAUDE.md の「PR 本文」節。
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_deck import ONT, ROOT, card_date, deck_name, parse, week_of  # noqa: E402

COLS = 3  # grid:2x3 の列数（上段 = 朝の ONY・下段 = 夕の検証）
REVIEW_NOTE = (
    "上段が朝の計画、下段が夕の検証です。とくに **O2（予測）と O（実測）のズレ** を見て、"
    "気づいたこと・別の見方をコメントしてください（詳しい文脈は不要です）。"
)


def cell(text: str) -> str:
    """カードの本文を表のセルに収める（改行 → <br>、| は縦棒として無効化）。"""
    return text.replace("|", "\\|").replace("\n", "<br>").strip() or ONT["deck"]["loop-slides"]["unverified-fill"]


def repo_url() -> str | None:
    """origin の https URL（末尾 .git を落とす）。git が無ければ None。"""
    try:
        url = subprocess.run(["git", "-C", str(ROOT), "config", "--get", "remote.origin.url"],
                             capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url[len("git@github.com:"):]
    return url[:-4] if url.endswith(".git") else url or None


def branch() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def slide_link(fm) -> str | None:
    """デッキの該当スライドへのリンク（画像ではなくリンク — private でも開ける）。"""
    url, br = repo_url(), branch()
    if not (url and br):
        return None
    y, w = week_of(card_date(fm))
    name = deck_name(fm["owner"], y, w)
    return f"[スライド]({url}/blob/{br}/wiki/{name}.md#{fm['id']})"


def loop_table(ofm, osec, yfm, ysec) -> list[str]:
    """1ループ = 見出し行 + 値行 を2段（= grid:2x3 の写し）。"""
    cells = ONT["deck"]["loop-slides"]["cells"]
    fill = ONT["deck"]["loop-slides"]["unverified-fill"]
    values = []
    for c in cells:
        src = osec if c["source"] == "ony" else (ysec or {})
        body = src.get(c["section"], "").strip() or fill
        if c.get("merge-yow") and ysec:
            done = ysec.get(c["merge-yow"], "").strip()
            if done and done != body:
                body = f"{body} → {done}"
        values.append(body)

    rows = []
    for i in range(0, len(cells), COLS):
        heads = [c["heading"] for c in cells[i:i + COLS]]
        vals = [cell(v) for v in values[i:i + COLS]]
        if i == 0:
            rows += ["| " + " | ".join(heads) + " |", "| " + " | ".join(["---"] * len(heads)) + " |"]
        else:
            rows.append("| " + " | ".join(f"**{h}**" for h in heads) + " |")
        rows.append("| " + " | ".join(vals) + " |")

    foot = [f"`{ofm['id']}`", ofm["activity"], "検証済" if yfm else "未検証（夕の /yow で埋まります）"]
    link = slide_link(ofm)
    if link:
        foot.append(link)
    return [f"## {ofm['title']}", ""] + rows + ["", " / ".join(foot)]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    day = dt.date.fromisoformat(args[0]) if args else dt.date.today()

    onys = {p.stem: parse(p) for p in sorted((ROOT / ONT["cards"]["ony"]["dir"]).glob("*.md"))}
    yows = {p.stem: parse(p) for p in sorted((ROOT / ONT["cards"]["yow"]["dir"]).glob("*.md"))}
    loops = [(fm, sec, *yows.get(cid, (None, None)))
             for cid, (fm, sec) in sorted(onys.items()) if card_date(fm) == day]
    if not loops:
        print(f"❌ {day} の ONY カードがない", file=sys.stderr)
        return 1

    done = sum(1 for t in loops if t[2])
    out = [f"{day} の ONY-YOW — {len(loops)} ループ（検証済 {done} / 未検証 {len(loops) - done}）", ""]
    for t in loops:
        out += loop_table(*t) + [""]
    out += ["---", "", REVIEW_NOTE]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

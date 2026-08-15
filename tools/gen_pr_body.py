#!/usr/bin/env python3
"""gen_pr_body — その日のループを PR 本文（A3 ライト = 1ループ1枚）に合成する。

実行:  uv run --with pyyaml --no-project python3 tools/gen_pr_body.py [YYYY-MM-DD] > /tmp/pr-body.md
出力:  標準出力に PR 本文の Markdown（gh pr create/edit --body-file で渡す）

本体は **スライド画像**（wiki/img/<ID>.svg を raw.githubusercontent の URL で貼る）。
同じ内容の表を「テキスト版」として下に残す — 画像を出さない通知メールや検索のため。

**push した後に実行する。** 画像 URL は HEAD のコミット SHA で固定するので、
その SHA が origin に載っていないと画像が出ない（マージ後もブランチ削除後も生き続ける）。

**画像をリンクで包まない・表を <details> で畳まない。** どちらも GitHub API 経由の
投稿では書き換えられる — リンク付き画像 `[![](img)](url)` はバッククォートで括られて
ただの文字列になり、<details>/<summary> はタグごと落ちる（2026-08-15 に PR #6 で観測）。
スライドへの導線は表の後に素のリンクで置く。
"""
import datetime as dt
import subprocess
import unicodedata
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_deck import ONT, ROOT, card_date, deck_name, loop_cells, parse, week_of  # noqa: E402

COLS = 3  # grid:2x3 の列数（上段 = 朝の ONY・下段 = 夕の検証）
REVIEW_NOTE = (
    "上段が朝の計画、下段が夕の検証です。とくに **O2（予測）と O（実測）のズレ** を見て、"
    "気づいたこと・別の見方をコメントしてください（詳しい文脈は不要です）。"
)


def git(*args) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True)
        return r.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_ok(*args) -> bool:
    """出力ではなく終了コードだけを見る（cat-file -e は成功時に何も出さない）。"""
    try:
        subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def slug(text: str) -> str:
    """GitHub が見出しから作るアンカー（github-slugger 相当）。
    小文字化 → 記号を落とす（日本語の文字・数字・ハイフンは残す）→ 空白を - に。"""
    kept = [c for c in text.strip().lower()
            if c.isalnum() or c.isspace() or unicodedata.category(c) in ("Mn", "Mc", "Pc", "Pd")]
    return "".join("-" if c.isspace() else c for c in kept)


def deck_anchor(deck: Path, card_id: str) -> str | None:
    """生成済みデッキ md を読み、そのループの見出しのアンカーを引く。
    `<!--id:...-->` は GitHub の blob 表示ではアンカーにならないため、見出し側から取る
    （重複見出しには GitHub と同じく -1, -2 が付くので、文書順に数える）。"""
    if not deck.exists():
        return None
    seen, current = {}, None
    for line in deck.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            s = slug(line.lstrip("#").strip())
            n = seen.get(s, 0)
            seen[s] = n + 1
            current = s if n == 0 else f"{s}-{n}"
        elif line.strip() == f"<!--id:{card_id}-->":
            return current
    return None


def origin() -> tuple[str, str] | None:
    """(owner, repo) — 画像 URL と スライド URL の組み立てに使う。"""
    url = git("config", "--get", "remote.origin.url")
    if not url:
        return None
    url = url.removesuffix(".git").replace("git@github.com:", "https://github.com/")
    parts = url.rstrip("/").split("/")
    return (parts[-2], parts[-1]) if len(parts) >= 2 else None


def pinned_sha() -> str | None:
    """HEAD の SHA。origin に載っていなければ警告する（画像が出ないため）。"""
    sha = git("rev-parse", "HEAD")
    if sha and not git("branch", "-r", "--contains", sha):
        print(f"⚠ {sha[:7]} がまだ origin に無い — 先に push してから実行する"
              "（画像 URL はこの SHA で固定される）", file=sys.stderr)
    return sha


def cell(text: str) -> str:
    """カードの本文を表のセルに収める（改行 → <br>、| は縦棒として無効化）。"""
    return text.replace("|", "\\|").replace("\n", "<br>").strip()


def loop_block(ofm, osec, yfm, ysec, repo, sha) -> list[str]:
    """1ループ = スライド画像 + テキスト版（同じ grid:2x3）。"""
    cells = loop_cells(osec, ysec)
    state = "検証済" if yfm else "未検証（夕の /yow で埋まります）"
    out = [f"## {ofm['title']}", ""]
    tail = []

    if repo and sha:
        owner, name = repo
        y, w = week_of(card_date(ofm))
        deck = f"wiki/{deck_name(ofm['owner'], y, w)}.md"
        svg = f"wiki/img/{ofm['id']}.svg"
        anchor = deck_anchor(ROOT / deck, ofm["id"])
        slide = (f"https://github.com/{owner}/{name}/blob/{sha}/{deck}"
                 + (f"#{anchor}" if anchor else ""))
        tail = [f"[スライドを見る]({slide})", ""]
        if not git_ok("cat-file", "-e", f"{sha}:{svg}"):
            print(f"⚠ {svg} が {sha[:7]} に無い — gen_deck.py を回してコミットしてから作り直す"
                  "（画像は貼らずに続ける）", file=sys.stderr)
        else:
            # 画像は素の ![]() で置く。リンクで包むと API 経由の投稿で
            # バッククォートに括られて文字列になる（module docstring を見よ）。
            img = f"https://raw.githubusercontent.com/{owner}/{name}/{sha}/{svg}"
            out += [f"![{ofm['title']}]({img})", ""]

    rows = []
    for i in range(0, len(cells), COLS):
        chunk = cells[i:i + COLS]
        if i == 0:
            rows += ["| " + " | ".join(h for h, _ in chunk) + " |",
                     "| " + " | ".join(["---"] * len(chunk)) + " |"]
        else:
            rows.append("| " + " | ".join(f"**{h}**" for h, _ in chunk) + " |")
        rows.append("| " + " | ".join(cell(b) for _, b in chunk) + " |")

    # 表は畳まない（<details> は API 経由の投稿でタグごと落ちる）
    return out + [f"テキスト版 — {ofm['id']} / {ofm['activity']} / {state}"
                  "（検索・通知メール用）", ""] + rows + [""] + tail


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

    repo, sha = origin(), pinned_sha()
    done = sum(1 for t in loops if t[2])
    out = [f"{day} の ONY-YOW — {len(loops)} ループ（検証済 {done} / 未検証 {len(loops) - done}）", ""]
    for t in loops:
        out += loop_block(*t, repo, sha)
    out += ["---", "", REVIEW_NOTE]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""gen_slide_svg — ループスライド（grid:2x3）を1枚の SVG に描く。

呼び出しは gen_deck.py（wiki/img/<ID>.svg として生成・鮮度検査・残骸削除まで面倒を見る）。
PR 本文はこの SVG を raw.githubusercontent の URL で貼る（tools/gen_pr_body.py）。

**PNG ではなく SVG。** テキストなので diff に残り grep でき、1枚 数 KB で済む。
文字は閲覧者の端末のフォントで描かれるので、生成環境に日本語フォントが無くても
豆腐にならない。GitHub は .svg を image/svg+xml で配信するため camo を通る。

高さは中身で決まる（最長セルに合わせて伸びる）。記録を画像側で切り詰めないため。
"""
import unicodedata
from html import escape

W = 1200                  # 幅は固定・高さは中身次第（短い日は 16:9 前後に収まる）
M = 32                    # 外周マージン
GRID_TOP, FOOT_H = 84, 52
GAP = 12
COLS, ROWS = 3, 2
PAD = 14                  # セル内側の余白
HEAD_FS, BODY_FS = 14, 15
MIN_BODY_LINES = 7        # これ未満でもセルは縮めない（スライドとしての見え方）
MAX_LINES = 24            # 異常に長い記録だけここで止める（テキスト版が PR 本文に付く）
FILL = "—"

BG, CELL_BG, BORDER = "#ffffff", "#f6f8fa", "#d0d7de"
INK, MUTED, FAINT = "#1f2328", "#656d76", "#8c959f"
ACCENT = ["#0969da", "#bc4c00"]   # 上段 = 朝の計画 / 下段 = 夕の検証
FONT = ("'Hiragino Sans','Hiragino Kaku Gothic ProN','Noto Sans JP','Yu Gothic',"
        "Meiryo,'IPAGothic','Droid Sans Japanese',sans-serif")
NO_HEAD = "、。，．）」』】〉》・…ー？！：；"   # 行頭に置かない（簡易禁則）

CELL_W = (W - 2 * M - (COLS - 1) * GAP) / COLS
INNER_W = CELL_W - 2 * PAD
LINE_H = round(BODY_FS * 1.55)
MAX_UNITS = int(INNER_W / (BODY_FS / 2))


def units(ch: str) -> int:
    """全角 = 2・半角 = 1 の幅単位（等幅近似。折り返し計算にだけ使う）。"""
    return 2 if unicodedata.east_asian_width(ch) in "FWA" else 1


def tokens(para: str) -> list[str]:
    """折り返しの最小単位。日本語は1文字ずつ、英数字の連なりは語のまま（wiki を wik/i で割らない）。"""
    out = []
    for ch in para:
        if units(ch) == 1 and not ch.isspace() and out and units(out[-1][-1]) == 1 \
                and not out[-1][-1].isspace():
            out[-1] += ch
        else:
            out.append(ch)
    return out


def wrap(text: str) -> list[str]:
    lines = []
    for para in text.split("\n"):
        cur, w, toks = "", 0, []
        for tok in tokens(para):
            while sum(units(c) for c in tok) > MAX_UNITS:   # 1行に収まらない語（URL 等）は割る
                toks.append(tok[:MAX_UNITS])
                tok = tok[MAX_UNITS:]
            toks.append(tok)
        for tok in toks:
            u = sum(units(c) for c in tok)
            if w + u > MAX_UNITS and cur and tok[0] not in NO_HEAD:
                lines.append(cur)
                cur, w = "", 0
                if tok.isspace():      # 行頭の空白は落とす
                    continue
            cur += tok
            w += u
        lines.append(cur)
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        lines[-1] = lines[-1][:-1] + "…"
    return lines


def render(fm, cells, verified: bool) -> str:
    """fm: ONY の frontmatter / cells: [(見出し, 本文)] を行優先で6件 / verified: 対の YOW の有無。"""
    wrapped = [wrap(body.strip() or FILL) for _, body in cells[:COLS * ROWS]]
    cell_h = PAD * 2 + HEAD_FS + 12 + max(MIN_BODY_LINES, max(map(len, wrapped))) * LINE_H
    height = round(GRID_TOP + ROWS * cell_h + (ROWS - 1) * GAP + FOOT_H)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" '
           f'viewBox="0 0 {W} {height}" font-family="{FONT}">',
           f'<rect width="{W}" height="{height}" fill="{BG}"/>',
           f'<text x="{M}" y="42" font-size="23" font-weight="bold" fill="{INK}">'
           f'{escape(str(fm["title"]))}</text>',
           f'<text x="{M}" y="66" font-size="13" fill="{MUTED}">'
           f'{fm["id"]} / {escape(str(fm["activity"]))} / '
           f'上段 = 朝の計画（O・N・Y） / 下段 = 夕の検証（O2・O 実測・W）</text>']

    for i, (heading, body) in enumerate(cells[:COLS * ROWS]):
        row, col = divmod(i, COLS)
        x = M + col * (CELL_W + GAP)
        y = GRID_TOP + row * (cell_h + GAP)
        out += [f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL_W:.1f}" height="{cell_h:.1f}" '
                f'rx="8" fill="{CELL_BG}" stroke="{BORDER}"/>',
                f'<text x="{x + PAD:.1f}" y="{y + PAD + HEAD_FS:.1f}" font-size="{HEAD_FS}" '
                f'font-weight="bold" fill="{ACCENT[row]}">{escape(heading)}</text>']
        color = FAINT if body.strip() in ("", FILL) else INK
        top = y + PAD + HEAD_FS + 12 + BODY_FS
        for j, line in enumerate(wrapped[i]):
            out.append(f'<text x="{x + PAD:.1f}" y="{top + j * LINE_H:.1f}" font-size="{BODY_FS}" '
                       f'fill="{color}">{escape(line)}</text>')

    out += [f'<text x="{M}" y="{height - 20}" font-size="13" fill="{MUTED}">'
            f'{"検証済" if verified else "未検証（夕の /yow で下段が埋まる）"}'
            f' / {escape(str(fm["owner"]))} / {escape(str(fm["date"]))}</text>',
            "</svg>"]
    return "\n".join(out) + "\n"

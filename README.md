# ony-yow-wiki

ONY-YOW — **O**:起きていること / **N**:望んでいること / **Y**:やってみること /
**O2**:起きそうなこと / **W**:分かったこと — を記録し、レビューして学ぶための LLM Wiki。

原典: 森雄哉『観察、仮説、実行、検証、計画、提案を一年で3000回トレーニングする方法 /
3000 Thinking Loops in 365 Days』(Scrum Fest Osaka 2026)。
読解資産は `origin/summary.md`（**ローカル専用** — 原典の詳細要約を含むため gitignore）。

## 仕組み

```
朝 /ony  → raw/ony/YYYYMMDD-NN.md   今日やることの根拠（即・単独コミット）
夕 /yow  → raw/yow/YYYYMMDD-NN.md   結果どうだったか（同じID・別コミット）
              │  記入タイミングが違うので別ファイル = 後知恵の構造的防止
              │  全カードが自動で wiki に載る（cards も wiki の一種）
              ▼
wiki/    ← gen_deck.py が生成（OKF バンドル・全て生成物）
   └ eiji-2026-w33.md     週1ファイル: 冒頭に週サマリー（今週の数字 / W カタログ / 未検証）
                          + 日々のループスライド（1ループ = grid:3x2 の1枚・日付順）
              │  /close-week: 週明けの stable 化差分 = 週締め PR。マージ = 週の確定
              ▼
PR コメント ← /onyw-review が3観点（バイアス / 因果の弱さ / 別の選択肢）でレビュー
```

- カードの型・つながり・引き算診断・合成規則の正本は [ontology.yaml](ontology.yaml)
- 機械的チェック: `tools/oylint.py`（カード検査）と `tools/gen_deck.py --check`（デッキ鮮度）
- 描画・リンク・バックリンクは [slide-wiki](https://github.com/iepyon/claude-skills) に委譲

## 使い方

```bash
# 記録（Claude Code 内）
/ony                  # 朝: 逆算で聞き出し → ドラフト PR → 計画レビューまで自動
/yow                  # 夕: 結果と教訓 → 同じ PR → ready + 検証レビューまで自動
                      #    残るはマージだけ（= 日の確定・本人）

# 週締めと手動レビュー
/close-week           # 前週デッキ確定の PR
/onyw-review 2        # 任意の PR に3観点コメント（朝夕は自動で走る）

# 機械的チェック
uv run --with pyyaml --no-project python3 tools/oylint.py --pending
uv run --with pyyaml --no-project python3 tools/gen_deck.py --check

# 閲覧
SW=~/src/claude-skills/slide-wiki/assets
npx --prefix $SW tsx $SW/src/cli.ts --wiki --site-title "ONY-YOW" wiki out/index.html && open out/index.html
```

規約の詳細は [CLAUDE.md](CLAUDE.md)。

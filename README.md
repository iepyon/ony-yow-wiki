# ony-yow-wiki

ONY-YOW — **O**:起きていること / **N**:望んでいること / **Y**:やってみること /
**O2**:起きそうなこと / **W**:分かったこと — を記録し、レビューして学ぶための LLM Wiki。

原典: 森雄哉『観察、仮説、実行、検証、計画、提案を一年で3000回トレーニングする方法 /
3000 Thinking Loops in 365 Days』(Scrum Fest Osaka 2026)。
読解資産は [origin/summary.md](origin/summary.md)。

## 仕組み

```
journal/  ─ 全件1行ログ（追記専用・数十秒〜2分/回）
   │  価値が分かったものだけ /promote
   ▼
wiki/     ─ OKF バンドル。1ループ = 1スライド（grid:3x2 の A3 相当1枚）
   │  昇格は PR。マージ = 確定
   ▼
PR コメント ─ /onyw-review が3観点（バイアス / 因果の弱さ / 別の選択肢）でレビュー
```

- 朝に ONY（計画）、夕に YOW（検証）— 原典 p160 の運用
- スライドの描画・リンク・バックリンクは [slide-wiki](https://github.com/iepyon/claude-skills) に委譲。
  このリポジトリに独自ツールは無い

## 使い方

```bash
# 記録（Claude Code 内）
/ony                 # 対話で O/N/Y/O2 を整えて journal に1行
/yow                 # 未検証の #NN を選んで Y/O/W を1行

# 昇格
/promote 2026-W33#03 # スライド生成 → lint → PR

# レビュー
/onyw-review 12      # PR #12 に3観点でコメント

# 閲覧
SW=/Users/eiji/src/claude-skills/slide-wiki/assets
npx tsx $SW/src/cli.ts --wiki --site-title "ONY-YOW" wiki out/index.html && open out/index.html
```

規約の詳細は [CLAUDE.md](CLAUDE.md)。

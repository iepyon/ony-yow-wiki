# ONY-YOW Wiki — 規約

ONY-YOW（O:起きていること / N:望んでいること / Y:やってみること / W:分かったこと）を
カードで記録し、スライドに合成し、レビューする LLM Wiki。AI はこのファイルの規約に従って振る舞う。

**このファイルには、ここにしか無い規約だけを書く。**
カードの型・語彙・つながり・引き算診断表・デッキ合成規則の正本は [ontology.yaml](ontology.yaml)。
Markdown・スライド・リンク・バンドル記法の正本は **slide-wiki**
（`~/src/claude-skills/slide-wiki`。無ければ `gh repo clone iepyon/claude-skills ~/src/claude-skills`）。
以下 `$SW` は `~/src/claude-skills/slide-wiki/assets` を指す。
ONY-YOW の定義の正本は [origin/summary.md](origin/summary.md)。**そちらの内容をここへ写さない。**
（**origin/ はローカル専用** — 原典スライドの詳細要約を含むため gitignore。リポジトリには載らない）

## 想定ユースケース（原典 p160）

**朝**、今日やることの根拠を ONY カードに書く。**夕方**、結果どうだったかを YOW カードに書く。
記入タイミングが違うので**別ファイル**。cards も wiki の一種 — **全カードが自動で wiki に載る**:
`gen_deck.py` が**週1ファイルのデッキ**に合成する。1日単位の記録（1ループ=1枚）が日付順に並び、
冒頭に**週サマリー**（今週の数字・W カタログ・未検証一覧）が付く。

## 3層アーキテクチャ（LLM-Wiki 準拠）

| 層 | 場所 | 編集権 |
|---|---|---|
| **Raw Sources**（生データ・不変層） | `raw/ony/` `raw/yow/`（カード = 一次記録）と `origin/`（原典読解・**ローカル専用/gitignore**） | 人間が `/ony` `/yow` または手書きで**追加**する。origin は変更しない。カードは**対の YOW ができたら ONY を凍結**（誤字修正・リンク追加は可。強制フックは無く、担保は git 履歴と `/onyw-review` の改変検査） |
| **The Wiki**（生成・保守層・OKF バンドル) | `wiki/` | **全て生成物**。デッキと `order.yaml` は `gen_deck.py`、`index.md` `log.md` は `gen-okf-index.ts`。手編集しない |
| **The Schema**（設定層） | `ontology.yaml` `CLAUDE.md` `templates/` `tools/` `.claude/skills/` | 人間が合意の上で変更する |

## カード

- ファイル名 = `id` = `YYYYMMDD-NN`（日付 + **日内連番**ゼロ詰め2桁）。ONY と対の YOW は**同じ ID**
- frontmatter・節見出しは `templates/{ony,yow}.md` から作る（節構成の正本は ontology.yaml）
- **節見出しは必須（構造）・中身は自由（規律を課さない）**。空の組合せは引き算診断が
  名前を返すだけで、記録は止めない（p152）
- 現在時刻は `date +%Y-%m-%dT%H:%M`、ISO 週は `date +%G-W%V`（暗算しない）
- **ONY カードを書いたらカードごとに単独コミット**。YOW は別コミット
  — コミットの分離が「予測を結果より先に書いた」ことの証明（日次 PR の push で
  GitHub のタイムスタンプにも残る）
- YOW を書くとき **ONY カードを開かない・書き換えない**（O2 の凍結はファイル分離が担保）

## 機械的チェック

```bash
uv run --with pyyaml --no-project python3 tools/oylint.py            # カード検査（--pending で未検証一覧）
uv run --with pyyaml --no-project python3 tools/gen_deck.py          # デッキ合成（--check で鮮度検査）
npx --prefix $SW tsx $SW/src/cli.ts --lint wiki/<デッキ>.md --strict  # スライド構造検査
# SW=~/src/claude-skills/slide-wiki/assets
```

oylint が見るもの: id=ファイル名 / 必須フィールド・語彙 / 必須節 / **yow→ony の参照存在と同 ID 規則** /
relates の参照存在 / 引き算診断（info）。error があれば exit 1。

## デッキ（生成物）

- **週デッキ** `eiji-2026-w33.md`（週単位でファイル化）= 冒頭に週サマリー
  （今週の数字 Table・W カタログ・未検証一覧、各項目から該当スライドへ内部リンク）、
  続けて日々のループスライド（1ループ = `grid:3x2` の1枚・日付順）。
  構成・セル並び・埋め文字「—」・Y 併記の正本は ontology.yaml の `deck` 節
- ファイル名は**全て小文字**（GitHub の raw 閲覧はケースセンシティブ）
- `status` は gen_deck が機械的に決める（過去 = `stable`、当日/現在週 = `draft`）
- 昇格フラグは無い — **全カードが自動掲載**される

## ワークフロー

| やりたいこと | 手段 |
|---|---|
| 朝: 今日やることを話す | `/ony` → **Y から逆算**して O/N/O2 を聞き出し、カード作成 → `day/<日付>` ブランチ → **ドラフト PR → `/onyw-review` 自動実行（計画レビュー）** |
| 夕: 結果と教訓を話す | `/yow` → 今朝の Y 一覧から O（結果）と W（教訓）を聞き出し、同じ PR に積む → **ready 化 → `/onyw-review` まで自動実行** |
| 日を確定する | 本人がマージ（**マージ = 日の確定**。ready 化とレビューは /yow が済ませている） |
| 週を締める | `/close-week` → 前週デッキの stable 化差分を PR に（日次 PR がマージ済み前提） |
| PR にレビューコメント | `/onyw-review <PR番号>`（日次・週締めどちらの PR にも。バイアス / 因果の弱さ / 別の選択肢） |
| 一覧・バックリンクを見る | `npx --prefix $SW tsx $SW/src/cli.ts --wiki wiki out/index.html` |

**1日 = 1ドラフト PR。** 朝 `/ony` が開き、夕 `/yow` が積み、本人のマージで日が確定する。
レビューの往復は PR コメントに残す（A3 のキャッチボール）。

## W に規律を課さない

W（分かったこと）は自由記述。falsifier・確信度・証拠の階梯を要求しない（原典忠実の決定）。
レビューで因果の弱さを**問う**ことはするが、記入を **block しない**。

## 記述言語

すべて日本語。要素キー（O/N/Y/O2/W）・ID・frontmatter キーは原文のまま。

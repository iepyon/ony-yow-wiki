# ONY-YOW Wiki — 規約

ONY-YOW（O:起きていること / N:望んでいること / Y:やってみること / W:分かったこと）を
カードで記録し、スライドに合成し、レビューする LLM Wiki。AI はこのファイルの規約に従って振る舞う。

**このファイルには、ここにしか無い規約だけを書く。**
守れているかは `tools/doclint.py` が見る（人間にも AI にも守れなかったため — 20260816-01）。

### 正本の所在

| 何の | 正本 | 他の場所での扱い |
|---|---|---|
| カードの型・語彙・つながり・引き算診断表・デッキ合成規則 | [ontology.yaml](ontology.yaml) | 参照だけ。`templates/` は doclint が整合を検査する |
| ONY-YOW の定義（原典の読解） | [origin/summary.md](origin/summary.md) | **写さない**（ローカル専用/gitignore） |
| Markdown・スライド・リンク・バンドル記法 | **slide-wiki** | 参照だけ |
| PR 本文・デッキの見た目と作り方 | `tools/gen_*.py` | CLAUDE.md は**理由**だけ書き、手順はコマンド名で指す |
| 対話の手順（何をどの順で聞くか） | `.claude/skills/*/SKILL.md` | CLAUDE.md はワークフロー表で入口だけ示す |
| 記録の運用規約（コミット単位・PR の単位・層の編集権） | **このファイル** | SKILL.md は理由を写さず、手順だけ書く |

slide-wiki の入手は `~/src/claude-skills/slide-wiki`。無ければ
`gh repo clone iepyon/claude-skills ~/src/claude-skills` →
**続けて `npm install --prefix ~/src/claude-skills/slide-wiki/assets`**
（クローンだけでは依存が入らず CLI が `effect` 未解決で落ちる）。
以下 `$SW` は `~/src/claude-skills/slide-wiki/assets` を指す。

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
uv run --with pyyaml --no-project python3 tools/doclint.py           # 規約の写しのずれを検査
uv run --with pyyaml --no-project python3 tools/gen_deck.py          # デッキ合成（--check で鮮度検査）
uv run --with pyyaml --no-project python3 tools/gen_pr_body.py       # PR 本文（A3 ライト）を標準出力へ
npx --prefix $SW tsx $SW/src/cli.ts --lint wiki/<デッキ>.md --strict  # スライド構造検査
# SW=~/src/claude-skills/slide-wiki/assets
```

oylint が見るもの: id=ファイル名 / 必須フィールド・語彙 / 必須節 / **yow→ony の参照存在と同 ID 規則** /
relates の参照存在 / 引き算診断（info）。error があれば exit 1。

doclint が見るもの: `templates/` が ontology.yaml の宣言からずれていないか（**宣言に無いキーは
廃止された規約の残骸** — コメントアウトも見る）/ ドキュメントのコマンド行が実在するツールを
指しているか。規約を2箇所目に書いても機械は気づけないので、**写しやすい2箇所だけを見張る**。

## デッキ（生成物）

- **週デッキ** `eiji-2026-w33.md`（週単位でファイル化）= 冒頭に週サマリー
  （今週の数字 Table・W カタログ・未検証一覧、各項目から該当スライドへ内部リンク）、
  続けて日々のループスライド（1ループ = `grid:2x3` の1枚・日付順）。
  構成・セル並び・埋め文字「—」・Y 併記の正本は ontology.yaml の `deck` 節
- ファイル名の規則（小文字）・`status` の決め方・**昇格フラグが無いこと**の正本は
  ontology.yaml の `deck` 節。ここには写さない
- デッキ本文と PR 本文はどちらも `loop_cells()` を源にする（写しがズレない）

## ワークフロー

| やりたいこと | 手段 |
|---|---|
| 朝: 今日やることを話す | `/ony` → **Y から逆算**して O/N/O2 を聞き出し、カード作成 → `day/<日付>` ブランチ → **ドラフト PR → `/onyw-review` 自動実行（計画レビュー）** |
| 夕: 結果と教訓を話す | `/yow` → 今朝の Y 一覧から O（結果）と W（教訓）を聞き出し、同じ PR に積む → **ready 化 → `/onyw-review` まで自動実行** |
| 日を確定する | 本人がマージ（**マージ = 日の確定**。ready 化とレビューは /yow が済ませている） |
| 週を締める | `/close-week` → 前週デッキの stable 化差分を PR に（日次 PR がマージ済み前提） |
| PR にレビューコメント | `/onyw-review <PR番号>` — **朝夕の /ony /yow が自動実行**する。手動でも可（週締め PR など） |
| 一覧・バックリンクを見る | `npx --prefix $SW tsx $SW/src/cli.ts --wiki wiki out/index.html` |

**1日 = 1ドラフト PR。** 朝 `/ony` が開き、夕 `/yow` が積み、本人のマージで日が確定する。
レビューの往復は PR コメントに残す（A3 のキャッチボール）。

## PR 本文 = A3 ライト（1ループ1枚）

PR 本文は `tools/gen_pr_body.py` の**生成物**（手書きしない）。デッキのループスライドと同じ
`grid:2x3` を Markdown 表で写す — 上段が朝の計画（O/N/Y）、下段が夕の検証（O2/O実測/W）。
diff を追わなくても**一枚で判る**ようにするのが目的（トヨタの A3 一枚もの — 事情を知らない人でも
初期レベルの助言ができる状態にする）。文末に「O2 と O のズレを見てほしい」の1行を添える。

**本体は表そのもの。画像は貼らない**（2026-08-15 の判断）。スライド画像（SVG）を貼る実装を
一度入れたが、表だけで一枚ぶんの情報は足りていた。画像は通知メールでも GitHub 検索でも
読めないぶん不利で、public 依存（camo）・SHA 固定・生成物の管理という制約だけが残る。
**画像をやめると public/private の制約も消える**（20260814-04 の W の続き）。
実装は git 履歴にある（`tools/gen_slide_svg.py`）。

**投稿の作法**（`<details>` で畳まない・URL を SHA で固定する・したがって
`push → 本文生成 → PR 作成/更新` の順）**の正本は `tools/gen_pr_body.py` の docstring**。
ここには写さない — 写した結果が古くなったのが 20260816-01 の O。

**日次 PR に載せるのは記録だけ**（`raw/` のカードと `wiki/` の再生成）。
スキーマ変更（CLAUDE.md・ontology.yaml・templates・tools・skills）は **main 直コミット**とし、
day ブランチへは merge で同期する — 日次 PR の diff を記録の検証だけに保つため
（2026-08-14 の W「ツール修正と記録が同じ流れで起きると PR に混ざる」から）。

## W に規律を課さない

W（分かったこと）は自由記述。falsifier・確信度・証拠の階梯を要求しない（原典忠実の決定）。
レビューで因果の弱さを**問う**ことはするが、記入を **block しない**。

## 記述言語

すべて日本語。要素キー（O/N/Y/O2/W）・ID・frontmatter キーは原文のまま。

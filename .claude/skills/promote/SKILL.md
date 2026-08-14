---
name: promote
description: journal の ONY-YOW 対（例 2026-W33#03）を wiki のスライド1枚（grid:3x2）へ昇格し、lint を通して PR を作る。昇格=PR、マージ=確定。「昇格して」「/promote 2026-W33#03」で起動。
---

# /promote — journal 行をスライドへ昇格して PR を作る

共通規約は [CLAUDE.md](../../../CLAUDE.md)（スライドの形・セルの行優先・ID 規約・週の定義）。
slide-wiki の記法の正本は `/Users/eiji/src/claude-skills/slide-wiki/SKILL.md`。

引数: `<年>-W<週>#<NN>`（例 `2026-W33#03`）。省略されたら今週の journal から
yow 済みの対を列挙して選ばせる。

## 手順

1. **journal から対を読む** — `journal/eiji-<年>-W<週>.md` の `#NN` の ony 行と yow 行。
   yow 行が無い場合は「未検証のまま昇格しますか」と確認し、右列の O(実測)・W は `—` で埋める。
2. **ブランチ** — `git switch -c promote/<YYYYMMDD>-<NN>`（日付は **ony 行の日付**）。
3. **デッキを用意** — `wiki/eiji-<年>-w<週>.md` が無ければ CLAUDE.md の frontmatter 例から作り、
   `wiki/order.yaml` の該当月グループ（**週の月曜が属する月**）に追記する。
4. **スライドを追記** — 以下の形。**記述順は行優先（O → O2 → N → W → Y → O実測）**。
   見た目の読み順（左列 O→N→Y）と違うことに注意。手で並べ替えない。

   ```markdown
   ---

   ## <タイトル: ONY の要約を一文で>
   <!--grid:3x2-->
   <!--id:<YYYYMMDD>-<NN>-->
   ### O 起きていること
   <ony 行の O>
   ### O2 起きそうなこと
   <ony 行の O2。無ければ —>
   ### N 望んでいること
   <ony 行の N>
   ### W 分かったこと
   <yow 行の W>
   ### Y やってみること
   <ony 行の Y（yow の Y と違えば「→」で併記）>
   ### O 起きたこと
   <yow 行の O>
   ```

   - **スライド ID = `<YYYYMMDD>-<NN>`**（journal の `#NN` と一致。`/onyw-review` の
     後知恵検査がこの対応に依存する）
   - 各セルは journal 行を膨らませてよいが、**O2 は journal の逐語のまま**（予測の凍結）
   - 関連する既存スライドがあれば本文かタイトル行に
     `[ラベル](eiji-<年>-w<週>.md#<ID>)` 形式で内部リンク（先頭に `/` `./` を付けない）
5. **検査と生成** —
   ```bash
   SW=/Users/eiji/src/claude-skills/slide-wiki/assets
   npx --prefix $SW tsx $SW/src/cli.ts --lint wiki/eiji-<年>-w<週>.md --strict
   npx --prefix $SW tsx $SW/src/tools/gen-okf-index.ts wiki
   ```
   lint が通らなければ直してから進む。`wiki/index.md` `wiki/log.md`（バンドル更新履歴）も
   ステージする。
6. **PR** —
   ```bash
   git add wiki/ && git commit
   git push -u origin promote/<YYYYMMDD>-<NN>
   gh pr create --title "<ID> <タイトル>" --body "<ONY-YOW の要約と journal 行の逐語>"
   ```
   body には **journal の2行を逐語で貼る**（レビュアが元行と突き合わせられるように）。
7. **締め** — PR の URL を見せ、「`/onyw-review <番号>` でレビューできます」と1行添える。

## してはいけないこと

- journal の編集（読むだけ）
- O2 の言い換え（凍結）
- 複数の `#NN` を1つの PR に混ぜる（昇格1件 = PR 1件）

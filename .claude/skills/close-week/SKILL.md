---
name: close-week
description: 週締め。前週デッキが stable 化する再生成差分を PR にし、レビューの場を作る。マージ = 週の確定。「週を締めて」「/close-week」で起動。
---

# /close-week — 週を締めて週デッキ確定の PR を作る

共通規約は [CLAUDE.md](../../../CLAUDE.md)。全カードは週デッキに自動掲載されるので、
「1ループ昇格」は存在しない。**レビューの単位は週** — デッキの stable 化差分が PR になり、
そこに `/onyw-review` が付く（A3 のキャッチボール）。

## 手順

0. **前提チェック**: `git status --porcelain` が空（カード・生成物ともコミット済み）、
   現在ブランチが main、`date +%G-W%V` で前週が確定していること（週の途中で締めない。
   途中で締めたいと言われたら「未検証 N 件が締めに含まれます」と伝えて確認）。
1. **ブランチ** — `git switch -c close/<年>-w<週>`（締める週。例 `close/2026-w33`）。
2. **再生成** — `uv run --with pyyaml --no-project python3 tools/gen_deck.py`
   （前週デッキの `status` が `stable` に変わる。差分ゼロなら締め済み — 止める）。
   続けて oylint / slide-wiki `--lint --strict` / `gen-okf-index.ts wiki` を通す。
3. **PR**:
   ```bash
   git add wiki/ && git commit -m "close: <年>-W<週> サマリー確定"
   git push -u origin close/<年>-w<週>
   gh pr create --title "<年>-W<週> 週締め" --body "<今週の数字と W カタログを逐語で>"
   ```
4. **締め** — PR の URL を見せ、「`/onyw-review <番号>` で週レビューできます」と1行添える。
   マージは本人が決める（マージ = 週の確定）。

## してはいけないこと

- デッキ md の手修正（生成物。直すならカードを直して再生成）
- 複数週を1つの PR に混ぜる

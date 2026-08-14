---
name: yow
description: 夕方、結果どうだったかを YOW カード（Y:やったこと / O:起きたこと / W:分かったこと）として raw/yow/ に作る。未検証の ONY カードを一覧提示して選ばせ、予測 O2 と実測 O を突き合わせて W を促す。「YOWを記録」「振り返る」「/yow」で起動。
---

# /yow — 夕方の YOW カードを作る

共通規約は [CLAUDE.md](../../../CLAUDE.md)、型の正本は [ontology.yaml](../../../ontology.yaml)。

## 手順

1. **未検証の ONY を出す** — `uv run --with pyyaml --no-project python3 tools/oylint.py --pending`
   の一覧を見せ、ユーザーが ID で選ぶ。該当が無ければ、単発の記録として
   新しい ONY カードを最小で作ってから対の YOW を書く（ID は共有）。
2. **予測を逐語で提示** — 選ばれた ONY カードの **O2 節をそのまま**見せる。
   O2 が空なら「予測なしの検証になります（突き合わせはできません）」と1行伝えて進む。
   **ONY カードは開いて読むだけ。書き換えない**（凍結はファイル分離が担保）。
3. **聞く** — Y（やったこと）/ O（起きたこと）/ W（分かったこと）。
   - O2 と O の一致・不一致は**ユーザー自身に言わせる**（こちらが判定しない）
   - W は自由記述。ただし食い違ったのに W が事前の見立てのままなら
     「食い違いは W に反映しなくていいですか」と**1回だけ**聞く
4. **カード作成** — `templates/yow.md` から `raw/yow/<同じID>.md` を作る
   （frontmatter の `ony:` は自分の ID と同じ — ontology の same-id 規則）。
5. **lint とデッキ再生成** — oylint（error は直す）→
   `uv run --with pyyaml --no-project python3 tools/gen_deck.py`
   （週デッキのループスライド右列と W カタログに反映される）。
6. **別コミット**:
   ```bash
   git add raw/yow/<ID>.md wiki/ && git commit -m "yow: <ID>"
   ```
7. **締め** — 週デッキ上の完成したスライド（予測 O2 と実測 O が並ぶ1枚）を見せる。

## してはいけないこと

- **ONY カードの編集**（読むだけ。O2 の言い換え・要約もしない）
- O2 と O の一致判定の代行
- W の質への駄目出し・falsifier の要求

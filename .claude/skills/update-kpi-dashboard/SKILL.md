---
name: update-kpi-dashboard
description: 08同窓会のKPIダッシュボード（claude.ai の Dashboard アーティファクト）を更新する。「GA更新して」「ダッシュボード更新」「KPI更新」「目標を変えて」「費用を変えて」などで使う。GAの数字を画面から取り直して反映する手順と、目標・費用など設定値の変え方をまとめている。
---

# 08同窓会 KPIダッシュボードの更新

ダッシュボード: https://claude.ai/artifact/4iNkBxvyZpt9G9vBsKjMUC （Dashboard 型のアーティファクト）

中身はすべてダッシュボードのストアのドキュメントで、`ArtifactData` ツールで読み書きする。`file_path` で Artifact を publish し直してはいけない（型のファイルを壊す）。書く前に必ず `get` して、返ってきた `version` を `if_version` に渡す。

## データの出どころ

| dataset id | 中身 | 更新のしかた |
|---|---|---|
| `responses` | 参加申込フォームの回答シート（Google Drive コネクタ `read_file_content`、fileId `1H_9JpNPDs7EvstUu1gX36JenQ4BPp6DQfSui9QxVuvk`） | ライブ。開くたびに読み直すので作業不要 |
| `ga` | GAのイベント別の回数とUU（ファネル・ボタン注記に使用） | GA画面から転記した JSON ファイル |
| `ga_daily` | GAの日別UU・新規UU・PV（日別の動きグラフに使用） | GA画面から転記した JSON ファイル |

計算（`dash.calc`）: `summary`（人数・会費・目標まで）、`daily`（日別累計）、`funnel`（ファネル）。ページは `files/index.html`。

## GAの数字を更新する（「GA更新して」）

GAはコネクタが無いので、内蔵ブラウザ（`mcp__Claude_Browser__*`）で読む。パスワードは入力しない。ログイン画面が出たらユーザーにログインを頼んで待つ。

1. イベントレポートを開く:
   `https://analytics.google.com/analytics/web/#/a413622384p560984590/reports/explorer?r=top-events`
   期間は右上の「過去28日間」など。期間をメモしておく（ファネルの説明文に書く）。
2. **イベント別（`ga`）**: 表の行を JavaScript で読む。
   ```js
   [...document.querySelectorAll('table tr, [role=row]')].map(r=>r.innerText.replace(/\s+/g,' ').trim())
   ```
   `page_view` `scroll` `click_form` `click_line` `click_map` `click_calendar` など各行の「イベント数」と「総ユーザー数」を取り、
   `[{"event":"page_view","count":502,"users":316}, …]` の形で JSON にする。
3. **日別（`ga_daily`）**: 表の「イベント名」見出しの横の「+」→ 検索に「日付」→「日付」を選ぶと、イベント名×日付の表になる（ビューポートが狭いと押しにくいので `resize_window` 1400x900 にしてから。終わったら `preset: desktop` に戻す）。表の検索欄に `page_view` を入れて日別の「総ユーザー数」（users）と「イベント数」（views）を、`first_visit` を入れて日別の「総ユーザー数」（new_users）を読む。
   `[{"date":"2026-10-27","users":20,"new_users":20,"views":50}, …]` の形にする。日付は `YYYY-MM-DD`。
   近道: 絞り込みと日付の追加はURLでもできる（`FILTER` を `page_view` や `first_visit` にして開くだけ）:
   `https://analytics.google.com/analytics/web/#/a413622384p560984590/reports/explorer?r=top-events&params=_r.explorerCard..filterTerm%3DFILTER%26_r.explorerCard..startRow%3D0%26_r.explorerCard..seldim%3D%5B%22eventName%22,%22date%22%5D`
   イベント別の表は1ページ10行なので、`click_` で絞り込んで `click_form_top`（ご挨拶の直後のボタン）も漏れなく取る。ファネルの「参加フォームを押した」は `click_form` と `click_form_top` のユーザー数の合計。
4. JSON をスクラッチパッドに保存し、`Artifact` の `asset: true` でダッシュボードに upload する（`url` にダッシュボードのURL）。返ってきた `/_blob/<id>` を使う。
5. `ArtifactData` `update` で `datasets/ga` と `datasets/ga_daily` の `source`（`{kind:"file", url, name}`）と `updated`（`{at: ISO時刻, by: "Claude（GA画面から転記）"}`）を書き換える。
6. ファネルの説明文の期間を直す（`files/index.html` の `text` を `str_replace`）:
   `Google アナリティクス 10月7日〜11月3日の記録` の日付部分。
7. 続けて、下の「共有用スナップショットとPDFを作り直す」で共有用スナップショットも作り直す（「ダッシュボード更新して」と言われたら、ここまでを1セットでやる）。PDFは頼まれたときだけ。

## 設定値を変える

`files/index.html` の `text` を `str_replace` で直す。同じ値が2か所にあるものは両方直す。

- **目標人数**（いま130）: `GOAL: 130,`（`window.K`）と、`summary` 計算の `to_goal: Math.max(0, 130 - …)`。
- **費用**（いま3,000,000円）: `COST: 3000000,`（`window.K`）と、`summary` 計算の `const COST = 3000000;`。
- **会費**: `summary` 計算の 24000 / 19000（事前振込）と 25000 / 20000（当日）。
- **締切・募集開始**: `DEADLINE: '2026-12-31'`、`START: '2026-11-01'`、グラフの始まり `AXIS_START: '2026-10-17'`。

ページは「one-writer」形式（先頭に `<meta name="dash-one-writer">`）。文言は HTML に直接書き、データで変わる数字だけ `data-draw` のドローイングで出す。数字を HTML に直書きしない。

## 共有用スナップショットとPDFを作り直す（「スナップショット更新して」「PDFにして」）

ダッシュボード本体は、見る人それぞれに Claude のアカウントと Google ドライブの接続が要る。誰でも見られるように、数字を埋め込んだ共有用HTMLを別のアーティファクトにしてある。

共有用スナップショット: https://claude.ai/artifact/6nWYtxfXwn5qUhohaTmdre （ふつうのHTMLのアーティファクト。「リンクを知っている全員」に公開されていて、差し替えると開いている人の画面もすぐ変わる。だから名前・メール・メッセージなど個人の情報は絶対に入れない）

Dashboard 型にはPDF出力が無く、ページから印刷も呼べない。PDFは同じHTMLを手元の Chrome で印刷して作る。

1. 材料をスクラッチパッドの作業フォルダにそろえる。
   - `page.html`: `ArtifactData` `get` で `files/index.html` を `out_dir` 付きで取り、その JSON の `text` を保存する。
   - `responses.json`: Google Drive `read_file_content`（上の fileId）で回答を読み、1回答1行の `[{"date":"YYYY-MM-DD","status":"参加","companions":0,"children":0,"payment":"事前振込"}, …]` にする。`payment` は「事前振込」「当日払い」「未定」のどれか。**名前・メール・メッセージは入れない。**
   - `ga.json` と `ga_daily.json`: 最新のGA転記ファイル（GAも更新するなら先に上の手順で取り直す）。
2. 組み立てる（スクリプトはこのスキルのフォルダにある）:
   ```bash
   python3 -I .claude/skills/update-kpi-dashboard/build_snapshot.py --page WORK/page.html --responses WORK/responses.json --ga WORK/ga.json --ga-daily WORK/ga_daily.json --label "2026年◯月◯日時点のスナップショット（フォーム回答は◯/◯、Google アナリティクスは◯/◯までの数字）" --out-dir WORK
   ```
   `WORK/kpi-snapshot.html`（共有用）と `WORK/export.html`（PDF用）ができる。
3. 共有用HTML: `Artifact` で `file_path` に `WORK/kpi-snapshot.html`、`url` に上の共有用スナップショットのURLを渡して publish する（URLを変えないため。別の会話からなら先に `action: "read"` が要る）。
4. PDF:
   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer --window-size=1120,1600 --virtual-time-budget=15000 --print-to-pdf="WORK/08同窓会KPI_YYYY-MM-DD.pdf" "file://WORK/export.html"
   ```
   確認したいときは同じコマンドを `--screenshot="WORK/preview.png"` にして画像を見る。できたPDFは `SendUserFile` で渡す。

## 書いたあとの確認

`ArtifactData` `get` で `data/users/me` の `check` を読む。`checking` なら読み直す（5回まで）。ドキュメントが無ければ問題なし。`failed` なら `page` の内容を見て直す。レンダリングやスクリーンショットでの確認はしない。

最後にユーザーへ、何を更新したか（GAの期間、主な数字の変化）を短く伝える。

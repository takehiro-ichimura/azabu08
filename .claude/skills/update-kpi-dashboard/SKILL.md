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
4. JSON をスクラッチパッドに保存し、`Artifact` の `asset: true` でダッシュボードに upload する（`url` にダッシュボードのURL）。返ってきた `/_blob/<id>` を使う。
5. `ArtifactData` `update` で `datasets/ga` と `datasets/ga_daily` の `source`（`{kind:"file", url, name}`）と `updated`（`{at: ISO時刻, by: "Claude（GA画面から転記）"}`）を書き換える。
6. ファネルの説明文の期間を直す（`files/index.html` の `text` を `str_replace`）:
   `Google アナリティクス 10月6日〜11月2日の記録` の日付部分。

## 設定値を変える

`files/index.html` の `text` を `str_replace` で直す。同じ値が2か所にあるものは両方直す。

- **目標人数**（いま130）: `GOAL: 130,`（`window.K`）と、`summary` 計算の `to_goal: Math.max(0, 130 - …)`。
- **費用**（いま3,000,000円）: `COST: 3000000,`（`window.K`）と、`summary` 計算の `const COST = 3000000;`。
- **会費**: `summary` 計算の 24000 / 19000（事前振込）と 25000 / 20000（当日）。
- **締切・募集開始**: `DEADLINE: '2026-12-31'`、`START: '2026-11-01'`、グラフの始まり `AXIS_START: '2026-10-17'`。

ページは「one-writer」形式（先頭に `<meta name="dash-one-writer">`）。文言は HTML に直接書き、データで変わる数字だけ `data-draw` のドローイングで出す。数字を HTML に直書きしない。

## 書いたあとの確認

`ArtifactData` `get` で `data/users/me` の `check` を読む。`checking` なら読み直す（5回まで）。ドキュメントが無ければ問題なし。`failed` なら `page` の内容を見て直す。レンダリングやスクリーンショットでの確認はしない。

最後にユーザーへ、何を更新したか（GAの期間、主な数字の変化）を短く伝える。

"""ダッシュボードのページとデータから、共有用HTMLとPDF用HTMLを組み立てる。

使い方:
  python3 -I build_snapshot.py --page page.html --responses responses.json \
      --ga ga.json --ga-daily ga_daily.json --label "2026年11月3日時点…" --as-of 2026-11-03 --out-dir OUT

page.html      ダッシュボードの files/index.html の text をそのまま保存したもの
responses.json 回答を [{date, status, companions, children, payment}, …] にしたもの（名前・メールは入れない）
出力:          OUT/kpi-snapshot.html（アーティファクト用） と OUT/export.html（PDF用）
"""
import argparse
import json
import os

ROOT_TOKENS = """:root{ --font-anthropic-sans:"Noto Sans JP","Hiragino Sans",sans-serif; --font-anthropic-serif:"Noto Serif JP","Hiragino Mincho ProN",serif;
 --cds-font-size-caption:12px; --cds-font-size-body:14px; --cds-font-size-heading:17px; --cds-font-size-title:26px; --cds-font-weight-medium:500;
 --cds-gap-xs:4px; --cds-gap-sm:8px; --cds-gap-md:14px; --cds-gap-lg:22px; --cds-pad-xs:4px; --cds-pad-sm:8px; --cds-pad-lg:18px;
 --cds-radius:8px; --cds-shadow-popover:none; --cds-dur-slow:.3s; }"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600&family=Noto+Serif+JP:wght@400&display=swap" rel="stylesheet">')

D3 = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'

# dash の最小限の代わり。データは埋め込み、calc はその場で計算し、draw は読み込み後にまとめて実行する。
STUB = """<script>
window.__DATA = %s;
// スナップショットの日付を「今日」として扱う（後で開いても、見込みや必要ペースがその日のまま）
(function(){ const fixed = %d; Date.now = () => fixed; })();
(function(){
  const calcs = {}, draws = [], cbs = [];
  const D = window.__DATA;
  window.dash = {
    colors: ['#7a2e2e','#9a8f55','#5b7083','#8a6d9e','#4f7d6a','#b0703c','#6b6560','#a3352b'],
    loader(){}, setLink(){}, refresh(){}, params(){ return {}; }, setParams(){}, resetParams(){},
    calc(id, o){ calcs[id] = o; },
    data(id){
      if (D[id]) return { status: 'ok', data: D[id], meta: [] };
      if (calcs[id]) { const o = calcs[id]; return { status: 'ok', data: o.fn(...o.inputs.map((i) => dash.data(i).data)), meta: [] }; }
      return { status: 'missing', data: [] };
    },
    onData(fn){ cbs.push(fn); },
    draw(name, fn){ draws.push([name, fn]); },
  };
  window.__run = () => {
    cbs.forEach((f) => f());
    draws.forEach(([n, f]) => document.querySelectorAll('[data-draw="' + n + '"]').forEach((el) => f(el)));
    document.querySelectorAll('details').forEach((d) => { d.open = true; });
  };
})();
</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', required=True)
    ap.add_argument('--responses', required=True)
    ap.add_argument('--ga', required=True)
    ap.add_argument('--ga-daily', required=True)
    ap.add_argument('--label', required=True, help='タイトル下に出す「◯月◯日時点」の一文')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--as-of', required=True, help='スナップショットの日付 YYYY-MM-DD（日本時間のその日の正午として扱う）')
    a = ap.parse_args()

    page = open(a.page, encoding='utf-8').read()
    page = page.replace('<h1>08同窓会 KPI</h1>',
                        '<h1>08同窓会 KPI</h1>\n    <p class="k-stamp">%s</p>' % a.label, 1)
    data = {
        'responses': json.load(open(a.responses, encoding='utf-8')),
        'ga': json.load(open(a.ga, encoding='utf-8')),
        'ga_daily': json.load(open(a.ga_daily, encoding='utf-8')),
    }
    import datetime
    as_of = datetime.datetime.fromisoformat(a.as_of + 'T12:00:00+09:00')
    stub = STUB % (json.dumps(data, ensure_ascii=False), int(as_of.timestamp() * 1000))
    stamp_css = '.k-head .k-stamp{font-size:12px;color:#6b6560;margin:0}'
    os.makedirs(a.out_dir, exist_ok=True)

    snapshot = '\n'.join([
        '<title>08同窓会 KPI</title>',
        '<meta name="claude:viewport-fit-sides" content="cover">',
        FONTS,
        '<style>', ROOT_TOKENS,
        'body{margin:0;background:#faf8f4;color:#1f1d1a}',
        '.k-page{padding-left:max(16px, env(safe-area-inset-left, 0px))!important;padding-right:max(16px, env(safe-area-inset-right, 0px))!important}',
        stamp_css, '</style>', D3, stub,
        '<div id="dash-root">', page, '</div>',
        "<script>document.fonts.ready.then(()=>window.__run()); let __t; addEventListener('resize',()=>{clearTimeout(__t);__t=setTimeout(()=>window.__run(),150);});</script>",
    ])
    open(os.path.join(a.out_dir, 'kpi-snapshot.html'), 'w', encoding='utf-8').write(snapshot)

    export = '\n'.join([
        '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>08同窓会 KPI</title>',
        FONTS,
        '<style>', ROOT_TOKENS,
        'html,body{margin:0;background:#faf8f4;-webkit-print-color-adjust:exact;print-color-adjust:exact}',
        '@page{size:A4 landscape;margin:8mm}', '.k-card{break-inside:avoid}', '.k-page{padding-inline:12px!important}',
        stamp_css, '</style>', D3, stub,
        '</head><body><div id="dash-root">', page, '</div>',
        '<script>document.fonts.ready.then(()=>window.__run());</script></body></html>',
    ])
    open(os.path.join(a.out_dir, 'export.html'), 'w', encoding='utf-8').write(export)
    print('wrote', a.out_dir)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CCLXXXIII: tablet280・tablet281・tablet282 を、曲の中の段 (ステム) に分けて書き出す。
  3 曲とも同じ 11/20 02:40 の鍵盤の録音が入っている。できあがった 3 曲をそのまま重ねると、その鍵盤だけが 3 つ重なって大きくなり、
  ほかの段 (フーガ、tablet117、11/21 の鍵盤) が埋もれる。そこで、それぞれの曲を、その曲の楽譜と同じ作り方 (同じ音量、同じ響き、同じ仕上げの基準) で
  段ごとに書き出して、段どうしを混ぜ直す。段を足し合わせると元の曲に戻る (差は −46 dB 以下)。
    tablet280 → s280_fuga.wav (tablet89 を 4 半音下げたフーガ → レクイエム → Amen)、s280_117.wav (tablet117 の眠りの段と変ロ長調の終わり)
    tablet281 → s281_a.wav (11/20 の鍵盤)、s281_b.wav (11/21 の鍵盤)
    tablet282 → s282_a.wav (11/20 の鍵盤、しっとりの仕上げ; 終わりにもう一度鳴る所は入れない)、s282_b.wav (11/21 の鍵盤、しっとりの仕上げ)
  11/21 の鍵盤の段は、録音の 288.90 秒で止める: 白い鍵盤の終わりのド・ミ (288.13 秒 — シ・ファからド・ミへ、ハ長調で閉じる所) まで。
    その 0.8 秒後に黒い鍵盤へ移る音 (288.94 秒の変ホ) が来るので、その手前で消す。響きは段の中に残るので、最後の和音は響きの尾で自然に消える
  使い方: python make_stems283.py <score_tablet280.json> <score_tablet281.json> <score_tablet282.json> <出力フォルダ>
"""
import sys, os, json, re, copy, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
B_LAST, B_CUT, B_FOUT = 232.9, 288.90, 0.45        # 11/21 の鍵盤の最後の切れ (録音の 232.9 秒から) を、288.90 秒で止める (終わりの 0.45 秒で消す)

def synth(score, out):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'synth.py'), score, out], capture_output=True, text=True)
    m = re.search(r'peak ([0-9.eE+-]+)', r.stdout)
    if not m: raise SystemExit('synth.py が失敗: ' + r.stderr[-400:])
    return float(m.group(1))

def main(s280, s281, s282, outdir):
    os.makedirs(outdir, exist_ok=True)
    plan = [(s280, '280', [('fuga', lambda e: e['rid'].startswith('20261107_089000')), ('117', lambda e: e['rid'].startswith('20261107_117000'))]),
            (s281, '281', [('a', lambda e: e['rid'].startswith('20261120_024046')), ('b', lambda e: e['rid'].startswith('20261121_041625'))]),
            (s282, '282', [('a', lambda e: e['rid'].startswith('20261120_024046') and e['t'] < 700.0), ('b', lambda e: e['rid'].startswith('20261121_041625'))])]
    for sc, n, parts in plan:
        d = json.load(open(sc)); peak = d['meta'].get('fixed_peak')
        if not peak:                                                                    # 曲の山を測る (ステムも曲と同じ基準で仕上げる)
            tmp = os.path.join(outdir, '_mix%s.wav' % n); peak = synth(sc, tmp); os.remove(tmp)
        for name, keep in parts:
            v = copy.deepcopy(d); v['extras'] = [e for e in v['extras'] if e.get('v') == 'REC' and keep(e)]; v['meta']['fixed_peak'] = peak
            if name == 'b':
                for e in v['extras']:
                    if abs(e['off'] - B_LAST) < 1e-6: e['d'] = B_CUT - B_LAST; e['fout'] = B_FOUT
            js = os.path.join(outdir, 's%s_%s.json' % (n, name)); json.dump(v, open(js, 'w'), ensure_ascii=False)
            synth(js, os.path.join(outdir, 's%s_%s.wav' % (n, name)))
            print('tablet%s %-4s 切れ %d 個、基準 %.4f → s%s_%s.wav' % (n, name, len(v['extras']), peak, n, name), flush=True)

if __name__ == '__main__':
    main(*sys.argv[1:5])

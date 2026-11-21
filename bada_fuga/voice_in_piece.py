#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""声の元の wav が手元にある曲から、「曲の中で鳴っているままの声」だけを書き出す。伴奏を引くのではなく、楽譜から声だけを鳴らす (tablet233 = CCXXXIII のために書いた)。
  tablet209 では声の元の音が無かったので、曲の音から伴奏を引いた (extract_voice209.py)。tablet233 の声は calma の声 (20261108_145525_aureola_sensuale_calma.mp3) で、手元にある。
  だから拾う必要が無い: 「声だけ」は calma の声のファイルそのもの。「曲の中で鳴っているままの声」は、同じ楽譜から声だけを synth.py で鳴らせば、伴奏も圧縮の雑音も入らずにできる。
  曲の中の声は synth.py のテープの経路を通る (モノラル、60 Hz〜8 kHz、左 0.707・右は 9 ms 遅れて 0.707、曲の全体の残響)。
    score: 楽譜から声の 1 回目だけを残す。入りと終わりのフェードを外す (extract_voice209.py がフェードを元へ戻すのと同じ形にする)。仕上げ (柔らかい頭打ち) を通さない (linear_master)
    cut:   声の所を切り出す。話し始める前は無音に。声の後の響きは 7 秒まで (終わりの 2 秒で閉じる)。話している所の rms を −24 dB に (extract_voice209.py と同じ決め方)
  使い方:
    python voice_in_piece.py score <score_tabletNNN.json> <score_V.json> [声の rid の初め (既定 20261108)]
    python3 synth.py score_V.json V_stem.wav
    python voice_in_piece.py cut <V_stem.wav> <score_V.json> <出力.wav> [後の響きの秒 (既定 7.0)]
"""
import sys, json
import numpy as np, soundfile as sf

db = lambda v: 10 * np.log10((np.asarray(v, dtype=np.float64) ** 2).mean() + 1e-20)

def score(src, out, prefix='20261108'):
    d = json.load(open(src)); V = sorted((e for e in d['extras'] if e.get('rid', '').startswith(prefix)), key=lambda e: e['t']); assert V, '声の段が無い'
    d['extras'] = [dict(V[0], fin=0.02, fout=0.02)]; d['meta'].update(linear_master=True, fixed_peak=2.0, no_fade=True); json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('声だけの楽譜: %s | 声は曲の %.1f 秒から %.1f 秒ぶん (曲の中では %d 回: %s 秒から; 倍率 %s、フェード %s / %s 秒、残響 %s)' % (
        out, V[0]['t'], V[0]['d'], len(V), '・'.join('%g' % e['t'] for e in V), V[0]['gain'], V[0]['fin'], V[0]['fout'], d['meta'].get('reverb')))

def cut(stem, sc, out, tail=7.0):
    v = json.load(open(sc))['extras'][0]; sr = sf.info(stem).samplerate; a, n = int(round(v['t'] * sr)), int(round((v['d'] + tail) * sr))
    X = sf.read(stem, always_2d=True, dtype='float32')[0].astype(np.float64); z = X[a:a + n].copy(); k = int(min(2.0, tail) * sr); z[-k:] *= np.linspace(1, 0, k)[:, None]
    print('声の段: 声の前 (0〜%.1f 秒) の山 %.6f、切り出した所の山 %.4f' % (v['t'], np.abs(X[:a]).max() if a else 0.0, np.abs(z).max()))
    hop = int(0.05 * sr); p = np.array([db(z[i * hop:(i + 1) * hop]) for i in range(len(z) // hop)]); act = p > np.percentile(p, 95) - 30
    on = np.where(act[:-2] & act[1:-1] & act[2:])[0][0] * 0.05; lead = db(z[:int(max(on - 0.40, 0.05) * sr)]) - 10 * np.log10(np.mean(10 ** (p[act] / 10)))
    z *= np.clip((np.arange(len(z)) / sr - (on - 0.40)) / 0.25, 0.0, 1.0)[:, None]                         # 話し始める前は無音に (曲の中では入りのフェードの下で聞こえない所; extract_voice209.py と同じ)
    print('話し始め: 声の %.2f 秒。その前にあった音は、話している所より %.1f dB 下 (無音にした)' % (on, -lead))
    p = np.array([db(z[i * hop:(i + 1) * hop]) for i in range(len(z) // hop)]); act = p > np.percentile(p, 95) - 30
    z = z * 10 ** ((-24.0 - 10 * np.log10(np.mean(10 ** (p[act] / 10)))) / 20.0); sf.write(out, z.astype(np.float32), sr)
    print('書き出し %s: %.1f 秒、話している所の rms −24.0 dB (全体 %.1f dB)、山 %.3f、左右の相関 %.2f | 話しているのは %.1f〜%.1f 秒' % (
        out, len(z) / sr, db(z), np.abs(z).max(), np.corrcoef(z[:, 0], z[:, 1])[0, 1], np.where(act)[0][0] * 0.05, (np.where(act)[0][-1] + 1) * 0.05))

if __name__ == '__main__':
    if sys.argv[1] == 'score': score(sys.argv[2], sys.argv[3], *(sys.argv[4:5]))
    elif sys.argv[1] == 'cut': cut(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]) if len(sys.argv) > 5 else 7.0)
    else: sys.exit(__doc__)

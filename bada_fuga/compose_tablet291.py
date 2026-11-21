#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXCI〜CCXCV · Voce chiara I〜V (届いた 5 曲のそれぞれに、濁らない鮮明な声を重ねる)
  届いたもの: 20261108_145525_tsukuyomi_aureola_messia.mp3 (make_voice288.py の声)、08 トラック 8.wma、18 トラック 18.wma、tablet117.mp4、tablet286.mp4、tablet285.mp4。
    依頼は「漏れなく全部の曲に、20261108 の音声を濁らずに、鮮明なきれいな声にして、曲を作って」。「全部の曲に」は、5 曲のそれぞれに声を重ねる、と読んだ (曲は 5 つ)
      CCXCI   Voce chiara I   トラック 8        CCXCII  Voce chiara II  トラック 18 (声より短いので、2 回続けて鳴らす)
      CCXCIII Voce chiara III tablet117         CCXCIV  Voce chiara IV  tablet285         CCXCV   Voce chiara V   tablet286
  声は make_voice291.py で作り直す (calma の声から; 声は 1 つ、残響なし、低い所を軽く、息を減らす、言葉の帯域を立てる)。曲の調に合わせて 3 通り:
    a3c = A3・ハ長調の音階 (トラック 8、tablet285・286 の後半)   a3f = A3・ヘ長調の音階 (トラック 18)   bb3 = B♭3・変ニ長調の音階 (tablet117、tablet285・286 の前半)
  曲は届いたまま: 速さも高さも変えない、楽器も響きも足さない、帯域も削らない (synth.py の faithful の経路; ステレオのまま)。動かすのは音量のつまみだけ
  濁らせないための置き方:
    声が先      初めの 2 小節は無音、2 小節 (8 秒) から声、4 小節 (16 秒) から曲 (これまでの入り方と同じ)
    声の下の曲  声が話している間は、曲を BEDL dB (声の約 10 dB 下) にそろえる: 曲の 20 秒窓の音量を見て、10 秒ごとにつまみを決める (−2〜−14 dB、2 dB 刻み、3 秒かけて動かす)。
               曲が小さい所は少しだけ下げ、大きい所は深く下げるので、声と曲の比が場所によらずそろう
    声が休む間  曲は TRIM dB の大きさ (tablet285・286 は届いたままの大きさ)。声が終わる 1 秒前から、6 秒かけて戻す (声の最後の言葉まで、曲は小さいまま)。
               tablet286 の 1 回目だけは 5 秒前から戻す: 声が終わってすぐ、曲が自分で 1.6 秒休む所 (−43 dB) があり、そこを小さいまま通ると音が途切れるので
    仕上げ      歪ませない (synth.py の linear_master): 声と曲が掛け合わさる歪みを作らない
  形 (♩=60 の目盛り、1 小節 = 4 秒): 曲ごとに PIECES に
  使い方: python compose_tablet291.py <番号 291〜295> <wav のフォルダ> <chords291.json (analyze_chords.py の出力)> [score_tabletNNN.json]
    wav のフォルダ: 20261108_145525_chiara_a3c.wav・_a3f.wav・_bb3.wav (make_voice291.py の声)、20261107_080000.wav (トラック 8)、20261107_180000.wav (トラック 18)、
                   20261107_117000.wav (tablet117 の音)、20261121_285000.wav (tablet285 の音)、20261121_286000.wav (tablet286 の音)
"""
import sys, os, json, math
import numpy as np, soundfile as sf
NUM = int(sys.argv[1]); WDIR, CHP = os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet%d.json' % NUM
E = lambda k, v: float(os.environ.get(k, v))
VTRIM = E('VTRIM', '4.4')                                   # 声の音量: 声のファイルの大きさ (rms −24.1 dB) から +4.4 dB → 話している所で約 −19.5 dB
BEDL = E('BEDL', '-30.0')                                   # 声が話している間の曲の大きさ (dB; 20 秒窓)
DMIN, DMAX, DSTEP = E('DMIN', '-14.0'), E('DMAX', '-2.0'), 2.0   # 声の下で曲を下げる量の範囲 (dB) と刻み
SEG, RAMP, RIN, REL = 10.0, 3.0, 4.0, 6.0                   # つまみを決める間隔 / 動かす時間 / 声が入る前に下げる時間 / 声が終わる時に戻す時間 (秒)
REL0 = -1.0                                                 # 戻し始める所 (声の終わりから秒; 既定は 1 秒前から。曲ごとに変えられる)
FIXPEAK = E('FIXPEAK', '1.0')                               # 仕上げの基準 (linear_master; 山 × 1.2515 ÷ FIXPEAK が 1 を超えないこと)
K_MASTER = 0.1 * 0.707 * 0.89 * (1.15 / math.tanh(1.15))    # synth.py の faithful の経路と仕上げを通った後の倍率 (録音の rms を 1 として; FIXPEAK = 1 のとき) = 0.08848
V_OFF, V_ON, V_END, V_LEN = 4.9, 5.4, 196.15, 198.46        # 声: ファイルの 4.9 秒から置く (その前は無音; 話し始めは 5.4 秒、話し終わりは 196.15 秒)
VPRE = '20261108_145525_chiara_'
COLV, COLM = (255, 200, 170), (150, 195, 240)
# 曲ごと: 名前、録音、声が休む間の大きさ (届いた大きさから dB)、曲を置く所 (録音の 0 秒が来る曲の秒; 2 つあれば 2 回鳴らす)、声 (版, 話し始める秒 [, 戻し始める所])、小節数、段落 (小節, 題, 説明)。
#   bedl があれば、その曲だけ声の下の大きさを変える (トラック 18 は 1〜4 kHz の音が多いので、2 dB 深く)
PIECES = {
    291: dict(roman='CCXCI', it='I', name='トラック 8', rid='20261107_080000', trim=E('TRIM', '-2.0'), plays=[15.3], voices=[('a3c', 8.0)], total=67, key='ハ長調 / イ短調',
              sections=[(0, 'I. Voce — 澄んだ声が、先に', '2 小節から声。4 小節からトラック 8 (声の下で小さく)'),
                        (50, 'II. Sola — 声が終わり、トラック 8 だけ', '3 分 19 秒に声が終わる。曲は届いたままの形で、終わりまで')]),
    292: dict(roman='CCXCII', it='II', name='トラック 18', rid='20261107_180000', trim=E('TRIM', '-5.0'), plays=[15.25, 159.25], voices=[('a3f', 8.0)], total=78, key='ニ短調 / ヘ長調', bedl=-32.0,
              sections=[(0, 'I. Voce — 澄んだ声が、先に', '2 小節から声。4 小節からトラック 18 (声の下で小さく)'),
                        (40, 'II. Da capo — トラック 18 をもう一度', '2 分 40 秒、トラック 18 が初めからもう一度。声は 3 分 19 秒まで'),
                        (50, 'III. Sola — 声が終わり、トラック 18 だけ', '曲は届いたままの形で、終わりまで')]),
    293: dict(roman='CCXCIII', it='III', name='tablet117', rid='20261107_117000', trim=E('TRIM', '-4.5'), plays=[16.0], voices=[('bb3', 8.0), ('bb3', 340.0)], total=199, key='変ロ短調 → ヘ短調 → 変ロ長調',
              sections=[(0, 'I. Voce — 澄んだ声が、先に', '2 小節から声。4 小節から tablet117 (眠りへの曲; 声の下で小さく)'),
                        (50, 'II. Calore — 声が休み、曲だけ', '3 分 19 秒に声が終わる。暖まりの段'),
                        (85, 'III. Voce — 声をもう一度', '5 分 40 秒から声。冷えの段の上で、8 分 51 秒まで'),
                        (133, 'IV. Sonno — 眠り', '声が終わり、曲だけ。ゆっくり静かになって、眠りへ')]),
    294: dict(roman='CCXCIV', it='IV', name='tablet285', rid='20261121_285000', trim=E('TRIM', '0.0'), plays=[8.0], voices=[('bb3', 8.0), ('a3c', 328.0)], total=152, key='変ニ長調 → ハ長調',
              sections=[(0, 'I. Voce — 澄んだ声が、先に', '2 小節から声 (変ロを中心に)。4 小節から tablet285 (声の下で小さく)'),
                        (50, 'II. Sola — 声が休み、曲だけ', '3 分 19 秒に声が終わる。11/20 の鍵盤が流れ、ファへ向かう'),
                        (78, 'III. Luce — 同じファから白い鍵盤へ', '5 分 12 秒に同じファ。曲だけで、光が差す'),
                        (82, 'IV. Voce — 声をもう一度', '5 分 28 秒から声 (ラを中心に; 半音低く)。8 分 39 秒まで'),
                        (130, 'V. Amen — 声が終わり、曲だけ', '9 分 2 秒に山。ド・ミで閉じて、Amen と祈り')]),
    295: dict(roman='CCXCV', it='V', name='tablet286', rid='20261121_286000', trim=E('TRIM', '0.0'), plays=[8.0], voices=[('bb3', 8.0, -5.0), ('a3c', 350.2)], total=153, key='変ニ長調 → ハ長調',
              sections=[(0, 'I. Voce — 澄んだ声が、先に', '2 小節から声 (変ロを中心に)。4 小節から tablet286 (声の下で小さく)'),
                        (50, 'II. Sola — 声が休み、曲だけ', '3 分 19 秒に声が終わる。11/20 の鍵盤が流れ、ファへ向かう'),
                        (83, 'III. Luce — 同じファから白い鍵盤へ', '5 分 34 秒に同じファ。曲だけで、光が差す'),
                        (87, 'IV. Voce — 声をもう一度', '5 分 50 秒から声 (ラを中心に; 半音低く)。9 分 1 秒まで'),
                        (136, 'V. Cadenza — 声が終わり、曲だけ', '9 分 25 秒に山。ド・ミで 3 回閉じる')]),
}
PZ = PIECES[NUM]; TOTAL = PZ['total']; RM = PZ['rid']; BEDL = PZ.get('bedl', BEDL)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
BPM = 60

# 曲の音量を読む (つまみを決めるため; 音そのものには手を入れない)
_x, _sr = sf.read(os.path.join(WDIR, RM + '.wav'), always_2d=True, dtype='float32'); _p = (_x.astype(np.float64) ** 2).mean(axis=1)
del _x; M_LEN = len(_p) / _sr; M_RMS = math.sqrt(_p.mean()); _h = _sr // 2; _e = np.array([_p[i * _h:(i + 1) * _h].mean() for i in range(len(_p) // _h)])      # 0.5 秒ごとの大きさ
_on = np.where(10 * np.log10(_e + 1e-12) > -45.0)[0]; M_ON, M_OFF = _on[0] * 0.5, (_on[-1] + 1) * 0.5                                           # 音が鳴っている範囲 (−45 dB より上)
def level(t, win=20.0):
    """曲の t 秒のまわり win 秒の大きさ (dB; 声が休む間の大きさ = 届いた大きさ + trim で)"""
    a, b = max(int((t - win / 2) * 2), 0), min(int((t + win / 2) * 2), len(_e)); return 10 * math.log10(_e[a:b].mean() + 1e-12) + PZ['trim'] if b > a else -120.0
_v, _ = sf.read(os.path.join(WDIR, VPRE + PZ['voices'][0][0] + '.wav'), always_2d=True, dtype='float32'); V_RMS = math.sqrt((_v.astype(np.float64) ** 2).mean())
GAIN = lambda db, rms: 10 ** (db / 20.0) * rms * FIXPEAK / K_MASTER      # 「録音の大きさから db」になる倍率 (synth.py は録音全体の rms を 0.1 に揃えてから倍率を掛ける)
GV = GAIN(VTRIM, V_RMS)

def duck(t):
    """声の下で曲を下げる量 (dB): その 10 秒 (前後 5 秒を足した 20 秒窓) の大きさを BEDL にそろえる。DMAX〜DMIN の範囲、DSTEP 刻み"""
    return float(np.clip(round((BEDL - level(t + SEG / 2)) / DSTEP) * DSTEP, DMIN, DMAX))

def ride(T0, spans):
    """録音の 0 秒が曲の T0 秒に来る 1 回ぶんの、つまみの動き。spans = 声が話している範囲 (曲の秒; 始め, 終わり) の一覧。
      返り値: [(録音の秒, つまみ dB, その値へ動かす時間)] — 録音の秒からその時間をかけて、前の値からその値へ動く"""
    pts = []; cur = None
    for a, b, rel0 in spans:                                    # a, b: 声が話している範囲 (曲の秒)、rel0: 戻し始める所 (b から秒)
        m_a, m_b = a - T0, b - T0                               # 録音の秒
        if m_b <= M_ON or m_a >= M_OFF: continue
        if m_a - RIN - 0.5 <= M_ON: t = 0.0; first = True      # 曲が鳴り始める時にはもう声がある: 初めから下げておく
        else: t = m_a - 0.5 - RIN; first = False                # 声が入る 0.5 秒前に下げ終わる
        end = min(m_b + rel0, M_OFF)                            # ここから REL 秒かけて戻す
        k = 0
        while t < end - 1.0:
            d = duck(max(t, 0.0) + (RIN if (k == 0 and not first) else 0.0))
            if k == 0 or (d != cur and end - t >= 2 * REL): pts.append((t, d, 0.0 if (first and k == 0) else (RIN if k == 0 else RAMP))); cur = d   # 戻す前の最後の段は 12 秒以上 (6 秒のクロスフェードが入る長さ)
            t += (RIN if (k == 0 and not first) else 0.0) + SEG; k += 1
        if m_b + rel0 + REL < M_OFF: pts.append((end, 0.0, REL)); cur = None
    if not pts or pts[0][0] > 0.0: pts.insert(0, (0.0, 0.0, 0.0))
    return pts

def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None, env=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=0, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=True, env=env)
def curve(pts, n, dt):
    """つまみの動き (ride の返り値) を、dt 秒ごとの倍率の列にする (画面の波形用; 声が休む間の大きさを 1 として)。クロスフェードと同じく、倍率はまっすぐ動く"""
    t = np.arange(n) * dt; g = np.full(n, 10 ** (pts[0][1] / 20.0))
    for k in range(1, len(pts)):
        m, db, r = pts[k]; a0, a1 = 10 ** (pts[k - 1][1] / 20.0), 10 ** (db / 20.0); g = np.where(t >= m, a0 + (a1 - a0) * np.clip((t - m) / max(r, 1e-6), 0.0, 1.0), g)
    return g
PLAYS = []; MUSIC = []; RIDES = []
SPANS = [(v[1], v[1] + (V_END - V_ON), v[2] if len(v) > 2 else REL0) for v in PZ['voices']]
for n, T0 in enumerate(PZ['plays']):
    pts = ride(T0, SPANS); RIDES.append((T0, pts)); c = CH[RM]
    envp = [round(float(v), 4) for v in np.asarray(c['env']) * curve(pts, len(c['env']), c.get('env_dt', 0.05))]   # 画面の波形: 曲の包絡に、つまみの動きを掛けたもの (声の下で小さくなるのが見える)
    for k, (m, db, r) in enumerate(pts):                        # 同じ録音どうしのクロスフェードで、つまみを動かす
        nxt = pts[k + 1] if k + 1 < len(pts) else None; end = (nxt[0] + nxt[2]) if nxt else M_LEN
        what = '声の下で (声の約 10 dB 下にそろえる)' if db < 0 else '曲だけ (%s)' % ('届いたままの大きさ' if PZ['trim'] == 0 else '届いたままの形')
        tag = '%s%s — %s' % (PZ['name'], ' (2 回目)' if n else '', what) if (k == 0 or db == 0 or pts[k - 1][1] == 0) else ''
        MUSIC.append(len(PLAYS)); PLAYS.append(play(RM, T0 + m, GAIN(PZ['trim'] + db, M_RMS), m, end - m, 1, COLM, tag, fin=(r if k else 0.03), fout=(nxt[2] if nxt else 0.05), env=envp))
for n, (ver, ts) in enumerate(v[:2] for v in PZ['voices']):
    PLAYS.append(play(VPRE + ver, ts - (V_ON - V_OFF), GV, V_OFF, V_LEN - V_OFF, 0, COLV, '澄んだ声 — %s%s' % ({'a3c': 'ラを中心に', 'a3f': 'ラを中心に', 'bb3': '変ロを中心に'}[ver], ' (2 回目)' if n else ''), fin=0.3, fout=2.0))
LEAD = [(i, PLAYS[i]['beat']) for i in MUSIC]                # 和音の表示は曲の録音から
def harm_at(q):
    cur = 'C'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0)
            cur = c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)]
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    for bar, title, sub in PZ['sections']: P_.section(bar, title + (' (♩=60)' if bar == 0 else ''), sub)
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        c = CH.get(p['rid'], {})
        add('REC', p['beat'], p['dur'] * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, p['rid'] + '.wav'), off=p['off'], fin=p['fin'], fout=p['fout'], semis=0, faithful=True,
            rid=p['rid'] + '.wav', tag=p['tag'], lane=p['lane'], color=list(p['color']), env=p['env'] or c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=p['off'], env_faded=bool(p['env']))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'linear_master': True, 'fixed_peak': FIXPEAK,
        'title': 'Requiem BADA — %s · Voce chiara %s' % (PZ['roman'], PZ['it']),
        'subtitle': '濁らない鮮明な声・%s。曲は届いたまま。%s、♩=60' % (PZ['name'], PZ['key']),
        'footer': ['声は calma の声から作り直した、濁らない鮮明な声 (20 代の女性、声は 1 つ、残響なし)。2 小節から声、4 小節から曲。',
                   '曲は届いたまま (速さも高さもそのまま)。声が話している間だけ、曲を声の約 10 dB 下にそろえる。声が休むと、元の大きさへ戻る。',
                   '楽器も響きも足さない。仕上げは歪ませない。%d 小節。' % TOTAL]}

if __name__ == '__main__':
    compose.main(OUT, seed=NUM, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'fixed_peak', d['meta'].get('fixed_peak'), '| 声 %+.1f dB (倍率 %.3f)、曲 %+.1f dB (倍率 %.3f)、声の下 %.0f dB、曲の rms %.1f dB、鳴っているのは %.1f〜%.1f 秒' % (
        VTRIM, GV, PZ['trim'], GAIN(PZ['trim'], M_RMS), BEDL, 20 * math.log10(M_RMS), M_ON, M_OFF))
    for T0, pts in RIDES: print('  つまみ (曲の秒 → dB): ' + ' '.join('%.1f:%+.0f' % (T0 + m, db) for m, db, r in pts))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  off %6.2f  fin %.2f fout %.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['off'], e['fin'] or 0, e['fout'] or 0, e['lane'], e['tag']))

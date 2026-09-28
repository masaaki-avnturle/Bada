# -*- coding: utf-8 -*-
"""
Tablet Sessions XL〜XLIII の歌詞 (すべてこの曲のために書いたオリジナル。参考にした曲の歌詞は使っていない)。
  各曲: block = 1 フレーズの小節数 (主題 1 つ分)、sections = [(区間の題名の頭, [歌詞の行…], block の上書き)]。
  行は空白で語を区切るだけ (うたうときは無視)。1 行 = 1 フレーズ。区間のフレーズが行より多いときは最初の行から繰り返す。
"""
LYRICS = {
    'tablet40': {                              # XL · Human Nature — 夜の街、ひとの心のぬくもり
        'block': 2, 'gain': 0.6,
        'sections': [
            ('Verse 1', ['よるの まちに ひかる あめ', 'ガラスごしに きみを みてた', 'ことばよりも やさしい おと', 'こころが しずかに ゆれる']),
            ('Chorus 1', ['ひとは なぜ こいを して', 'よるに とけて ゆくの', 'ふれた ゆびの ぬくもり', 'それが ひとの こころ']),
            ('Verse 2', ['かぜが ほほを なでて ゆく', 'しらない まちの ネオン', 'きみの なまえ よんで みた', 'こたえは やみの なか']),
            ('Chorus 2', ['ひとは なぜ こいを して', 'よるに とけて ゆくの', 'ふれた ゆびの ぬくもり', 'それが ひとの こころ']),
            ('Bridge — 9/22 17:53', ['ながれる ときの なかで', 'ふたり ただ よりそう']),
            ('Last chorus', ['ひとは なぜ こいを して', 'よるに とけて ゆくの', 'ふれた ゆびの ぬくもり', 'それが ひとの こころ',
                             'ひとは なぜ あいを して', 'あさを まちわびるの', 'かさねた こころの ねつ', 'それが ひとの あかし']),
        ]},
    'tablet41': {                              # XLI · Recall (+ Anubis) — たましいの旅、冥界の導き、祈り
        'block': 2, 'gain': 0.6,
        'sections': [
            ('Kyrie', ['とおい きおくの なかで', 'きみの こえが ひびく', 'しずかに ねむる たましい', 'やみを てらす ひかり']),
            ('Sequentia', ['おもいだして あの ひを', 'わすれないで いのりを', 'めぐる ときの かなたで', 'また あえる ひまで']),
            ('Duat — 冥界', ['くろい かみの みちびき', 'すなの うみを わたる', 'はかりに のせた こころ', 'はねより かるく あれ']),
            ('Lacrimosa — 9/22 17:53', ['なみだに ぬれた この よを'], 4),
            ('Lux aeterna', ['おもいだして あの ひを', 'わすれないで いのりを', 'めぐる ときの かなたで', 'また あえる ひまで',
                             'とわの ひかりに つつまれ', 'きみは そらへ かえる', 'わたしは ここで うたう', 'レクイエムを きみに']),
        ]},
    'tablet42': {                              # XLII · Ray — 夜明け前を駆け抜ける、ひとすじの光
        'block': 4, 'gain': 0.6,
        'sections': [
            ('Verse 1', ['よあけまえの まちを かけぬける', 'つめたい かぜを きりさいて', 'だれも しらない みちの さき', 'とどかない ゆめを おいかけた']),
            ('Chorus 1', ['ひかりよ この むねを つらぬけ', 'やみを こえて とおくへ', 'ひとすじの レイに なって', 'あしたへ はしりだせ']),
            ('Verse 2', ['こわれた とけいの はりが', 'とまった ままの よる', 'それでも ぼくは まえを むく', 'ちいさな ひかりを しんじて']),
            ('Chorus 2', ['ひかりよ この むねを つらぬけ', 'やみを こえて とおくへ', 'ひとすじの レイに なって', 'あしたへ はしりだせ']),
            ('Last chorus', ['ひかりよ この むねを つらぬけ', 'やみを こえて とおくへ', 'ひとすじの レイに なって', 'あしたへ はしりだせ',
                             'ひかりよ この そらを てらせ', 'すべてを こえて とおくへ', 'きみと みた あの レイを', 'えいえんに わすれない']),
        ]},
    'tablet43': {                              # XLIII · Recall II — よみがえる記憶、とどかない願い
        'block': 2, 'gain': 0.6,
        'sections': [
            ('Verse 1', ['かれた はなを てに とり', 'あの ひの そらを おもう', 'こえに ならない ことばが', 'むねの おくで ねむる']),
            ('Chorus 1', ['よみがえる きおくの かけら', 'きみの えがおが ゆれる', 'とどかない ねがいを だいて', 'きょうも ひとり うたう']),
            ('Verse 2', ['ふゆの まどに えがいた', 'きえて ゆく なまえ', 'ときは なにも かたらず', 'ただ ながれて ゆく']),
            ('Bridge — 9/22 17:53', ['もう いちど あいたい'], 4),
            ('Last chorus', ['よみがえる きおくの かけら', 'きみの えがおが ゆれる', 'とどかない ねがいを だいて', 'きょうも ひとり うたう',
                             'よみがえる あの ひの ひかり', 'きみの こえが きこえる', 'わすれない いつまでも', 'この うたを きみに']),
        ]},
    'tablet44': {                              # XLIV · Anubis — 名前をなくした魂を闇の向こうへ導く、わたしの声のレクイエム
        'block': 2, 'gain': 0.72, 'timbre': 'user', 'range': (49, 60), 'voice_name': 'わたしの声 (9/28)', 'title_suffix': '',
        'sections': [
            ('Verse 1', ['つきの ない よるに', 'くろい かげが まねく', 'なまえを なくした たましい', 'しずかに ならんで あるく']),
            ('Chorus 1', ['みちびいて やみの むこうへ', 'なみだを すなに かえて', 'わすれられた いのりを', 'いま ここで うたう']),
            ('Verse 2', ['かねの おとが とおく', 'ひとつ ひとつ きえる', 'だれかが よんで いる', 'ふりむけば だれも いない']),
            ('Chorus 2', ['みちびいて やみの むこうへ', 'なみだを すなに かえて', 'わすれられた いのりを', 'いま ここで うたう']),
            ('Lacrimosa — 9/22 17:53', ['やすらかに ねむれ'], 4),
            ('Last chorus', ['みちびいて やみの むこうへ', 'なみだを すなに かえて', 'わすれられた いのりを', 'いま ここで うたう',
                             'みちびいて ひかりの ほうへ', 'こころを はかりに のせて', 'えいえんの やすらぎを', 'レクイエムを きみに']),
        ]},
    'tablet45': {                              # XLV · Goccia di colore — ひとしずくの色で世界が変わる、あたたかい祈り (父が嫌いでない穏やかな声で)
        'block': 2, 'gain': 0.72, 'timbre': 'user', 'range': (47, 57), 'voice_name': 'わたしの声 (9/28)', 'title_suffix': '',
        'voice_opts': {'vib_depth': 0.2, 'vib_rate': 5.0, 'attack': 0.028, 'sib': 0.55, 'presence': 2.5},
        'sections': [
            ('Requiem aeternam', ['やすらかに ねむれ とわに', 'やさしい ひかりの なかで'], 4),
            ('Aria I — A メロ', ['しろい せかいに ひとしずく', 'きみが おとした いろが ある', 'しずかに ひろがる あおい なみ', 'わたしの むねを そめて ゆく']),
            ('Aria I — サビ', ['ひとしずくの いろが おちて', 'しずかに せかいが かわる', 'なみだも いつか', 'なみだは にじに かわる']),
            ('Aria II — A メロ', ['とおい ひの ぬくもりを', 'てのひらに のこして', 'ありがとうと いえずに', 'きせつは めぐる']),
            ('Last chorus', ['ひとしずくの いろが おちて', 'しずかに せかいが かわる', 'なみだも いつか', 'なみだは にじに かわる',
                             'ひとしずくの いのりで', 'よるは あける', 'わすれない ずっと', 'この いろを わすれない']),
            ('Lux aeterna', ['とわの ひかりを きみに'], 4),
        ]},
    'tablet46': {                              # XLVI · Requiem in fuga — レクイエムの祈りの言葉をもとにした日本語 (オリジナル)。主題が入るたびに同じ祈りを歌う
        'block': 2, 'gain': 0.85, 'timbre': 'user', 'range': (65, 75), 'top': 81, 'voice_name': '女声の歌', 'title_suffix': '',
        'voice_opts': {'formant': 1.21, 'breath': 0.15, 'vib_depth': 0.5, 'vib_rate': 5.8, 'vib_delay': 0.18, 'presence': 3.0, 'sib': 0.7, 'attack': 0.02},
        'sections': [
            ('Requiem aeternam — Fuga I', ['とわの やすらぎを かれらに', 'たえざる ひかりで てらせ'], 2,
             {'entries': True, 'voices': 'SATB', 'ranges': {'S': (66, 76), 'A': (60, 69), 'T': (60, 69), 'B': (58, 67)}, 'pans': {'S': -0.3, 'A': 0.3, 'T': 0.1, 'B': -0.1}, 'boost': 1.0}),
            ('Kyrie — コラール', ['あわれみたまえ しずかに', 'いのりは そらへ のぼる'], 4),
            ('Lux aeterna — Fuga II', ['とわの ひかりが かれらを', 'やさしく てらし つづける'], 2,
             {'entries': True, 'voices': 'SATB', 'ranges': {'S': (66, 76), 'A': (60, 69), 'T': (60, 69), 'B': (58, 67)}, 'pans': {'S': -0.3, 'A': 0.3, 'T': 0.1, 'B': -0.1}, 'boost': 1.0}),
            ('In paradisum — コラール', ['てんしよ みちびきたまえ'], 4),
        ]},
    'tablet46en': {                            # XLVI · Requiem in fuga の英語版 — レクイエムの祈りの言葉をもとに書いたオリジナルの英語。(表示, 発音の表記) の組
        'block': 2, 'gain': 0.85, 'timbre': 'user', 'range': (65, 75), 'top': 81, 'voice_name': 'Soprano', 'title_suffix': '',
        'title': 'Requiem BADA — XLVI · Requiem in fuga (English)', 'subtitle': '歌の旋律がフーガのレクイエムを英語で — 9/24 の 5 本と、わたしの声から書き換えた 20 代前半の淑女の声 (♩=60)',
        'voice_opts': {'formant': 1.22, 'breath': 0.12, 'vib_depth': 0.45, 'vib_rate': 5.7, 'vib_delay': 0.2, 'presence': 3.5, 'sib': 0.85, 'attack': 0.02},
        'sections': [
            ('Requiem aeternam — Fuga I', [('Grant them rest for-ev-er-more', 'grant dhem rest fxr e vxr mor'),
                                           ('Let the end-less light shine on them', 'let dhx end lxs lait shain on dhem')], 2,
             {'entries': True, 'voices': 'SATB', 'ranges': {'S': (66, 76), 'A': (60, 69), 'T': (60, 69), 'B': (58, 67)}, 'pans': {'S': -0.3, 'A': 0.3, 'T': 0.1, 'B': -0.1}, 'boost': 1.0}),
            ('Kyrie — コラール', [('Lord, have mer-cy on us all', 'lord haev mxr sii on as ol'),
                                  ('Hear our qui-et prayer', 'hiir aur kwai xt prer')], 4),
            ('Lux aeterna — Fuga II', [('Light e-ter-nal, shine up-on them', 'lait ii txr nxl shain x pon dhem'),
                                       ('Soft-ly and gent-ly for-ev-er-more', 'soft lii aend jent lii fxr e vxr mor')], 2,
             {'entries': True, 'voices': 'SATB', 'ranges': {'S': (66, 76), 'A': (60, 69), 'T': (60, 69), 'B': (58, 67)}, 'pans': {'S': -0.3, 'A': 0.3, 'T': 0.1, 'B': -0.1}, 'boost': 1.0}),
            ('In paradisum — コラール', [('May the an-gels lead you home', 'mei dhx ein jxlz liid yuu houm')], 4),
        ]},
}
# 十八歳の淑女の英語の歌声: 英語版と同じ歌詞・フーガで、響きをもう少し明るく (1.25 倍)、息を少し足して軽く若々しく、声域をわずかに上げる
_SEC18 = []
for sec in LYRICS['tablet46en']['sections']:
    if len(sec) > 3:
        sec = sec[:3] + (dict(sec[3], ranges={'S': (67, 77), 'A': (61, 70), 'T': (61, 70), 'B': (59, 68)}),)
    _SEC18.append(sec)
LYRICS['tablet46en18'] = dict(LYRICS['tablet46en'], range=(66, 76), top=81, voice_name='Soprano (18)', sections=_SEC18,
    title='Requiem BADA — XLVI · Requiem in fuga (English, 18)',
    subtitle='歌の旋律がフーガのレクイエムを英語で — わたしの声から書き換えた十八歳の淑女の声 (♩=60)',
    voice_opts={'formant': 1.25, 'breath': 0.18, 'vib_depth': 0.38, 'vib_rate': 5.9, 'vib_delay': 0.2, 'presence': 4.0, 'sib': 0.85, 'attack': 0.018})

# XLVII · Aria di cattedrale — 大聖堂の賛美歌のアリア。この曲のために書いたオリジナルの英語の賛美歌 (表示, 発音の表記)。19 歳の淑女の声
LYRICS['tablet47'] = {
    'block': 4, 'gain': 0.85, 'timbre': 'user', 'range': (66, 76), 'top': 81, 'voice_name': 'Soprano (19)', 'title_suffix': '',
    'voice_opts': {'formant': 1.24, 'breath': 0.16, 'vib_depth': 0.42, 'vib_rate': 5.8, 'vib_delay': 0.22, 'presence': 3.5, 'sib': 0.8, 'attack': 0.022},
    'sections': [
        ('Verse 1', [('Hol-y light up-on the wa-ters', 'hou lii lait x pon dhx wo txrz'),
                     ('Gent-ly guide us through the night', 'jent lii gaid as thruu dhx nait')]),
        ('Verse 2', [('All the bells of heav-en ring-ing', 'ol dhx belz xv he vxn rin ging'),
                     ('Sing a-loud the morn-ing song', 'sing x laud dhx mor ning song')]),
        ('Verse 3', [('Grace that holds us, love e-ter-nal', 'greis dhaet houldz as lav ii txr nxl'),
                     ('Bring us home where we be-long', 'bring as houm wer wii bi long')]),
        ('Amen', [('A-men', 'aa men')], 3),
    ]}

# XLVIII · Klang und Fuge — 5 人の歌い手 (淑女 2 人・紳士 3 人) がドイツ語で歌う。歌詞はレクイエムの典礼文のドイツ語 (表示, 発音の表記)
_SINGERS = {                                   # 歌い手ごとの声: 響きの長さ (formant)・息・ビブラート。声域は ranges (フレーズの平均の音高)
    'S':   {'formant': 1.24, 'breath': 0.16, 'vib_depth': 0.42, 'vib_rate': 5.8, 'vib_delay': 0.22, 'presence': 3.5, 'sib': 0.8, 'attack': 0.022},   # ソプラノの淑女
    'A':   {'formant': 1.15, 'breath': 0.12, 'vib_depth': 0.36, 'vib_rate': 5.5, 'vib_delay': 0.25, 'presence': 3.0, 'sib': 0.8, 'attack': 0.025},   # アルトの淑女
    'T':   {'formant': 1.04, 'breath': 0.05, 'vib_depth': 0.32, 'vib_rate': 5.4, 'vib_delay': 0.25, 'presence': 2.5, 'sib': 0.8, 'attack': 0.02},    # 高音の紳士 (テノール)
    'Bar': {'formant': 1.0, 'breath': 0.04, 'vib_depth': 0.28, 'vib_rate': 5.2, 'vib_delay': 0.3, 'presence': 2.0, 'sib': 0.8, 'attack': 0.025},    # バリトンの紳士
    'B':   {'formant': 0.9, 'breath': 0.03, 'vib_depth': 0.2, 'vib_rate': 5.0, 'vib_delay': 0.35, 'presence': 1.5, 'sib': 0.7, 'attack': 0.03},     # 重低音の紳士 (バッソ・プロフォンド)
}
_CHOIR = {'voices': 'SATB', 'vopts': _SINGERS, 'boost': 1.0,
          'ranges': {'S': (66, 76), 'A': (58, 67), 'T': (55, 64), 'Bar': (47, 56), 'B': (38, 48)},
          'pans': {'S': -0.35, 'A': 0.35, 'T': 0.15, 'Bar': -0.15, 'B': 0.0},
          'gains': {'B': 1.1, 'Bar': 0.85}}
_FUGUE = dict(_CHOIR, entries=True, extra=[{'name': 'Bar', 'src': 'T'}], boost=1.5)   # フーガ: 主題の入りごと、バリトンはテノールの 1 オクターヴ下 (入りがまばらなので大きめ)
_KLANG = dict(_FUGUE, prefix='Klang', boost=1.0)                                 # 共鳴する不協和音: 4 声が置いた和音を全員で
_HOMO = dict(_CHOIR, extra=[{'name': 'Bar', 'src': 'B'}], boost=0.6)              # コラール / Amen: 全員が同じ言葉を和声で、バリトンはバスの 1 オクターヴ上 (5 人そろうので小さめ)
LYRICS['tablet48'] = {
    'block': 2, 'gain': 0.6, 'timbre': 'user', 'range': (60, 72), 'top': 81, 'voice_name': '歌い手 5 人', 'title_suffix': '',
    'voice_opts': _SINGERS['S'],
    'sections': [
        ('Klang I', [('Ru-he', 'ruu hx')], 2, _KLANG),
        ('Fuga I', [('Herr, gib ih-nen e-wi-ge Ru-he', 'her gip ii nxn e vi gx ruu hx'),
                    ('und das e-wi-ge Licht leuch-te ih-nen', 'unt das e vi gx lisht loish tx ii nxn')], 2, _FUGUE),
        ('Kyrie', [('Herr, er-bar-me dich', 'her er baar mx dish'), ('Chri-stus, er-bar-me dich', 'kri stus er baar mx dish')], 4, _HOMO),
        ('Klang II', [('Trä-nen', 'tre nxn')], 2, _KLANG),
        ('Fuga II', [('E-wi-ges Licht, leuch-te ih-nen', 'e vi gxs lisht loish tx ii nxn'),
                     ('Herr, mit dei-nen Hei-li-gen', 'her mit dai nxn hai li gxn')], 2, _FUGUE),
        ('Amen', [('A-men', 'aa men')], 3, _HOMO),
    ]}

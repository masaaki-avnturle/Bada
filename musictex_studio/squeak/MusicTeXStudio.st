'MusicTeX Studio - Squeak edition
 スペクトルコード制作アプリ (MusixTeX / texlive-music)
 macOS デスクトップ専用ソフト風デザイン:
   タイトルバー(信号機) + ツールバー(トランスポート+LCD) +
   ライブラリ(楽器/テンプレート) + センター(モーツァルト・ビジョン/楽譜/エディタ) +
   インスペクタ(スペクトルコード/五行コード線)
 使い方: このファイルを fileIn して  MTSApp open  を実行
 (c) Masaaki Yamaguchi - MIT License'!

Object subclass: #MTSTheory
	instanceVariableNames: ''
	classVariableNames: ''
	poolDictionaries: ''
	category: 'MusicTeXStudio'!

!MTSTheory class methodsFor: 'pitch'!
midiToFreq: midi
	^ 440.0 * (2.0 raisedTo: (midi - 69) / 12.0)! !

!MTSTheory class methodsFor: 'pitch'!
midiToWavelength: midi
	"音の周波数を約40オクターブ上げて可視光帯へ写像。^ {freqHz. THz. nm}"
	| f fl nm |
	f := self midiToFreq: midi.
	fl := f.
	[299792458.0 / fl > 7.8e-7] whileTrue: [fl := fl * 2.0].
	[299792458.0 / fl < 3.8e-7] whileTrue: [fl := fl / 2.0].
	nm := 299792458.0 / fl * 1000000000.
	^ Array with: f with: fl / 1000000000000 with: nm! !

!MTSTheory class methodsFor: 'pitch'!
wavelengthToRGB: nm
	"可視スペクトル近似 (Bruton) で波長(nm)から Color を返す"
	| r g b a |
	r := 0.0. g := 0.0. b := 0.0.
	(nm >= 380 and: [nm < 440]) ifTrue: [r := (440 - nm) / 60.0. b := 1.0].
	(nm >= 440 and: [nm < 490]) ifTrue: [g := (nm - 440) / 50.0. b := 1.0].
	(nm >= 490 and: [nm < 510]) ifTrue: [g := 1.0. b := (510 - nm) / 20.0].
	(nm >= 510 and: [nm < 580]) ifTrue: [r := (nm - 510) / 70.0. g := 1.0].
	(nm >= 580 and: [nm < 645]) ifTrue: [r := 1.0. g := (645 - nm) / 65.0].
	(nm >= 645 and: [nm <= 780]) ifTrue: [r := 1.0].
	a := 1.0.
	nm > 700 ifTrue: [a := 0.3 + (0.7 * (780 - nm) / 80.0)].
	nm < 420 ifTrue: [a := 0.3 + (0.7 * (nm - 380) / 40.0)].
	^ Color r: ((r * a) min: 1.0 max: 0.0)
		g: ((g * a) min: 1.0 max: 0.0)
		b: ((b * a) min: 1.0 max: 0.0)! !

!MTSTheory class methodsFor: 'pitch'!
noteColor: midi
	^ self wavelengthToRGB: ((self midiToWavelength: midi) at: 3)! !

!MTSTheory class methodsFor: 'pitch'!
noteNames
	^ #('C' 'C#' 'D' 'D#' 'E' 'F' 'F#' 'G' 'G#' 'A' 'A#' 'B')! !

!MTSTheory class methodsFor: 'theory'!
natStep: pc
	"ピッチクラス -> 幹音ステップ (C=0..B=6)。黒鍵は nil"
	pc = 0 ifTrue: [^ 0]. pc = 2 ifTrue: [^ 1]. pc = 4 ifTrue: [^ 2].
	pc = 5 ifTrue: [^ 3]. pc = 7 ifTrue: [^ 4]. pc = 9 ifTrue: [^ 5].
	pc = 11 ifTrue: [^ 6].
	^ nil! !

!MTSTheory class methodsFor: 'theory'!
sigFlatSteps
	^ #(6 2 5 1 4 0 3)! !

!MTSTheory class methodsFor: 'theory'!
sigSharpSteps
	^ #(3 0 4 1 5 2 6)! !

!MTSTheory class methodsFor: 'theory'!
estimateKeySignature: midis
	"長調15種 (フラット7〜シャープ7) への当てはまりで調号を推定"
	| counts order best bestScore tonic steps score |
	midis isEmpty ifTrue: [^ 0].
	counts := Array new: 12 withAll: 0.
	midis do: [:m | | pc | pc := m \\ 12. counts at: pc + 1 put: (counts at: pc + 1) + 1].
	order := OrderedCollection with: 0.
	1 to: 7 do: [:k | order add: k negated. order add: k].
	best := 0. bestScore := -1.
	order do: [:sig |
		tonic := sig * 7 \\ 12.
		steps := #(0 2 4 5 7 9 11).
		score := 0.
		steps do: [:s | score := score + (counts at: (tonic + s \\ 12) + 1)].
		score > bestScore ifTrue: [bestScore := score. best := sig]].
	^ best! !

!MTSTheory class methodsFor: 'theory'!
idxToLetter: idx
	"ダイアトニック番号 -> MusixTeX 音名 (a=A3 の小文字 / 1オクターブ下は大文字)"
	| i |
	i := idx.
	[i < 19] whileTrue: [i := i + 7].
	[i > 51] whileTrue: [i := i - 7].
	i >= 26 ifTrue: [^ (Character value: 97 + i - 26) asString].
	^ (Character value: 65 + i - 19) asString! !

!MTSTheory class methodsFor: 'theory'!
pitchIndexOf: aCharacter
	"MusixTeX 音名 -> ダイアトニック番号 (c = C4 = 28)。不明は nil"
	| code |
	code := aCharacter asInteger.
	(code >= 97 and: [code <= 122]) ifTrue: [^ 26 + code - 97].
	(code >= 65 and: [code <= 90]) ifTrue: [^ 26 + code - 65 - 7].
	^ nil! !

!MTSTheory class methodsFor: 'theory'!
midiToTex: midi sig: sig
	"^ {音名文字列. 臨時記号(#sh/#fl/#na/nil). ダイアトニック番号}"
	| pc oct step alt idx def n acc |
	pc := midi \\ 12.
	oct := (midi // 12) - 1.
	step := self natStep: pc.
	alt := 0.
	step isNil ifTrue: [
		sig < 0
			ifTrue: [step := self natStep: (pc + 1) \\ 12. alt := -1]
			ifFalse: [step := self natStep: pc - 1. alt := 1]].
	idx := oct * 7 + step.
	def := 0.
	n := sig abs.
	1 to: n do: [:j |
		(sig < 0 and: [(self sigFlatSteps at: j) = step]) ifTrue: [def := -1].
		(sig > 0 and: [(self sigSharpSteps at: j) = step]) ifTrue: [def := 1]].
	acc := nil.
	alt = def ifFalse: [
		acc := alt = 1 ifTrue: [#sh] ifFalse: [alt = -1 ifTrue: [#fl] ifFalse: [#na]]].
	^ Array with: (self idxToLetter: idx) with: acc with: idx! !

!MTSTheory class methodsFor: 'theory'!
midiOfIdx: idx acc: acc sig: sig
	"ダイアトニック番号 + 臨時記号 + 調号 -> MIDI ノート番号"
	| oct step semis midi flat sharp applied |
	oct := idx // 7.
	step := idx \\ 7.
	semis := #(0 2 4 5 7 9 11).
	midi := 12 * (oct + 1) + (semis at: step + 1).
	flat := self sigFlatSteps. sharp := self sigSharpSteps.
	applied := 0.
	1 to: sig abs do: [:j |
		(sig < 0 and: [(flat at: j) = step]) ifTrue: [applied := -1].
		(sig > 0 and: [(sharp at: j) = step]) ifTrue: [applied := 1]].
	acc = #sh ifTrue: [applied := 1].
	acc = #fl ifTrue: [applied := -1].
	acc = #na ifTrue: [applied := 0].
	^ midi + applied! !

!MTSTheory class methodsFor: 'chords'!
chordTypes
	"五行コード線: 5 種のコード行"
	^ Array
		with: (Array with: 'M' with: #(0 4 7))
		with: (Array with: 'm' with: #(0 3 7))
		with: (Array with: '7' with: #(0 4 7 10))
		with: (Array with: 'M7' with: #(0 4 7 11))
		with: (Array with: 'sus4' with: #(0 5 7))! !

!MTSTheory class methodsFor: 'chords'!
chordMidisRoot: pc type: typeName octave: oct
	| root found |
	root := 12 * (oct + 1) + (pc \\ 12).
	found := self chordTypes detect: [:t | (t at: 1) = typeName] ifNone: [nil].
	found isNil ifTrue: [^ #()].
	^ (found at: 2) collect: [:iv | root + iv]! !

!MTSTheory class methodsFor: 'chords'!
chordFromPitchClasses: counts
	"ピッチクラス分布 -> 最も合うコード {rootPc. typeName} or nil"
	| best bestScore |
	best := nil. bestScore := 0.
	0 to: 11 do: [:root |
		self chordTypes do: [:t | | sc iv |
			iv := t at: 2.
			sc := 0.
			iv do: [:i | sc := sc + ((counts at: (root + i \\ 12) + 1) * (i = 0 ifTrue: [1.5] ifFalse: [1.0]))].
			sc := sc / iv size sqrt.
			sc > (bestScore + 0.000000001) ifTrue: [bestScore := sc. best := Array with: root with: (t at: 1)]]].
	^ bestScore > 0 ifTrue: [best] ifFalse: [nil]! !

!MTSTheory class methodsFor: 'chords'!
extractChordLine: events window: w
	"拍イベント列 -> 小節ごとのコード進行 {start. w. rootPc. type} の列"
	| endBeat chords counts t |
	endBeat := 0.
	events do: [:e | endBeat := endBeat max: (e at: 1) + (e at: 2)].
	chords := OrderedCollection new.
	t := 0.
	[t < (endBeat - 0.000001)] whileTrue: [
		counts := Array new: 12 withAll: 0.
		events do: [:e | | ov |
			ov := ((e at: 1) + (e at: 2) min: t + w) - ((e at: 1) max: t).
			ov > 0 ifTrue: [
				(e at: 3) do: [:m | counts at: (m \\ 12) + 1 put: (counts at: (m \\ 12) + 1) + ov]]].
		(self chordFromPitchClasses: counts) ifNotNil: [:c |
			chords add: (Array with: t with: w with: (c at: 1) with: (c at: 2))].
		t := t + w].
	^ chords! !

!MTSTheory class methodsFor: 'events'!
mergeEvents: a with: b
	"2つの拍イベント列 {start. dur. midis} を重ねる (同時発音は和音・最大6声)"
	| all merged |
	all := OrderedCollection new.
	a do: [:e | all add: (Array with: (e at: 1) with: (e at: 2) with: (e at: 3) asOrderedCollection)].
	b do: [:e | all add: (Array with: (e at: 1) with: (e at: 2) with: (e at: 3) asOrderedCollection)].
	all := all asSortedCollection: [:x :y | (x at: 1) <= (y at: 1)].
	merged := OrderedCollection new.
	all do: [:ev |
		(merged notEmpty and: [((ev at: 1) - (merged last at: 1)) abs < 0.125])
			ifTrue: [
				(ev at: 3) do: [:m |
					((merged last at: 3) includes: m) ifFalse: [
						(merged last at: 3) size < 6 ifTrue: [(merged last at: 3) add: m]]]]
			ifFalse: [merged add: ev]].
	^ merged collect: [:e | Array with: (e at: 1) with: (e at: 2) with: (e at: 3) asArray]! !

!MTSTheory class methodsFor: 'musixtex'!
durTokenFor: beats stemDown: down
	beats = 4 ifTrue: [^ '\wh'].
	beats = 2 ifTrue: [^ down ifTrue: ['\hl'] ifFalse: ['\hu']].
	beats = 1 ifTrue: [^ down ifTrue: ['\ql'] ifFalse: ['\qu']].
	^ down ifTrue: ['\cl'] ifFalse: ['\cu']! !

!MTSTheory class methodsFor: 'musixtex'!
snapDur: d
	| best bd |
	best := 0.5. bd := 999999999.
	#(0.5 1 2 4) do: [:c | | dist |
		dist := ((d max: 0.01) / c) ln abs.
		dist < bd ifTrue: [bd := dist. best := c]].
	^ best! !

!MTSTheory class methodsFor: 'musixtex'!
eventsToMusixTex: events signature: sigOrNil source: srcName
	"拍イベント列 {start. dur. midis} -> 完全な MusixTeX ドキュメント文字列"
	| all sig bars cur pos out |
	events isEmpty ifTrue: [^ nil].
	all := OrderedCollection new.
	events do: [:e | (e at: 3) do: [:m | all add: m]].
	sig := sigOrNil ifNil: [self estimateKeySignature: all].
	bars := OrderedCollection new.
	cur := OrderedCollection new.
	pos := 0.
	events do: [:ev | | start gap dur midis parts tok down |
		start := ((ev at: 1) * 2) rounded / 2.
		gap := ((start - pos) * 2) floor / 2.
		[gap >= 0.5] whileTrue: [ | rem piece |
			rem := 4 - (pos \\ 4).
			piece := gap min: rem.
			piece := piece >= 4 ifTrue: [4] ifFalse: [piece >= 2 ifTrue: [2] ifFalse: [piece >= 1 ifTrue: [1] ifFalse: [0.5]]].
			cur add: (piece = 4 ifTrue: ['\pause'] ifFalse: [piece = 2 ifTrue: ['\hpause'] ifFalse: [piece = 1 ifTrue: ['\qp'] ifFalse: ['\ds']]]).
			pos := pos + piece.
			gap := gap - piece.
			(pos \\ 4 = 0 and: [cur notEmpty]) ifTrue: [bars add: cur. cur := OrderedCollection new]].
		dur := self snapDur: (ev at: 2).
		[dur > (4 - (pos \\ 4)) + 0.000001] whileTrue: [
			dur := dur > 2 ifTrue: [2] ifFalse: [dur > 1 ifTrue: [1] ifFalse: [0.5]]].
		midis := (ev at: 3) asSortedCollection asArray.
		parts := OrderedCollection new.
		midis do: [:m | | p |
			p := self midiToTex: m sig: sig.
			(parts detect: [:q | (q at: 1) = (p at: 1) and: [(q at: 2) = (p at: 2)]] ifNone: [nil]) isNil
				ifTrue: [parts add: p]].
		down := (parts last at: 3) >= 34.
		tok := WriteStream on: String new.
		parts doWithIndex: [:p :i |
			(p at: 2) ifNotNil: [:acc | tok nextPutAll: '\', acc asString, ' ', (p at: 1)].
			i < parts size
				ifTrue: [tok nextPutAll: '\zq{', (p at: 1), '}']
				ifFalse: [tok nextPutAll: (self durTokenFor: dur stemDown: down), '{', (p at: 1), '}']].
		cur add: tok contents.
		pos := pos + dur.
		(pos \\ 4 = 0 and: [cur notEmpty]) ifTrue: [bars add: cur. cur := OrderedCollection new]].
	cur notEmpty ifTrue: [bars add: cur].
	out := WriteStream on: String new.
	out nextPutAll: '% MusicTeX Studio (Squeak edition): ', srcName; cr.
	out nextPutAll: '\input musixtex'; cr.
	out nextPutAll: '\generalsignature{', sig printString, '}'; cr.
	out nextPutAll: '\generalmeter{\meterfrac44}'; cr.
	out nextPutAll: '\parindent0pt'; cr.
	out nextPutAll: '\startpiece'; cr.
	bars doWithIndex: [:bar :i |
		i > 1 ifTrue: [out nextPutAll: '\bar'; cr].
		out nextPutAll: '\NOtes'.
		bar do: [:t | out nextPutAll: t].
		out nextPutAll: '\en'; cr].
	out nextPutAll: '\endpiece'; cr.
	out nextPutAll: '\end'; cr.
	^ out contents! !

!MTSTheory class methodsFor: 'musixtex'!
parseMusixTeX: aString
	"MusixTeX サブセットを解析。^ {#signature->n. #events->列} の Dictionary
	 イベント: {#note. durSym. pitches({idx. acc})} / {#rest. durSym} / {#bar}"
	| s result events inGroup pendAcc chord sig ch cmd |
	s := ReadStream on: aString.
	events := OrderedCollection new.
	inGroup := false. pendAcc := nil. sig := 0.
	chord := OrderedCollection new.
	[s atEnd] whileFalse: [
		ch := s next.
		ch = $% ifTrue: [[s atEnd or: [ | cc | cc := s next. cc = Character cr or: [cc = Character lf]]] whileFalse].
		ch = $\ ifTrue: [
			cmd := WriteStream on: String new.
			[s atEnd not and: [s peek isLetter]] whileTrue: [cmd nextPut: s next].
			cmd := cmd contents.
			cmd = 'generalsignature' ifTrue: [ | neg num |
				[s atEnd not and: [s peek isLetter not and: [s peek isDigit not and: [s peek ~= $-]]]] whileTrue: [s next].
				neg := false.
				(s atEnd not and: [s peek = $-]) ifTrue: [s next. neg := true].
				num := 0.
				[s atEnd not and: [s peek isDigit]] whileTrue: [num := num * 10 + s next digitValue].
				sig := neg ifTrue: [num negated] ifFalse: [num]].
			((cmd = 'NOtes') or: [(cmd = 'Notes') or: [(cmd = 'notes') or: [(cmd = 'NOTes') or: [cmd = 'NOTEs']]]])
				ifTrue: [inGroup := true].
			((cmd = 'en') or: [cmd = 'enotes']) ifTrue: [inGroup := false. chord := OrderedCollection new. pendAcc := nil].
			cmd = 'bar' ifTrue: [events add: (Array with: #bar)].
			inGroup ifTrue: [
				((cmd = 'sh') or: [(cmd = 'fl') or: [cmd = 'na']]) ifTrue: [pendAcc := cmd asSymbol].
				cmd = 'qp' ifTrue: [events add: (Array with: #rest with: #q)].
				cmd = 'hpause' ifTrue: [events add: (Array with: #rest with: #h)].
				cmd = 'pause' ifTrue: [events add: (Array with: #rest with: #w)].
				cmd = 'ds' ifTrue: [events add: (Array with: #rest with: #c)].
				((cmd = 'zq') or: [cmd = 'zh']) ifTrue: [
					(self readPitchArg: s) do: [:idx |
						chord add: (Array with: idx with: pendAcc). pendAcc := nil]].
				(#('qu' 'ql' 'cu' 'cl' 'hu' 'hl' 'wh') includes: cmd) ifTrue: [ | durSym |
					durSym := (cmd = 'wh') ifTrue: [#w] ifFalse: [
						(cmd first = $c) ifTrue: [#c] ifFalse: [(cmd first = $h) ifTrue: [#h] ifFalse: [#q]]].
					(self readPitchArg: s) do: [:idx | | pitches |
						pitches := chord copy.
						pitches add: (Array with: idx with: pendAcc).
						pendAcc := nil. chord := OrderedCollection new.
						events add: (Array with: #note with: durSym with: pitches asArray)]]]]].
	result := Dictionary new.
	result at: #signature put: sig.
	result at: #events put: events.
	^ result! !

!MTSTheory class methodsFor: 'musixtex'!
readPitchArg: aStream
	"音名引数 (1文字 または {abc...}) を読み、ダイアトニック番号の列を返す"
	| out |
	out := OrderedCollection new.
	[aStream atEnd not and: [aStream peek = Character space]] whileTrue: [aStream next].
	aStream atEnd ifTrue: [^ out].
	aStream peek = ${
		ifTrue: [
			aStream next.
			[aStream atEnd not and: [aStream peek ~= $}]] whileTrue: [ | c |
				c := aStream next.
				(self pitchIndexOf: c) ifNotNil: [:idx | out add: idx]].
			aStream atEnd ifFalse: [aStream next]]
		ifFalse: [
			(self pitchIndexOf: aStream peek) ifNotNil: [:idx | out add: idx. aStream next]].
	^ out! !

!MTSTheory class methodsFor: 'musixtex'!
beatEventsFrom: parsed
	"parseMusixTeX: の結果 -> 拍イベント列 {start. dur. midis}"
	| sig out pos durB |
	sig := parsed at: #signature.
	out := OrderedCollection new.
	pos := 0.
	(parsed at: #events) do: [:ev |
		(ev at: 1) = #bar ifFalse: [
			durB := self beatsOfDurSym: (ev at: 2).
			(ev at: 1) = #note ifTrue: [ | midis |
				midis := (ev at: 3) collect: [:p | self midiOfIdx: (p at: 1) acc: (p at: 2) sig: sig].
				out add: (Array with: pos with: durB with: midis asArray)].
			pos := pos + durB]].
	^ out! !

!MTSTheory class methodsFor: 'musixtex'!
beatsOfDurSym: sym
	sym = #w ifTrue: [^ 4].
	sym = #h ifTrue: [^ 2].
	sym = #c ifTrue: [^ 0.5].
	^ 1! !

!MTSTheory class methodsFor: 'templates'!
templates
	"octave74 レポートの題材テンプレート {名前. MusixTeX ソース}"
	| nl |
	nl := String with: Character cr.
	^ Array
		with: (Array with: 'B-flat major scale (octave74)'
			with: '\input musixtex', nl, '\generalsignature{-2}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl, '\NOtes\qu{bcde}\en', nl, '\bar', nl,
				'\NOtes\qu{fghi}\en', nl, '\bar', nl, '\NOtes\qu{ihgf}\en', nl, '\bar', nl,
				'\NOtes\qu{edcb}\en', nl, '\endpiece', nl, '\end', nl)
		with: (Array with: 'E-flat major scale (octave74)'
			with: '\input musixtex', nl, '\generalsignature{-3}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl, '\NOtes\qu{efgh}\en', nl, '\bar', nl,
				'\NOtes\qu{ijkl}\en', nl, '\bar', nl, '\NOtes\qu{lkji}\en', nl, '\bar', nl,
				'\NOtes\qu{hgfe}\en', nl, '\endpiece', nl, '\end', nl)
		with: (Array with: 'G and A chords (octave74)'
			with: '\input musixtex', nl, '\generalsignature{0}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl,
				'\NOtes\zq{g}\zq{i}\qu{k}\zq{h}\zq{j}\qu{l}\zq{g}\zq{i}\hu{k}\en', nl, '\bar', nl,
				'\NOtes\sh f\zq{f}\zq{h}\qu{j}\zq{g}\zq{i}\qu{k}\zq{h}\zq{j}\hu{l}\en', nl,
				'\endpiece', nl, '\end', nl)
		with: (Array with: 'Two scales = two octaves (octave74)'
			with: '\input musixtex', nl, '\generalsignature{0}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl, '\NOtes\qu{cdef}\en', nl, '\bar', nl,
				'\NOtes\qu{ghij}\en', nl, '\bar', nl, '\NOtes\qu{jklm}\en', nl, '\bar', nl,
				'\NOtes\qu{nopq}\en', nl, '\endpiece', nl, '\end', nl)
		with: (Array with: 'HANON style exercise (octave74)'
			with: '\input musixtex', nl, '\generalsignature{0}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl,
				'\NOtes\cu{c}\cu{e}\cu{f}\cu{g}\cu{h}\cu{g}\cu{f}\cu{e}\en', nl, '\bar', nl,
				'\NOtes\cu{d}\cu{f}\cu{g}\cu{h}\cu{i}\cu{h}\cu{g}\cu{f}\en', nl,
				'\endpiece', nl, '\end', nl)
		with: (Array with: 'Empty score'
			with: '\input musixtex', nl, '\generalsignature{0}', nl, '\generalmeter{\meterfrac44}', nl,
				'\parindent0pt', nl, '\startpiece', nl, '\NOtes\qu{c}\qu{d}\qu{e}\qu{f}\en', nl,
				'\endpiece', nl, '\end', nl)! !

Object subclass: #MTSSynth
	instanceVariableNames: ''
	classVariableNames: 'PlayProcess'
	poolDictionaries: ''
	category: 'MusicTeXStudio'!

!MTSSynth class methodsFor: 'presets'!
instrumentNames
	^ #('Piano' 'Organ' 'Violin' 'Cello' 'Flute' 'Trumpet' 'Clarinet' 'Guitar'
	    'Harp' 'MusicBox' 'Bell' 'Marimba' 'Bass' 'Sine' 'Triangle' 'Saw' 'Square')! !

!MTSSynth class methodsFor: 'presets'!
presetNamed: aName
	"楽器名 -> スペクトルコード (倍音1〜8) + ADSR の Dictionary"
	| d h a dec sus r |
	h := #(1 0.45 0.22 0.12 0.07 0.04 0.02 0.01). a := 0.008. dec := 0.25. sus := 0.35. r := 0.35.
	aName = 'Organ' ifTrue: [h := #(1 0.6 0.3 0.5 0.1 0.2 0.05 0.3). a := 0.03. dec := 0.05. sus := 0.9. r := 0.15].
	aName = 'Violin' ifTrue: [h := #(1 0.7 0.5 0.4 0.3 0.25 0.2 0.15). a := 0.12. dec := 0.1. sus := 0.8. r := 0.25].
	aName = 'Cello' ifTrue: [h := #(1 0.8 0.5 0.35 0.2 0.15 0.1 0.05). a := 0.1. dec := 0.1. sus := 0.8. r := 0.3].
	aName = 'Flute' ifTrue: [h := #(1 0.25 0.08 0.04 0.02 0.01 0 0). a := 0.07. dec := 0.05. sus := 0.85. r := 0.2].
	aName = 'Trumpet' ifTrue: [h := #(1 0.9 0.8 0.7 0.55 0.4 0.3 0.2). a := 0.04. dec := 0.08. sus := 0.8. r := 0.15].
	aName = 'Clarinet' ifTrue: [h := #(1 0.05 0.6 0.05 0.35 0.05 0.2 0.05). a := 0.06. dec := 0.05. sus := 0.85. r := 0.2].
	aName = 'Guitar' ifTrue: [h := #(1 0.5 0.33 0.2 0.12 0.08 0.05 0.03). a := 0.005. dec := 0.4. sus := 0.15. r := 0.3].
	aName = 'Harp' ifTrue: [h := #(1 0.3 0.15 0.08 0.04 0.02 0.01 0). a := 0.004. dec := 0.5. sus := 0.1. r := 0.4].
	aName = 'MusicBox' ifTrue: [h := #(1 0 0.15 0 0.4 0 0.05 0). a := 0.003. dec := 0.6. sus := 0.05. r := 0.5].
	aName = 'Bell' ifTrue: [h := #(1 0 0.5 0 0 0.7 0 0.3). a := 0.003. dec := 0.8. sus := 0.1. r := 0.8].
	aName = 'Marimba' ifTrue: [h := #(1 0 0 0.5 0 0 0 0.15). a := 0.003. dec := 0.3. sus := 0.05. r := 0.2].
	aName = 'Bass' ifTrue: [h := #(1 0.6 0.3 0.15 0.05 0.02 0 0). a := 0.01. dec := 0.2. sus := 0.5. r := 0.25].
	aName = 'Sine' ifTrue: [h := #(1 0 0 0 0 0 0 0). a := 0.015. dec := 0.05. sus := 0.9. r := 0.3].
	aName = 'Triangle' ifTrue: [h := #(1 0 0.111 0 0.04 0 0.02 0). a := 0.015. dec := 0.05. sus := 0.9. r := 0.3].
	aName = 'Saw' ifTrue: [h := #(1 0.5 0.333 0.25 0.2 0.167 0.143 0.125). a := 0.015. dec := 0.05. sus := 0.9. r := 0.3].
	aName = 'Square' ifTrue: [h := #(1 0 0.333 0 0.2 0 0.143 0). a := 0.015. dec := 0.05. sus := 0.9. r := 0.3].
	d := Dictionary new.
	d at: #harmonics put: h.
	d at: #attack put: a. d at: #decay put: dec. d at: #sustain put: sus. d at: #release put: r.
	^ d! !

!MTSSynth class methodsFor: 'playing'!
soundForMidi: midi dur: secs loudness: loud patch: patch
	"加算合成: 倍音スペクトル (スペクトルコード) + ADSR で 1 音を作る"
	| freq mix harms total |
	freq := MTSTheory midiToFreq: midi.
	harms := patch at: #harmonics.
	total := 0.
	harms do: [:v | total := total + v].
	total <= 0 ifTrue: [total := 1].
	mix := MixedSound new.
	harms doWithIndex: [:amp :k |
		(amp > 0 and: [freq * k < 10000]) ifTrue: [ | snd |
			snd := FMSound new.
			snd setPitch: freq * k dur: secs loudness: loud * amp / total.
			[snd addEnvelope: (VolumeEnvelope
				points: (Array
					with: 0 @ 0.0
					with: ((patch at: #attack) * 1000) rounded @ 1.0
					with: (((patch at: #attack) + (patch at: #decay)) * 1000) rounded @ (patch at: #sustain)
					with: ((secs - (patch at: #release) max: (patch at: #attack) + (patch at: #decay)) * 1000) rounded @ (patch at: #sustain)
					with: (secs * 1000) rounded @ 0.0)
				loopStart: 4 loopEnd: 4)] on: Error do: [:e | ].
			mix add: snd pan: 0.5]].
	mix sounds isEmpty ifTrue: [ | snd |
		snd := FMSound new.
		snd setPitch: freq dur: secs loudness: loud.
		mix add: snd pan: 0.5].
	^ mix! !

!MTSSynth class methodsFor: 'playing'!
playMidi: midi dur: secs patch: patch
	(self soundForMidi: midi dur: secs loudness: 0.3 patch: patch) play! !

!MTSSynth class methodsFor: 'playing'!
playMidis: midis dur: secs patch: patch
	midis do: [:m |
		(self soundForMidi: m dur: secs loudness: 0.25 / midis size sqrt patch: patch) play]! !

!MTSSynth class methodsFor: 'playing'!
stop
	PlayProcess ifNotNil: [PlayProcess terminate. PlayProcess := nil]! !

!MTSSynth class methodsFor: 'playing'!
playEvents: events tempo: bpm patch: patch onEvent: aBlockOrNil
	"拍イベント列をシンセで順に演奏 (バックグラウンドプロセス)"
	| beat |
	self stop.
	beat := 60.0 / bpm.
	PlayProcess := [
		events doWithIndex: [:ev :i | | secs |
			aBlockOrNil ifNotNil: [aBlockOrNil value: i].
			secs := (ev at: 2) * beat.
			self playMidis: (ev at: 3) dur: secs * 0.95 patch: patch.
			(Delay forSeconds: secs) wait].
		aBlockOrNil ifNotNil: [aBlockOrNil value: 0].
		PlayProcess := nil] newProcess.
	PlayProcess priority: Processor userBackgroundPriority.
	PlayProcess resume! !

!MTSSynth class methodsFor: 'import'!
midiEventsFromFileNamed: path
	"標準 MIDI ファイル -> 拍イベント列 (Squeak 標準の MIDIFileReader を使用)"
	| score div notes events |
	score := MIDIFileReader scoreFromFileNamed: path.
	div := [score ticksPerQuarterNote] on: Error do: [:e | 480].
	(div isNil or: [div <= 0]) ifTrue: [div := 480].
	notes := OrderedCollection new.
	score tracks do: [:trk |
		trk do: [:ev |
			(ev respondsTo: #midiKey) ifTrue: [
				notes add: (Array with: ev time / div with: ((ev duration max: 1) / div) with: ev midiKey)]]].
	notes := notes asSortedCollection: [:x :y | (x at: 1) <= (y at: 1)].
	events := OrderedCollection new.
	notes do: [:n |
		(events notEmpty and: [((n at: 1) - (events last at: 1)) abs < 0.125])
			ifTrue: [
				((events last at: 3) includes: (n at: 3)) ifFalse: [
					(events last at: 3) size < 6 ifTrue: [(events last at: 3) add: (n at: 3)]]]
			ifFalse: [
				events add: (Array with: (n at: 1) asFloat with: (n at: 2) asFloat
					with: (OrderedCollection with: (n at: 3)))]].
	^ events collect: [:e | Array with: (e at: 1) with: (e at: 2) with: (e at: 3) asArray]! !

!MTSSynth class methodsFor: 'import'!
detectPitchIn: buf from: start size: win rate: rate
	"自己相関ピッチ検出。^ MIDI ノート番号 (Float) or 0"
	| energy minLag maxLag bestR bestLag sum r freq |
	energy := 0.0.
	0 to: win - 1 do: [:i | | v | v := (buf at: start + i) / 32768.0. energy := energy + (v * v)].
	(energy / win) sqrt < 0.01 ifTrue: [^ 0].
	minLag := (rate / 1000) truncated max: 2.
	maxLag := (rate / 60) truncated min: win - 2.
	bestR := 0.3. bestLag := -1.
	minLag to: maxLag do: [:lag |
		sum := 0.0.
		0 to: win - 1 - lag do: [:i |
			sum := sum + ((buf at: start + i) / 32768.0 * ((buf at: start + i + lag) / 32768.0))].
		r := sum / energy.
		r > bestR ifTrue: [bestR := r. bestLag := lag]].
	bestLag < 0 ifTrue: [^ 0].
	freq := rate / bestLag.
	^ 69 + (12 * ((freq / 440.0) ln / 2 ln))! !

!MTSSynth class methodsFor: 'import'!
wavEventsFromFileNamed: path
	"WAV ファイル -> 単旋律の拍イベント列 (自己相関ピッチ検出)"
	| snd buf rate deci win hop frames segs curMidi curStart durs beatSec |
	snd := SampledSound fromWaveFileNamed: path.
	buf := snd samples.
	rate := snd originalSamplingRate.
	deci := (rate / 11025) truncated max: 1.
	rate := rate / deci.
	win := 1024. hop := 256.
	frames := OrderedCollection new.
	1 to: ((buf size / deci) truncated - win - 1) by: hop do: [:i | | frame |
		frame := Array new: win.
		1 to: win do: [:k | frame at: k put: (buf at: (i + k - 1) * deci min: buf size)].
		frames add: (self detectPitchIn: frame from: 1 size: win rate: rate)].
	segs := OrderedCollection new.
	curMidi := 0. curStart := 1.
	frames doWithIndex: [:f :i | | m |
		m := f > 0 ifTrue: [f rounded] ifFalse: [0].
		m = curMidi ifFalse: [
			(curMidi > 0 and: [i - curStart >= 4]) ifTrue: [
				segs add: (Array with: curStart with: i - curStart with: curMidi)].
			curMidi := m. curStart := i]].
	(curMidi > 0 and: [frames size - curStart >= 4]) ifTrue: [
		segs add: (Array with: curStart with: frames size - curStart with: curMidi)].
	segs isEmpty ifTrue: [^ OrderedCollection new].
	durs := (segs collect: [:s | s at: 2]) asSortedCollection asArray.
	beatSec := (durs at: (durs size + 1) // 2) * hop / rate.
	beatSec := beatSec min: 1.2 max: 0.18.
	^ segs collect: [:s |
		Array with: (s at: 1) * hop / rate / beatSec
			with: ((s at: 2) * hop / rate / beatSec)
			with: (Array with: (s at: 3))]! !

Morph subclass: #MTSSpectralMorph
	instanceVariableNames: 'app'
	classVariableNames: ''
	poolDictionaries: ''
	category: 'MusicTeXStudio'!

!MTSSpectralMorph methodsFor: 'accessing'!
app: anApp
	app := anApp! !

!MTSSpectralMorph methodsFor: 'drawing'!
drawOn: aCanvas
	"モーツァルト・ビジョン: 楽譜を色の波長帯の映像として描く"
	| b events lo hi span pxPerBeat total rulerH areaH bandH |
	b := self bounds.
	aCanvas fillRectangle: b color: (Color r: 0.02 g: 0.03 b: 0.05).
	rulerH := 10.
	0 to: b width - 1 by: 2 do: [:x | | nm |
		nm := 380 + (400 * x / b width).
		aCanvas fillRectangle: ((b left + x) @ (b bottom - rulerH) extent: 2 @ rulerH)
			color: ((MTSTheory wavelengthToRGB: nm) alpha: 0.55)].
	app ifNil: [^ self].
	events := app beatEvents.
	events isEmpty ifTrue: [^ self].
	total := 1.
	events do: [:e | total := total max: (e at: 1) + (e at: 2)].
	pxPerBeat := ((b width - 8) / total) min: 60 max: 8.
	lo := 200. hi := 0.
	events do: [:e | (e at: 3) do: [:m | lo := lo min: m. hi := hi max: m]].
	lo := lo - 2. hi := hi + 2.
	span := (hi - lo) max: 8.
	areaH := b height - rulerH - 8.
	bandH := (areaH / span * 1.6) min: 12 max: 4.
	events doWithIndex: [:e :i | | x w |
		x := b left + 4 + ((e at: 1) * pxPerBeat).
		w := ((e at: 2) * pxPerBeat - 2) max: 3.
		(e at: 3) do: [:m | | y c |
			y := b top + 4 + ((1 - ((m - lo) / span)) * (areaH - bandH)).
			c := MTSTheory noteColor: m.
			aCanvas fillRectangle: (x rounded @ y rounded extent: w rounded @ bandH rounded) color: c.
			i = app playingIndex ifTrue: [
				aCanvas frameRectangle: ((x rounded - 1) @ (y rounded - 1) extent: (w rounded + 2) @ (bandH rounded + 2))
					width: 1 color: Color white]]]! !

Morph subclass: #MTSStaffMorph
	instanceVariableNames: 'app'
	classVariableNames: ''
	poolDictionaries: ''
	category: 'MusicTeXStudio'!

!MTSStaffMorph methodsFor: 'accessing'!
app: anApp
	app := anApp! !

!MTSStaffMorph methodsFor: 'drawing'!
drawOn: aCanvas
	"五線譜の簡易プレビュー (ト音記号・調号・音符・小節線)"
	| b parsed sig events step topY x noteW lineCol perLine count line |
	b := self bounds.
	aCanvas fillRectangle: b color: (Color r: 0.96 g: 0.95 b: 0.92).
	app ifNil: [^ self].
	parsed := app parsed.
	parsed ifNil: [^ self].
	sig := parsed at: #signature.
	events := parsed at: #events.
	step := 4. noteW := 26.
	lineCol := Color r: 0.2 g: 0.2 b: 0.2.
	topY := b top + 24.
	x := b left + 56 + (sig abs * 9).
	perLine := ((b width - 80) / noteW) truncated max: 4.
	count := 0. line := 0.
	self drawStaffOn: aCanvas at: topY in: b sig: sig color: lineCol.
	events do: [:ev |
		((ev at: 1) = #bar)
			ifTrue: [
				aCanvas fillRectangle: ((x - 8) @ topY extent: 1 @ (8 * step)) color: lineCol]
			ifFalse: [
				count >= perLine ifTrue: [
					line := line + 1. count := 0.
					topY := topY + 110.
					topY + 40 > b bottom ifTrue: [^ self].
					self drawStaffOn: aCanvas at: topY in: b sig: sig color: lineCol.
					x := b left + 56 + (sig abs * 9)].
				(ev at: 1) = #note ifTrue: [
					(ev at: 3) do: [:p | | idx y |
						idx := p at: 1.
						y := topY + (8 * step) - ((idx - 30) * step).
						idx <= 28 ifTrue: [
							28 to: idx by: -2 do: [:li |
								aCanvas fillRectangle: ((x - 7) @ (topY + (8 * step) - ((li - 30) * step)) extent: 14 @ 1) color: lineCol]].
						idx >= 40 ifTrue: [
							40 to: idx by: 2 do: [:li |
								aCanvas fillRectangle: ((x - 7) @ (topY + (8 * step) - ((li - 30) * step)) extent: 14 @ 1) color: lineCol]].
						(p at: 2) = #sh ifTrue: [aCanvas drawString: '#' at: (x - 15) @ (y - 8) font: nil color: lineCol].
						(p at: 2) = #fl ifTrue: [aCanvas drawString: 'b' at: (x - 15) @ (y - 8) font: nil color: lineCol].
						(p at: 2) = #na ifTrue: [aCanvas drawString: 'n' at: (x - 15) @ (y - 8) font: nil color: lineCol].
						((ev at: 2) = #h or: [(ev at: 2) = #w])
							ifTrue: [
								aCanvas fillOval: ((x - 5) @ (y - 4) extent: 10 @ 8) color: lineCol.
								aCanvas fillOval: ((x - 3) @ (y - 2) extent: 6 @ 4) color: (Color r: 0.96 g: 0.95 b: 0.92)]
							ifFalse: [aCanvas fillOval: ((x - 5) @ (y - 4) extent: 10 @ 8) color: lineCol].
						(ev at: 2) = #w ifFalse: [
							aCanvas fillRectangle: ((x + 4) @ (y - 26) extent: 1 @ 26) color: lineCol]]].
				(ev at: 1) = #rest ifTrue: [
					aCanvas fillRectangle: ((x - 4) @ (topY + (3 * step)) extent: 8 @ 4) color: lineCol].
				x := x + noteW.
				count := count + 1]]! !

!MTSStaffMorph methodsFor: 'drawing'!
drawStaffOn: aCanvas at: topY in: b sig: sig color: lineCol
	| step |
	step := 4.
	0 to: 4 do: [:j |
		aCanvas fillRectangle: ((b left + 8) @ (topY + (j * 2 * step)) extent: (b width - 16) @ 1) color: lineCol].
	aCanvas drawString: 'G' at: (b left + 12) @ (topY + 4) font: nil color: lineCol.
	1 to: sig abs do: [:k |
		aCanvas drawString: (sig < 0 ifTrue: ['b'] ifFalse: ['#'])
			at: (b left + 30 + (k * 9)) @ (topY + 2) font: nil color: lineCol]! !

Morph subclass: #MTSApp
	instanceVariableNames: 'sourceEditor lcd visionInfo spectral staff patch patchName playingIndex parsed beatEventsCache importOverlay instButtons tplButtons harmSliders'
	classVariableNames: ''
	poolDictionaries: ''
	category: 'MusicTeXStudio'!

!MTSApp class methodsFor: 'instance creation'!
open
	"MusicTeX Studio (Squeak edition) を開く"
	| app |
	app := self new.
	app position: 40 @ 40.
	app openInWorld.
	^ app! !

!MTSApp methodsFor: 'initialization'!
initialize
	super initialize.
	self extent: 1240 @ 820.
	self color: (Color r: 0.16 g: 0.16 b: 0.17).
	self clipSubmorphs: true.
	patchName := 'Piano'.
	patch := MTSSynth presetNamed: patchName.
	playingIndex := 0.
	importOverlay := false.
	self buildTitlebar.
	self buildToolbar.
	self buildLibrary.
	self buildCenter.
	self buildInspector.
	self setSource: ((MTSTheory templates at: 1) at: 2).
	self refresh! !

!MTSApp methodsFor: 'building'!
mkButton: label action: sel at: pos extent: ext color: col
	| b |
	b := SimpleButtonMorph new.
	b label: label.
	b target: self.
	b actionSelector: sel.
	b color: col.
	b borderWidth: 0.
	b position: self position + pos.
	b extent: ext.
	self addMorph: b.
	^ b! !

!MTSApp methodsFor: 'building'!
mkLabel: text at: pos color: col
	| s |
	s := StringMorph contents: text.
	s color: col.
	s position: self position + pos.
	self addMorph: s.
	^ s! !

!MTSApp methodsFor: 'building'!
buildTitlebar
	| bar |
	bar := BorderedMorph new.
	bar color: (Color r: 0.22 g: 0.22 b: 0.24).
	bar borderWidth: 0.
	bar position: self position.
	bar extent: 1240 @ 30.
	self addMorph: bar.
	#(red yellow green) doWithIndex: [:c :i | | dot |
		dot := EllipseMorph new.
		dot color: (c = #red ifTrue: [Color r: 1 g: 0.37 b: 0.34]
			ifFalse: [c = #yellow ifTrue: [Color r: 1 g: 0.74 b: 0.18] ifFalse: [Color r: 0.16 g: 0.78 b: 0.25]]).
		dot borderWidth: 0.
		dot extent: 12 @ 12.
		dot position: self position + ((8 + (i * 20)) @ 9).
		c = #red ifTrue: [dot on: #mouseDown send: #delete to: self].
		self addMorph: dot].
	self mkLabel: 'MusicTeX Studio - Spectral Code (Squeak edition)' at: 470 @ 7
		color: (Color r: 0.7 g: 0.7 b: 0.72)! !

!MTSApp methodsFor: 'building'!
buildToolbar
	| bar btnCol lcdBox |
	bar := BorderedMorph new.
	bar color: (Color r: 0.2 g: 0.2 b: 0.22).
	bar borderWidth: 0.
	bar position: self position + (0 @ 30).
	bar extent: 1240 @ 46.
	self addMorph: bar.
	btnCol := Color r: 0.27 g: 0.27 b: 0.29.
	self mkButton: 'MIDI取込' action: #doImportMidi at: 10 @ 40 extent: 74 @ 26 color: btnCol.
	self mkButton: 'WAV取込' action: #doImportWav at: 90 @ 40 extent: 74 @ 26 color: btnCol.
	self mkButton: '置き換え' action: #toggleImportMode at: 170 @ 40 extent: 74 @ 26 color: btnCol.
	self mkButton: 'Stop' action: #doStop at: 268 @ 40 extent: 50 @ 26 color: btnCol.
	self mkButton: 'Play' action: #doPlay at: 322 @ 40 extent: 50 @ 26 color: (Color r: 0.16 g: 0.5 b: 0.25).
	lcdBox := BorderedMorph new.
	lcdBox color: (Color r: 0.1 g: 0.13 b: 0.1).
	lcdBox borderColor: Color black.
	lcdBox borderWidth: 1.
	lcdBox position: self position + (390 @ 36).
	lcdBox extent: 440 @ 34.
	self addMorph: lcdBox.
	lcd := self mkLabel: 'MusicTeX Studio' at: 400 @ 44 color: (Color r: 0.72 g: 0.88 b: 0.55).
	self mkButton: 'コード化' action: #doChordify at: 846 @ 40 extent: 70 @ 26 color: btnCol.
	self mkButton: '更新' action: #doRefresh at: 920 @ 40 extent: 50 @ 26 color: btnCol.
	self mkButton: '.tex保存' action: #doSaveTex at: 974 @ 40 extent: 70 @ 26 color: btnCol.
	self mkButton: '試聴音' action: #doTestTone at: 1048 @ 40 extent: 58 @ 26 color: btnCol! !

!MTSApp methodsFor: 'building'!
buildLibrary
	| y |
	self mkLabel: 'ライブラリ' at: 12 @ 82 color: (Color r: 0.6 g: 0.6 b: 0.65).
	self mkLabel: '楽器 (スペクトルコード)' at: 12 @ 100 color: (Color r: 0.45 g: 0.45 b: 0.5).
	y := 118.
	instButtons := OrderedCollection new.
	MTSSynth instrumentNames do: [:nm | | b |
		b := self mkButton: nm action: #selectInstrument: at: 10 @ y extent: 160 @ 22
			color: (nm = patchName
				ifTrue: [Color r: 0.04 g: 0.52 b: 1.0]
				ifFalse: [Color r: 0.2 g: 0.2 b: 0.22]).
		b arguments: (Array with: nm).
		instButtons add: b.
		y := y + 24].
	self mkLabel: 'テンプレート (octave74)' at: 12 @ (y + 6) color: (Color r: 0.45 g: 0.45 b: 0.5).
	y := y + 24.
	tplButtons := OrderedCollection new.
	MTSTheory templates doWithIndex: [:t :i | | b |
		b := self mkButton: (t at: 1) action: #selectTemplate: at: 10 @ y extent: 160 @ 22
			color: (Color r: 0.2 g: 0.2 b: 0.22).
		b arguments: (Array with: i).
		tplButtons add: b.
		y := y + 24]! !

!MTSApp methodsFor: 'building'!
buildCenter
	| edBox |
	self mkLabel: 'モーツァルト・ビジョン (音 = 光の波長帯)' at: 190 @ 82
		color: (Color r: 0.69 g: 0.54 b: 0.88).
	visionInfo := self mkLabel: '' at: 640 @ 82 color: (Color r: 0.55 g: 0.55 b: 0.6).
	spectral := MTSSpectralMorph new.
	spectral app: self.
	spectral position: self position + (188 @ 100).
	spectral extent: 770 @ 170.
	self addMorph: spectral.
	self mkLabel: '楽譜 - ライブプレビュー (印刷は texlive-music: musixtex -p score.tex)'
		at: 190 @ 276 color: (Color r: 0.25 g: 0.72 b: 0.75).
	staff := MTSStaffMorph new.
	staff app: self.
	staff position: self position + (188 @ 294).
	staff extent: 770 @ 250.
	self addMorph: staff.
	self mkLabel: 'MusixTeX エディタ (編集したら 更新 を押す)' at: 190 @ 550
		color: (Color r: 0.6 g: 0.6 b: 0.65).
	edBox := BorderedMorph new.
	edBox color: (Color r: 0.09 g: 0.09 b: 0.1).
	edBox borderColor: (Color r: 0.23 g: 0.23 b: 0.25).
	edBox borderWidth: 1.
	edBox position: self position + (188 @ 568).
	edBox extent: 770 @ 244.
	edBox clipSubmorphs: true.
	self addMorph: edBox.
	sourceEditor := TextMorph new.
	sourceEditor contents: ''.
	sourceEditor position: self position + (194 @ 572).
	sourceEditor extent: 758 @ 236.
	[sourceEditor textColor: (Color r: 0.9 g: 0.9 b: 0.92)] on: Error do: [:e | ].
	self addMorph: sourceEditor! !

!MTSApp methodsFor: 'building'!
buildInspector
	| y |
	self mkLabel: 'インスペクタ' at: 972 @ 82 color: (Color r: 0.6 g: 0.6 b: 0.65).
	self mkLabel: 'スペクトルコード (倍音1-8)' at: 972 @ 100 color: (Color r: 0.45 g: 0.45 b: 0.5).
	y := 118.
	harmSliders := OrderedCollection new.
	1 to: 8 do: [:k | | s |
		self mkLabel: k printString at: 972 @ (y + 2) color: (Color r: 0.45 g: 0.45 b: 0.5).
		s := SimpleSliderMorph new.
		s color: (Color r: 0.04 g: 0.52 b: 1.0).
		s extent: 220 @ 14.
		s position: self position + (990 @ y).
		s target: self.
		s actionSelector: ('harm', k printString, ':') asSymbol.
		s setValue: ((patch at: #harmonics) at: k).
		self addMorph: s.
		harmSliders add: s.
		y := y + 20].
	self mkLabel: '五行コード線 (M m 7 M7 sus4 x 12)' at: 972 @ (y + 8)
		color: (Color r: 0.45 g: 0.45 b: 0.5).
	y := y + 28.
	MTSTheory chordTypes doWithIndex: [:t :r |
		self mkLabel: (t at: 1) at: 972 @ (y + 2) color: (Color r: 0.45 g: 0.45 b: 0.5).
		0 to: 11 do: [:pc | | b |
			b := SimpleButtonMorph new.
			b label: ''.
			b target: self.
			b actionSelector: #insertChord:type:.
			b arguments: (Array with: pc with: (t at: 1)).
			b color: (MTSTheory noteColor: 60 + pc).
			b borderWidth: 1.
			b borderColor: Color black.
			b extent: 17 @ 17.
			b position: self position + ((1002 + (pc * 19)) @ y).
			self addMorph: b].
		y := y + 21].
	self mkLabel: 'コードをクリック = シンセ演奏 + 楽譜へ挿入' at: 972 @ (y + 4)
		color: (Color r: 0.4 g: 0.4 b: 0.45)! !

!MTSApp methodsFor: 'accessing'!
parsed
	^ parsed! !

!MTSApp methodsFor: 'accessing'!
beatEvents
	^ beatEventsCache ifNil: [OrderedCollection new]! !

!MTSApp methodsFor: 'accessing'!
playingIndex
	^ playingIndex ifNil: [0]! !

!MTSApp methodsFor: 'source'!
sourceString
	^ [sourceEditor text asString]
		on: Error
		do: [:e | [sourceEditor contents asString] on: Error do: [:x | '']]! !

!MTSApp methodsFor: 'source'!
setSource: aString
	[sourceEditor contents: aString] on: Error do: [:e | ]! !

!MTSApp methodsFor: 'actions'!
refresh
	parsed := MTSTheory parseMusixTeX: self sourceString.
	beatEventsCache := MTSTheory beatEventsFrom: parsed.
	self updateLcd.
	spectral ifNotNil: [spectral changed].
	staff ifNotNil: [staff changed]! !

!MTSApp methodsFor: 'actions'!
updateLcd
	| notes bars sig |
	parsed ifNil: [^ self].
	sig := parsed at: #signature.
	notes := 0. bars := 1.
	(parsed at: #events) do: [:e |
		(e at: 1) = #bar ifTrue: [bars := bars + 1] ifFalse: [notes := notes + 1]].
	lcd contents: 'KEY ', sig printString, '  4/4  NOTES ', notes printString,
		'  BARS ', bars printString, '  INST ', patchName,
		(importOverlay ifTrue: ['  MODE overlay'] ifFalse: ['  MODE replace'])! !

!MTSApp methodsFor: 'actions'!
doRefresh
	self refresh! !

!MTSApp methodsFor: 'actions'!
doPlay
	| me |
	self refresh.
	me := self.
	MTSSynth playEvents: self beatEvents tempo: 96 patch: patch
		onEvent: [:i |
			playingIndex := i.
			WorldState addDeferredUIMessage: [me spectralChanged]]! !

!MTSApp methodsFor: 'actions'!
spectralChanged
	spectral ifNotNil: [spectral changed]! !

!MTSApp methodsFor: 'actions'!
doStop
	MTSSynth stop.
	playingIndex := 0.
	self spectralChanged! !

!MTSApp methodsFor: 'actions'!
doTestTone
	MTSSynth playMidi: 69 dur: 0.5 patch: patch.
	visionInfo contents: 'A4 = 440Hz -> 484THz -> 620nm'! !

!MTSApp methodsFor: 'actions'!
toggleImportMode
	importOverlay := importOverlay not.
	self updateLcd! !

!MTSApp methodsFor: 'actions'!
selectInstrument: aName
	patchName := aName.
	patch := MTSSynth presetNamed: aName.
	instButtons do: [:b |
		b color: (b label = aName
			ifTrue: [Color r: 0.04 g: 0.52 b: 1.0]
			ifFalse: [Color r: 0.2 g: 0.2 b: 0.22])].
	harmSliders doWithIndex: [:s :k | s setValue: ((patch at: #harmonics) at: k)].
	self updateLcd.
	MTSSynth playMidi: 69 dur: 0.4 patch: patch! !

!MTSApp methodsFor: 'actions'!
selectTemplate: i
	self setSource: ((MTSTheory templates at: i) at: 2).
	self refresh! !

!MTSApp methodsFor: 'actions'!
harm1: value
	self setHarmonic: value index: 1! !

!MTSApp methodsFor: 'actions'!
harm2: value
	self setHarmonic: value index: 2! !

!MTSApp methodsFor: 'actions'!
harm3: value
	self setHarmonic: value index: 3! !

!MTSApp methodsFor: 'actions'!
harm4: value
	self setHarmonic: value index: 4! !

!MTSApp methodsFor: 'actions'!
harm5: value
	self setHarmonic: value index: 5! !

!MTSApp methodsFor: 'actions'!
harm6: value
	self setHarmonic: value index: 6! !

!MTSApp methodsFor: 'actions'!
harm7: value
	self setHarmonic: value index: 7! !

!MTSApp methodsFor: 'actions'!
harm8: value
	self setHarmonic: value index: 8! !

!MTSApp methodsFor: 'actions'!
setHarmonic: value index: k
	| h |
	h := (patch at: #harmonics) copy asArray.
	h at: k put: value asFloat.
	patch at: #harmonics put: h! !

!MTSApp methodsFor: 'actions'!
insertChord: pc type: typeName
	"五行コード線: シンセで演奏し、調号を考慮した和音を楽譜へ挿入"
	| midis sig tok src pos |
	midis := MTSTheory chordMidisRoot: pc type: typeName octave: 4.
	MTSSynth playMidis: midis dur: 0.7 patch: patch.
	self refresh.
	sig := parsed at: #signature.
	tok := WriteStream on: String new.
	(midis asSortedCollection asArray) doWithIndex: [:m :i | | p |
		p := MTSTheory midiToTex: m sig: sig.
		(p at: 2) ifNotNil: [:acc | tok nextPutAll: '\', acc asString, ' ', (p at: 1)].
		i < midis size
			ifTrue: [tok nextPutAll: '\zq{', (p at: 1), '}']
			ifFalse: [tok nextPutAll: '\qu{', (p at: 1), '}']].
	src := self sourceString.
	pos := self lastEnPositionIn: src.
	pos > 0
		ifTrue: [self setSource: (src copyFrom: 1 to: pos - 1), tok contents, (src copyFrom: pos to: src size)]
		ifFalse: [self setSource: src, tok contents].
	visionInfo contents: (MTSTheory noteNames at: pc + 1), typeName, ' = ', midis printString.
	self refresh! !

!MTSApp methodsFor: 'actions'!
lastEnPositionIn: src
	"最後の音符グループ末尾 (\en の直前位置) を探す"
	| i last |
	last := 0.
	i := 1.
	[i <= (src size - 2)] whileTrue: [
		((src at: i) = $\ and: [(src at: i + 1) = $e and: [(src at: i + 2) = $n]])
			ifTrue: [
				(i + 3 > src size or: [(src at: i + 3) isLetter not])
					ifTrue: [last := i]].
		i := i + 1].
	^ last! !

!MTSApp methodsFor: 'actions'!
doChordify
	"いまの楽譜からコード進行を抽出して伴奏として重ねる"
	| events line chordEvents merged tex |
	self refresh.
	events := self beatEvents.
	events isEmpty ifTrue: [^ self inform: 'コード化する音符がありません'].
	line := MTSTheory extractChordLine: events window: 4.
	line isEmpty ifTrue: [^ self inform: 'コードを抽出できませんでした'].
	chordEvents := line collect: [:c |
		Array with: (c at: 1) with: 1
			with: (MTSTheory chordMidisRoot: (c at: 3) type: (c at: 4) octave: 3)].
	merged := MTSTheory mergeEvents: events with: chordEvents.
	tex := MTSTheory eventsToMusixTex: merged signature: (parsed at: #signature) source: 'chordify'.
	tex ifNotNil: [self setSource: tex. self refresh]! !

!MTSApp methodsFor: 'actions'!
importEvents: events name: aName
	| tex merged |
	(events isNil or: [events isEmpty]) ifTrue: [^ self inform: aName, ': 音符を検出できませんでした'].
	importOverlay
		ifTrue: [
			self refresh.
			merged := MTSTheory mergeEvents: self beatEvents with: events.
			tex := MTSTheory eventsToMusixTex: merged signature: (parsed at: #signature) source: aName]
		ifFalse: [
			tex := MTSTheory eventsToMusixTex: events signature: nil source: aName].
	tex ifNotNil: [self setSource: tex. self refresh]! !

!MTSApp methodsFor: 'actions'!
doImportMidi
	| path |
	path := UIManager default request: 'MIDI ファイルのパス' initialAnswer: 'song.mid'.
	(path isNil or: [path isEmpty]) ifTrue: [^ self].
	[self importEvents: (MTSSynth midiEventsFromFileNamed: path) name: path]
		on: Error do: [:e | self inform: 'MIDI 読み込みエラー: ', e messageText asString]! !

!MTSApp methodsFor: 'actions'!
doImportWav
	| path |
	path := UIManager default request: 'WAV ファイルのパス' initialAnswer: 'song.wav'.
	(path isNil or: [path isEmpty]) ifTrue: [^ self].
	[self importEvents: (MTSSynth wavEventsFromFileNamed: path) name: path]
		on: Error do: [:e | self inform: 'WAV 読み込みエラー: ', e messageText asString]! !

!MTSApp methodsFor: 'actions'!
doSaveTex
	| path f |
	path := UIManager default request: '保存する .tex ファイル名' initialAnswer: 'score.tex'.
	(path isNil or: [path isEmpty]) ifTrue: [^ self].
	[f := FileStream newFileNamed: path.
	 f nextPutAll: self sourceString.
	 f close.
	 self inform: path, ' に保存しました。texlive-music でコンパイル: musixtex -p ', path]
		on: Error do: [:e | self inform: '保存エラー: ', e messageText asString]! !

// Bada Studio — オーディオエンジン
//
// AVAudioEngine の上に
//   - 8 ボイス・ポリフォニックシンセ (AVAudioSourceNode / 波形 4 種 / AR エンベロープ)
//   - ドラムシンセ + 16 ステップシーケンサー (キック / スネア / ハイハット、サンプル精度)
//   - センドエフェクト (ディレイ → リバーブ)
//   - マスターバス録音 (~/Music/Bada Studio/*.caf)
// を実装する。UI からは ObservableObject として扱う。

import AVFoundation
import AppKit
import Combine
import Foundation

enum Waveform: Int, CaseIterable, Identifiable {
    case sine = 0
    case sawtooth = 1
    case square = 2
    case triangle = 3

    var id: Int { rawValue }

    var label: String {
        switch self {
        case .sine: return "サイン"
        case .sawtooth: return "ノコギリ"
        case .square: return "矩形"
        case .triangle: return "三角"
        }
    }
}

/// 1 ボイス分の状態。オーディオスレッドが毎レンダーで読み書きする。
final class SynthVoice {
    var note: Int = -1
    var phase: Double = 0
    var envelope: Double = 0
    var gate: Bool = false
    var active: Bool = false
}

final class StudioEngine: ObservableObject {

    // MARK: - 定数

    static let stepCount = 16
    static let trackCount = 3
    static let drumNames = ["キック", "スネア", "ハイハット"]

    // MARK: - UI 公開パラメータ

    @Published var waveform: Waveform = .sawtooth
    @Published var attack: Double = 0.01
    @Published var release: Double = 0.35
    @Published var octave: Int = 4
    @Published var bpm: Double = 120

    @Published var synthVolume: Double = 0.8 {
        didSet { synthMixer.outputVolume = Float(synthVolume) }
    }
    @Published var drumVolume: Double = 0.9 {
        didSet { drumMixer.outputVolume = Float(drumVolume) }
    }
    @Published var masterVolume: Double = 0.85 {
        didSet { engine.mainMixerNode.outputVolume = Float(masterVolume) }
    }
    @Published var reverbMix: Double = 18 {
        didSet { reverb.wetDryMix = Float(reverbMix) }
    }
    @Published var delayMix: Double = 0 {
        didSet { delay.wetDryMix = Float(delayMix) }
    }
    @Published var delayTime: Double = 0.28 {
        didSet { delay.delayTime = delayTime }
    }
    @Published var delayFeedback: Double = 30 {
        didSet { delay.feedback = Float(delayFeedback) }
    }

    @Published var isPlaying = false
    @Published var isRecording = false
    @Published var currentStep = 0
    @Published var lastRecordingName: String?

    /// 3 トラック x 16 ステップ。要素の書き換えのみ行い、再確保はしない
    /// (オーディオスレッドが同じストレージを読むため)。
    private(set) var pattern = [Bool](repeating: false, count: StudioEngine.trackCount * StudioEngine.stepCount)

    // MARK: - オーディオグラフ

    private let engine = AVAudioEngine()
    private let synthMixer = AVAudioMixerNode()
    private let drumMixer = AVAudioMixerNode()
    private let submix = AVAudioMixerNode()
    private let reverb = AVAudioUnitReverb()
    private let delay = AVAudioUnitDelay()
    private var synthNode: AVAudioSourceNode!
    private var drumNode: AVAudioSourceNode!
    private var sampleRate: Double = 44100

    // MARK: - シンセ / ドラム / シーケンサー状態 (オーディオスレッド専有)

    private let voices: [SynthVoice] = (0..<8).map { _ in SynthVoice() }

    private var kickEnv: Double = 0
    private var kickPhase: Double = 0
    private var snareEnv: Double = 0
    private var snarePhase: Double = 0
    private var hatEnv: Double = 0
    private var noiseState: UInt32 = 0x1234_5678
    private var lastNoise: Double = 0

    private var playingFlag = false
    private var frameCursor: Double = 0
    private var stepIndex = 0

    // MARK: - 録音

    private var recordFile: AVAudioFile?
    private var recordURL: URL?

    // MARK: - 初期化

    init() {
        let hwRate = engine.outputNode.outputFormat(forBus: 0).sampleRate
        sampleRate = hwRate > 0 ? hwRate : 44100

        guard let mono = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 1),
              let stereo = AVAudioFormat(standardFormatWithSampleRate: sampleRate, channels: 2)
        else {
            fatalError("AVAudioFormat の作成に失敗しました")
        }

        synthNode = AVAudioSourceNode(format: mono) { [unowned self] _, _, frameCount, audioBufferList in
            self.renderSynth(frameCount: frameCount, audioBufferList: audioBufferList)
        }
        drumNode = AVAudioSourceNode(format: mono) { [unowned self] _, _, frameCount, audioBufferList in
            self.renderDrums(frameCount: frameCount, audioBufferList: audioBufferList)
        }

        engine.attach(synthNode)
        engine.attach(drumNode)
        engine.attach(synthMixer)
        engine.attach(drumMixer)
        engine.attach(submix)
        engine.attach(delay)
        engine.attach(reverb)

        engine.connect(synthNode, to: synthMixer, format: mono)
        engine.connect(drumNode, to: drumMixer, format: mono)
        engine.connect(synthMixer, to: submix, format: stereo)
        engine.connect(drumMixer, to: submix, format: stereo)
        engine.connect(submix, to: delay, format: stereo)
        engine.connect(delay, to: reverb, format: stereo)
        engine.connect(reverb, to: engine.mainMixerNode, format: stereo)

        reverb.loadFactoryPreset(.mediumHall)
        reverb.wetDryMix = Float(reverbMix)
        delay.wetDryMix = Float(delayMix)
        delay.delayTime = delayTime
        delay.feedback = Float(delayFeedback)
        delay.lowPassCutoff = 12000

        synthMixer.outputVolume = Float(synthVolume)
        drumMixer.outputVolume = Float(drumVolume)
        engine.mainMixerNode.outputVolume = Float(masterVolume)

        loadDefaultPattern()

        engine.prepare()
        do {
            try engine.start()
        } catch {
            NSLog("Bada Studio: オーディオエンジンを開始できませんでした: \(error)")
        }
    }

    private func loadDefaultPattern() {
        // 定番の 4 つ打ち + バックビート + 8 分ハイハット
        for step in [0, 4, 8, 12] { pattern[0 * Self.stepCount + step] = true }
        for step in [4, 12] { pattern[1 * Self.stepCount + step] = true }
        for step in stride(from: 0, to: Self.stepCount, by: 2) { pattern[2 * Self.stepCount + step] = true }
    }

    // MARK: - パターン編集

    func patternValue(track: Int, step: Int) -> Bool {
        pattern[track * Self.stepCount + step]
    }

    func togglePattern(track: Int, step: Int) {
        objectWillChange.send()
        pattern[track * Self.stepCount + step].toggle()
    }

    func clearPattern() {
        objectWillChange.send()
        for i in pattern.indices { pattern[i] = false }
    }

    // MARK: - トランスポート

    func togglePlay() {
        if isPlaying {
            playingFlag = false
            isPlaying = false
            currentStep = 0
        } else {
            stepIndex = 0
            frameCursor = 0
            currentStep = 0
            playingFlag = true
            isPlaying = true
        }
    }

    // MARK: - 鍵盤

    func noteOn(_ note: Int) {
        if let held = voices.first(where: { $0.active && $0.note == note }) {
            held.gate = true
            return
        }
        let voice = voices.first(where: { !$0.active })
            ?? voices.min(by: { $0.envelope < $1.envelope })!
        voice.note = note
        voice.phase = 0
        voice.envelope = 0
        voice.gate = true
        voice.active = true
    }

    func noteOff(_ note: Int) {
        for voice in voices where voice.note == note {
            voice.gate = false
        }
    }

    // MARK: - 録音 (マスターバスをそのままファイルへ)

    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }

    private func startRecording() {
        let format = engine.mainMixerNode.outputFormat(forBus: 0)
        let musicDir = FileManager.default.urls(for: .musicDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        let dir = musicDir.appendingPathComponent("Bada Studio", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)

        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        let url = dir.appendingPathComponent("BadaStudio-\(formatter.string(from: Date())).caf")

        do {
            let file = try AVAudioFile(forWriting: url, settings: format.settings)
            recordFile = file
            recordURL = url
            engine.mainMixerNode.installTap(onBus: 0, bufferSize: 4096, format: format) { [weak self] buffer, _ in
                guard let file = self?.recordFile else { return }
                do {
                    try file.write(from: buffer)
                } catch {
                    NSLog("Bada Studio: 録音書き込みに失敗: \(error)")
                }
            }
            isRecording = true
        } catch {
            NSLog("Bada Studio: 録音を開始できませんでした: \(error)")
        }
    }

    private func stopRecording() {
        engine.mainMixerNode.removeTap(onBus: 0)
        recordFile = nil
        isRecording = false
        if let url = recordURL {
            lastRecordingName = url.lastPathComponent
            NSWorkspace.shared.activateFileViewerSelecting([url])
        }
    }

    // MARK: - シンセレンダリング (オーディオスレッド)

    private func renderSynth(frameCount: AVAudioFrameCount,
                             audioBufferList: UnsafeMutablePointer<AudioBufferList>) -> OSStatus {
        let buffers = UnsafeMutableAudioBufferListPointer(audioBufferList)
        guard let rawBuffer = buffers[0].mData else { return noErr }
        let out = rawBuffer.assumingMemoryBound(to: Float.self)
        let frames = Int(frameCount)

        for i in 0..<frames { out[i] = 0 }

        let shape = waveform
        let attackStep = 1.0 / (max(0.001, attack) * sampleRate)
        let releaseStep = 1.0 / (max(0.005, release) * sampleRate)

        for voice in voices where voice.active {
            let frequency = 440.0 * pow(2.0, Double(voice.note - 69) / 12.0)
            let phaseStep = frequency / sampleRate
            var phase = voice.phase
            var envelope = voice.envelope
            let gate = voice.gate

            for i in 0..<frames {
                if gate {
                    envelope = min(1.0, envelope + attackStep)
                } else {
                    envelope = max(0.0, envelope - releaseStep)
                    if envelope == 0 { continue }
                }

                let value: Double
                switch shape {
                case .sine:
                    value = sin(2.0 * Double.pi * phase)
                case .sawtooth:
                    value = 2.0 * phase - 1.0
                case .square:
                    value = phase < 0.5 ? 1.0 : -1.0
                case .triangle:
                    value = 1.0 - 4.0 * abs(phase - 0.5)
                }

                out[i] += Float(value * envelope * 0.22)
                phase += phaseStep
                if phase >= 1.0 { phase -= 1.0 }
            }

            voice.phase = phase
            voice.envelope = envelope
            if !gate && envelope == 0 {
                voice.active = false
                voice.note = -1
            }
        }

        return noErr
    }

    // MARK: - ドラム + シーケンサーレンダリング (オーディオスレッド)

    private func renderDrums(frameCount: AVAudioFrameCount,
                             audioBufferList: UnsafeMutablePointer<AudioBufferList>) -> OSStatus {
        let buffers = UnsafeMutableAudioBufferListPointer(audioBufferList)
        guard let rawBuffer = buffers[0].mData else { return noErr }
        let out = rawBuffer.assumingMemoryBound(to: Float.self)
        let frames = Int(frameCount)

        // 16 分音符 1 個あたりのフレーム数
        let framesPerStep = max(1.0, sampleRate * 60.0 / max(30.0, bpm) / 4.0)

        // -60 dB へ落ちるまでの時間から減衰係数を決める
        let kickDecay = pow(0.001, 1.0 / (0.35 * sampleRate))
        let snareDecay = pow(0.001, 1.0 / (0.18 * sampleRate))
        let hatDecay = pow(0.001, 1.0 / (0.06 * sampleRate))

        for i in 0..<frames {
            if playingFlag {
                if frameCursor <= 0 {
                    triggerStep(stepIndex)
                    let firedStep = stepIndex
                    DispatchQueue.main.async { [weak self] in
                        self?.currentStep = firedStep
                    }
                    stepIndex = (stepIndex + 1) % Self.stepCount
                    frameCursor += framesPerStep
                }
                frameCursor -= 1
            }

            // 線形合同法ノイズ (オーディオスレッドでアロケーションしない)
            noiseState = noiseState &* 1_664_525 &+ 1_013_904_223
            let white = Double(Int32(bitPattern: noiseState)) / Double(Int32.max)

            var sample = 0.0

            if kickEnv > 0.0005 {
                let sweep = 42.0 + 130.0 * kickEnv * kickEnv
                kickPhase += sweep / sampleRate
                if kickPhase >= 1.0 { kickPhase -= 1.0 }
                sample += sin(2.0 * Double.pi * kickPhase) * kickEnv * 1.1
                kickEnv *= kickDecay
            }

            if snareEnv > 0.0005 {
                snarePhase += 190.0 / sampleRate
                if snarePhase >= 1.0 { snarePhase -= 1.0 }
                sample += (white * 0.75 + sin(2.0 * Double.pi * snarePhase) * 0.3) * snareEnv * 0.8
                snareEnv *= snareDecay
            }

            if hatEnv > 0.0005 {
                // 1 次差分でノイズの低域を落とし、金属的な質感にする
                sample += (white - lastNoise) * 0.5 * hatEnv * 0.6
                hatEnv *= hatDecay
            }

            lastNoise = white
            out[i] = Float(max(-1.0, min(1.0, sample)))
        }

        return noErr
    }

    private func triggerStep(_ step: Int) {
        if pattern[0 * Self.stepCount + step] {
            kickEnv = 1.0
            kickPhase = 0
        }
        if pattern[1 * Self.stepCount + step] {
            snareEnv = 1.0
        }
        if pattern[2 * Self.stepCount + step] {
            hatEnv = 1.0
        }
    }
}

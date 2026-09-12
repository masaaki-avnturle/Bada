// Bada Studio — メイン画面
// トランスポート / シンセ / ミキサー&エフェクト / ステップシーケンサー / 鍵盤

import AppKit
import SwiftUI

// MARK: - 共通パネル

struct Panel<Content: View>: View {
    let title: String
    let content: Content

    init(_ title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
                .foregroundColor(.white.opacity(0.85))
            content
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 12).fill(Color.white.opacity(0.06)))
    }
}

struct SliderRow: View {
    let title: String
    @Binding var value: Double
    let range: ClosedRange<Double>
    var format: String = "%.2f"
    var unit: String = ""

    var body: some View {
        HStack(spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundColor(.white.opacity(0.7))
                .frame(width: 96, alignment: .leading)
            Slider(value: $value, in: range)
            Text(String(format: format, value) + unit)
                .font(.caption.monospacedDigit())
                .foregroundColor(.white.opacity(0.7))
                .frame(width: 64, alignment: .trailing)
        }
    }
}

// MARK: - 鍵盤

struct PianoKeyView: View {
    let note: Int
    let isBlack: Bool
    let engine: StudioEngine
    @State private var pressed = false

    var body: some View {
        RoundedRectangle(cornerRadius: 4)
            .fill(fillColor)
            .overlay(
                RoundedRectangle(cornerRadius: 4)
                    .stroke(Color.black.opacity(0.7), lineWidth: 1)
            )
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { _ in
                        if !pressed {
                            pressed = true
                            engine.noteOn(note)
                        }
                    }
                    .onEnded { _ in
                        pressed = false
                        engine.noteOff(note)
                    }
            )
    }

    private var fillColor: Color {
        if pressed { return Color.orange }
        return isBlack ? Color(white: 0.12) : Color(white: 0.93)
    }
}

private struct BlackKeySpec: Identifiable {
    let offset: Int       // オクターブ内の半音オフセット
    let position: Double  // 白鍵何個目の境界に置くか
    var id: Int { offset }
}

struct PianoKeyboardView: View {
    @ObservedObject var engine: StudioEngine

    private let whiteOffsets = [0, 2, 4, 5, 7, 9, 11]
    private let blackKeys: [BlackKeySpec] = [
        BlackKeySpec(offset: 1, position: 1),
        BlackKeySpec(offset: 3, position: 2),
        BlackKeySpec(offset: 6, position: 4),
        BlackKeySpec(offset: 8, position: 5),
        BlackKeySpec(offset: 10, position: 6),
    ]
    private let octaveSpan = 2

    var body: some View {
        GeometryReader { geo in
            let whiteCount = octaveSpan * 7 + 1
            let keyWidth = geo.size.width / CGFloat(whiteCount)
            let baseNote = (engine.octave + 1) * 12

            ZStack(alignment: .topLeading) {
                HStack(spacing: 0) {
                    ForEach(0..<whiteCount, id: \.self) { index in
                        PianoKeyView(
                            note: baseNote + (index / 7) * 12 + whiteOffsets[index % 7],
                            isBlack: false,
                            engine: engine
                        )
                        .frame(width: keyWidth)
                    }
                }
                ForEach(0..<octaveSpan, id: \.self) { octave in
                    ForEach(blackKeys) { key in
                        PianoKeyView(
                            note: baseNote + octave * 12 + key.offset,
                            isBlack: true,
                            engine: engine
                        )
                        .frame(width: keyWidth * 0.62, height: geo.size.height * 0.6)
                        .offset(x: (CGFloat(octave * 7) + CGFloat(key.position)) * keyWidth - keyWidth * 0.31)
                    }
                }
            }
        }
        .frame(height: 140)
    }
}

// MARK: - ステップシーケンサー

struct DrumGridView: View {
    @ObservedObject var engine: StudioEngine

    var body: some View {
        VStack(spacing: 6) {
            ForEach(0..<StudioEngine.trackCount, id: \.self) { track in
                HStack(spacing: 4) {
                    Text(StudioEngine.drumNames[track])
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.7))
                        .frame(width: 74, alignment: .leading)
                    ForEach(0..<StudioEngine.stepCount, id: \.self) { step in
                        RoundedRectangle(cornerRadius: 3)
                            .fill(cellColor(track: track, step: step))
                            .frame(height: 28)
                            .frame(maxWidth: .infinity)
                            .onTapGesture {
                                engine.togglePattern(track: track, step: step)
                            }
                    }
                }
            }
        }
    }

    private func cellColor(track: Int, step: Int) -> Color {
        let on = engine.patternValue(track: track, step: step)
        let isCurrent = engine.isPlaying && engine.currentStep == step
        if on {
            return isCurrent ? Color.orange : Color.cyan.opacity(0.85)
        }
        if isCurrent {
            return Color.white.opacity(0.32)
        }
        return step % 4 == 0 ? Color.white.opacity(0.14) : Color.white.opacity(0.07)
    }
}

// MARK: - メイン画面

struct ContentView: View {
    @StateObject private var engine = StudioEngine()
    @State private var keyMonitor: Any?

    // PC キーボード → 半音オフセット (a=ド から k=1 オクターブ上のド まで)
    private static let keyToOffset: [Character: Int] = [
        "a": 0, "w": 1, "s": 2, "e": 3, "d": 4, "f": 5, "t": 6,
        "g": 7, "y": 8, "h": 9, "u": 10, "j": 11, "k": 12, "o": 13, "l": 14,
    ]

    var body: some View {
        VStack(spacing: 12) {
            transportBar

            HStack(alignment: .top, spacing: 12) {
                synthPanel
                mixerPanel
            }

            Panel("ステップシーケンサー — 16 ステップ / 3 トラック") {
                DrumGridView(engine: engine)
                HStack {
                    Button("パターンをクリア") { engine.clearPattern() }
                    Spacer()
                    Text("マスを押して打ち込み。再生中はオレンジのマスが現在位置。")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.5))
                }
            }

            Panel("鍵盤 — マウス演奏 / PC キー (A,W,S,E,D,F,T,G,Y,H,U,J,K…)") {
                PianoKeyboardView(engine: engine)
            }
        }
        .padding(16)
        .frame(minWidth: 1020, minHeight: 700)
        .background(
            LinearGradient(
                colors: [Color(red: 0.10, green: 0.11, blue: 0.15),
                         Color(red: 0.05, green: 0.05, blue: 0.08)],
                startPoint: .top,
                endPoint: .bottom
            )
        )
        .preferredColorScheme(.dark)
        .onAppear { installKeyMonitor() }
        .onDisappear { removeKeyMonitor() }
    }

    // MARK: トランスポート

    private var transportBar: some View {
        Panel("トランスポート") {
            HStack(spacing: 16) {
                Button {
                    engine.togglePlay()
                } label: {
                    Label(engine.isPlaying ? "停止" : "再生",
                          systemImage: engine.isPlaying ? "stop.fill" : "play.fill")
                        .frame(width: 80)
                }
                .keyboardShortcut(.space, modifiers: [])

                Button {
                    engine.toggleRecording()
                } label: {
                    Label(engine.isRecording ? "録音停止" : "録音",
                          systemImage: "record.circle")
                        .frame(width: 90)
                        .foregroundColor(engine.isRecording ? .red : .primary)
                }

                if engine.isRecording {
                    Text("● REC")
                        .font(.caption.bold())
                        .foregroundColor(.red)
                } else if let name = engine.lastRecordingName {
                    Text("保存済み: \(name)")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.6))
                        .lineLimit(1)
                }

                Spacer()

                Text("BPM")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.7))
                Slider(value: $engine.bpm, in: 60...200)
                    .frame(width: 180)
                Text(String(format: "%.0f", engine.bpm))
                    .font(.body.monospacedDigit())
                    .frame(width: 44, alignment: .trailing)

                Divider().frame(height: 20)

                Text("マスター")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.7))
                Slider(value: $engine.masterVolume, in: 0...1)
                    .frame(width: 140)
            }
        }
    }

    // MARK: シンセパネル

    private var synthPanel: some View {
        Panel("シンセサイザー — 8 ボイス ポリフォニック") {
            Picker("波形", selection: $engine.waveform) {
                ForEach(Waveform.allCases) { shape in
                    Text(shape.label).tag(shape)
                }
            }
            .pickerStyle(.segmented)
            .labelsHidden()

            SliderRow(title: "アタック", value: $engine.attack, range: 0.001...1.0, format: "%.3f", unit: " s")
            SliderRow(title: "リリース", value: $engine.release, range: 0.02...3.0, unit: " s")
            SliderRow(title: "音量", value: $engine.synthVolume, range: 0...1)

            Stepper("オクターブ: C\(engine.octave)", value: $engine.octave, in: 2...6)
                .font(.caption)
        }
    }

    // MARK: ミキサー & エフェクト

    private var mixerPanel: some View {
        Panel("ミキサー & エフェクト") {
            SliderRow(title: "ドラム音量", value: $engine.drumVolume, range: 0...1)
            SliderRow(title: "リバーブ", value: $engine.reverbMix, range: 0...100, format: "%.0f", unit: " %")
            SliderRow(title: "ディレイ", value: $engine.delayMix, range: 0...100, format: "%.0f", unit: " %")
            SliderRow(title: "遅延時間", value: $engine.delayTime, range: 0.05...1.0, unit: " s")
            SliderRow(title: "フィードバック", value: $engine.delayFeedback, range: 0...90, format: "%.0f", unit: " %")
        }
    }

    // MARK: PC キーボード演奏

    private func installKeyMonitor() {
        guard keyMonitor == nil else { return }
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown, .keyUp]) { event in
            guard !event.modifierFlags.contains(.command) else { return event }
            guard let characters = event.charactersIgnoringModifiers?.lowercased(),
                  let key = characters.first,
                  let offset = Self.keyToOffset[key]
            else { return event }

            let note = (engine.octave + 1) * 12 + offset
            if event.type == .keyDown {
                if !event.isARepeat {
                    engine.noteOn(note)
                }
            } else {
                engine.noteOff(note)
            }
            return nil
        }
    }

    private func removeKeyMonitor() {
        if let monitor = keyMonitor {
            NSEvent.removeMonitor(monitor)
            keyMonitor = nil
        }
    }
}

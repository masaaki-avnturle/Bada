// swift-tools-version:5.9
// Bada Studio — macOS 専用の音楽制作アプリ (SwiftUI + AVAudioEngine)
import PackageDescription

let package = Package(
    name: "BadaStudio",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "BadaStudio",
            path: "Sources/BadaStudio"
        )
    ]
)

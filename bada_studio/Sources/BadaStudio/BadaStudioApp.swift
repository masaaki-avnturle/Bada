// Bada Studio — macOS 専用 音楽制作アプリ
// エントリポイント。SwiftUI の WindowGroup 1 枚に全パネルを載せる。

import AppKit
import SwiftUI

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // swift run / 直接バイナリ起動でも前面のフォアグラウンドアプリになるように
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }
}

@main
struct BadaStudioApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup("Bada Studio") {
            ContentView()
        }
    }
}

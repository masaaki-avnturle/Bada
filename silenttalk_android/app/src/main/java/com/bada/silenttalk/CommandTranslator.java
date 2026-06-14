package com.bada.silenttalk;

/**
 * Translates a recognised silent signal into a language command — the
 * "言語に翻訳" step. The label is shown on the HUD so the user can see what
 * Silent Talk understood before/while it operates the device.
 */
final class CommandTranslator {

    private CommandTranslator() {}

    enum Command {
        TAP, BACK, HOME, RECENTS, NOTIFICATIONS, SCROLL_UP, SCROLL_DOWN
    }

    static String label(Command c) {
        switch (c) {
            case TAP:           return "タップ";
            case BACK:          return "戻る";
            case HOME:          return "ホーム";
            case RECENTS:       return "履歴";
            case NOTIFICATIONS: return "通知";
            case SCROLL_UP:     return "上スクロール";
            case SCROLL_DOWN:   return "下スクロール";
            default:            return "?";
        }
    }

    static String spoken(Command c) {
        return "🗣 「" + label(c) + "」";
    }
}

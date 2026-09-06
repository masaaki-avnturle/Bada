/* Bada VM Pro OS — Calamares スライドショー (slideshowAPI 1: 単純な QML アイテム) */
import QtQuick 2.0

Rectangle {
    width: 800; height: 320
    color: "#0b0e14"

    Column {
        anchors.centerIn: parent
        spacing: 14

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Bada VM Pro OS"
            color: "#c8a44a"
            font.pixelSize: 34
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "量子 Bada 言語の OS をインストールしています…"
            color: "#d7dce8"
            font.pixelSize: 18
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "w9wm · BadaGPT · Bada on Rails · Laevateinn"
            color: "#8791a8"
            font.pixelSize: 13
        }
    }
}

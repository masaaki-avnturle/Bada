// BadaFiles — ネイティブのファイル選択・保存 (Android)。すべて Promise を返す。
var exec = require("cordova/exec");
function call(action, args) {
  return new Promise(function (resolve, reject) { exec(resolve, reject, "BadaFiles", action, args); });
}
module.exports = {
  // mime: "application/pdf" など ("*/*" で全ファイル) → {name, size, data: base64}
  open: function (mime) { return call("open", [mime || "*/*"]); },
  // ダウンロード フォルダへ保存 → 保存先の表示名 ("Download/xxx.apk")
  saveDownloads: function (name, mime, b64) { return call("saveDownloads", [name, mime || "application/octet-stream", b64]); },
  // 保存先を選んで保存 → ファイル名
  saveAs: function (name, mime, b64) { return call("saveAs", [name, mime || "application/octet-stream", b64]); },
  // ダウンロード フォルダを開く
  showDownloads: function () { return call("showDownloads", []); }
};

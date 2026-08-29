/*
 * electron-builder.config.js — 汎用ビルド設定
 * 環境変数で 1 アプリ分の設定を受け取ります (all-apps-build.yml が設定):
 *   BADA_APP_ID   … apps.json の id           (例: omega_tomograph)
 *   BADA_PRODUCT  … apps.json の product      (例: Omega-Tomograph)
 *   BADA_VERSION  … apps.json の version      (例: 1.0.0)
 *   BADA_CATEGORY … Linux デスクトップカテゴリ (例: Science)
 */
const id = process.env.BADA_APP_ID || "bada_omega_app";
const product = process.env.BADA_PRODUCT || "Bada-Omega-App";
const version = process.env.BADA_VERSION || "1.0.0";
const category = process.env.BADA_CATEGORY || "Utility";

module.exports = {
  appId: "io.github.masaaki_avnturle." + id,
  productName: product,
  publish: null,
  extraMetadata: {
    name: id.replace(/_/g, "-"),
    version: version
  },
  files: ["main.js", "app.json", "package.json"],
  extraResources: [{ from: "www", to: "www" }],
  directories: { output: "dist" },
  win: {
    target: ["nsis", "portable"],
    artifactName: product + "-${version}-${arch}.${ext}"
  },
  nsis: { oneClick: false, allowToChangeInstallationDirectory: true },
  portable: { artifactName: product + "-${version}-portable.${ext}" },
  linux: {
    target: ["AppImage", "deb"],
    category: category,
    artifactName: product + "-${version}-${arch}.${ext}",
    maintainer: "masaaki-avnturle",
    synopsis: product
  }
};

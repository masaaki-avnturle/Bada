# 📚 bookscope — 書籍バーコードスキャン & 蔵書一覧アプリ

購入した書籍のバーコード(ISBN)をスマホ・タブレットのカメラでスキャンすると、
書籍の**表紙**と**内容の概要**を自動取得して bookscope に登録し、
**蔵書一覧表**で閲覧・検索・CSV 出力できる Web アプリです。

- 依存パッケージなし(Node.js だけで動きます)
- スキャンはブラウザで動くので、スマホ・タブレットへのアプリインストールは不要
- 書誌情報は [openBD](https://openbd.jp/)(日本の書籍の表紙・内容紹介)を優先し、
  足りない情報は Google Books API で補完
- 蔵書データはサーバーの `data/books.json` に保存されるため、
  スマホ・タブレット・PC のどこから登録しても同じ一覧を共有できます

## 使い方

### 1. サーバーを起動する(PC 側)

```bash
cd bookscope
node server.js
```

`http://localhost:3000` で起動します。PC のブラウザで開けば、
そのまま手入力での登録・一覧表示ができます。

### 2. スマホ・タブレットからカメラでスキャンする

ブラウザのカメラ機能(getUserMedia)はセキュリティ上 **HTTPS または localhost**
でしか動きません。スマホ・タブレットから使うには HTTPS を有効にします。

自己署名証明書を作って `certs/` に置くだけです:

```bash
cd bookscope
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout certs/server.key -out certs/server.crt \
  -subj "/CN=bookscope"
node server.js
```

すると `https://<PCのIPアドレス>:3443` でも待ち受けます。
PC の IP アドレスは `ip addr`(Linux)や `ipconfig`(Windows)で確認してください。

スマホ・タブレットを **PC と同じ Wi-Fi** につなぎ、ブラウザで
`https://<PCのIPアドレス>:3443` を開きます。
自己署名証明書のため初回に警告が出ますが、「詳細設定」→「アクセスする」で進めます。

### 3. スキャンして登録する

1. 「バーコードスキャン」タブで **スキャン開始** を押し、カメラを許可
2. 本の裏表紙の **上段バーコード(978 で始まる方)** を枠内に写す
   (日本の書籍の下段バーコード 192… は自動的に無視されます)
3. 表紙・タイトル・著者・内容の概要が表示されるので **「bookscope に登録」** を押す
4. バーコードが読みにくい本は、ISBN の手入力でも検索できます

### 4. 蔵書一覧を見る

「蔵書一覧」タブで登録済みの書籍を一覧表示します。

- タイトル・著者・出版社・ISBN での絞り込み検索
- 登録順・タイトル順・出版日順などの並び替え
- タブレット・PC では表形式、スマホではカード形式で自動切替
- CSV 出力(Excel でそのまま開けます)
- 不要になった書籍の削除

## 対応ブラウザ

| 環境 | スキャン方式 |
|---|---|
| Android の Chrome / Edge | BarcodeDetector API(ネイティブ、高速) |
| iPhone / iPad の Safari | ZXing(JavaScript フォールバック) |
| PC ブラウザ | Web カメラがあれば同様にスキャン可、なければ手入力 |

## API

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/books` | 登録済み書籍の一覧を取得 |
| POST | `/api/books` | 書籍を登録(同じ ISBN は 409 で重複エラー) |
| DELETE | `/api/books/:id` | 書籍を削除 |

書籍データの形式:

```json
{
  "id": "uuid",
  "isbn": "9784873115658",
  "title": "書籍タイトル",
  "author": "著者名",
  "publisher": "出版社",
  "pubdate": "2020-01-01",
  "cover": "https://cover.openbd.jp/....jpg",
  "description": "内容の概要…",
  "registeredAt": "2026-09-11T00:00:00.000Z"
}
```

## ディレクトリ構成

```
bookscope/
├── server.js        # 依存ゼロの Node.js サーバー(静的配信 + REST API)
├── public/
│   ├── index.html   # スキャン画面 + 蔵書一覧(タブ切替)
│   ├── app.js       # スキャン・書誌情報取得・一覧表示のロジック
│   └── style.css    # スマホ・タブレット対応レスポンシブデザイン
├── data/
│   └── books.json   # 蔵書データ(自動生成、git 管理外)
└── certs/           # HTTPS 用証明書(任意、git 管理外)
```

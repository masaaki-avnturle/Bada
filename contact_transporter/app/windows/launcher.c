/*
 * launcher.c — Bada アプリの Windows 10 / 11 ランチャー (論文 PDF から作ったアプリ用)
 *
 * この EXE の末尾に、アプリ一式 (index.html = Bada 処理系 + 作ったアプリ、.bada ソース、論文 PDF …)
 * が付け足されています。起動すると
 *   1. %LOCALAPPDATA%\BadaApps\<アプリ ID>\ に展開し
 *   2. Windows 10 / 11 標準の Microsoft Edge をアプリ ウィンドウ (--app) で開きます
 *      (Edge が見つからなければ既定のブラウザで開く)
 *
 *   launcher.exe --extract <dir>   展開だけして終了 (CI の動作確認用)
 *   launcher.exe --info            同梱ファイルの一覧を表示
 *
 * 末尾の形式:  "BADAPKG1" u32 個数 { u32 名前長 名前(UTF-8) u64 サイズ データ }…  u64 先頭位置 "BADAEND1"
 *
 * ビルド: x86_64-w64-mingw32-gcc -O2 -municode -mwindows launcher.c -o bada-launcher.exe -lshell32
 */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#include <windows.h>
#include <shellapi.h>
#include <shlobj.h>
#include <stdio.h>
#include <stdint.h>
#include <wchar.h>

static void fail(const wchar_t *msg) {
  MessageBoxW(NULL, msg, L"Bada アプリ", MB_OK | MB_ICONERROR);
  ExitProcess(1);
}

static int readAt(HANDLE h, uint64_t off, void *buf, DWORD n) {
  LARGE_INTEGER li; li.QuadPart = (LONGLONG)off;
  if (!SetFilePointerEx(h, li, NULL, FILE_BEGIN)) return 0;
  DWORD got = 0;
  return ReadFile(h, buf, n, &got, NULL) && got == n;
}

static void ensureDir(const wchar_t *dir) {
  wchar_t tmp[MAX_PATH * 2];
  wcsncpy(tmp, dir, MAX_PATH * 2 - 1); tmp[MAX_PATH * 2 - 1] = 0;
  for (wchar_t *p = tmp + 3; *p; p++) if (*p == L'\\') { *p = 0; CreateDirectoryW(tmp, NULL); *p = L'\\'; }
  CreateDirectoryW(tmp, NULL);
}

int wmain(int argc, wchar_t **argv) {
  wchar_t self[MAX_PATH * 2];
  GetModuleFileNameW(NULL, self, MAX_PATH * 2);
  HANDLE h = CreateFileW(self, GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
  if (h == INVALID_HANDLE_VALUE) fail(L"自分自身を開けませんでした");
  LARGE_INTEGER size; GetFileSizeEx(h, &size);
  unsigned char tail[16];
  if (size.QuadPart < 32 || !readAt(h, (uint64_t)size.QuadPart - 16, tail, 16) || memcmp(tail + 8, "BADAEND1", 8) != 0)
    fail(L"アプリ一式が付いていません。Contact Transporter Studio の「論文→アプリ」から作った EXE を使ってください。");
  uint64_t start; memcpy(&start, tail, 8);
  unsigned char magic[12];
  if (!readAt(h, start, magic, 12) || memcmp(magic, "BADAPKG1", 8) != 0) fail(L"アプリ一式が壊れています");
  uint32_t count; memcpy(&count, magic + 8, 4);

  int extractOnly = 0, infoOnly = 0;
  wchar_t dir[MAX_PATH * 2] = L"";
  if (argc >= 3 && wcscmp(argv[1], L"--extract") == 0) { extractOnly = 1; wcsncpy(dir, argv[2], MAX_PATH * 2 - 1); }
  if (argc >= 2 && wcscmp(argv[1], L"--info") == 0) infoOnly = 1;

  // 1 回目の走査: アプリ ID (app.id) を読む
  uint64_t off = start + 12;
  char appId[128] = "bada-app";
  for (uint32_t i = 0; i < count; i++) {
    uint32_t nlen; uint64_t len; char name[512];
    if (!readAt(h, off, &nlen, 4) || nlen >= sizeof(name)) fail(L"アプリ一式が壊れています (名前)");
    if (!readAt(h, off + 4, name, nlen)) fail(L"アプリ一式が壊れています");
    name[nlen] = 0;
    if (!readAt(h, off + 4 + nlen, &len, 8)) fail(L"アプリ一式が壊れています (サイズ)");
    if (strcmp(name, "app.id") == 0 && len < sizeof(appId)) { readAt(h, off + 12 + nlen, appId, (DWORD)len); appId[len] = 0; }
    if (infoOnly) printf("%s  %llu bytes\n", name, (unsigned long long)len);
    off += 12 + nlen + len;
  }
  if (infoOnly) return 0;
  if (!extractOnly) {
    wchar_t base[MAX_PATH];
    if (FAILED(SHGetFolderPathW(NULL, CSIDL_LOCAL_APPDATA, NULL, 0, base))) fail(L"%LOCALAPPDATA% が見つかりません");
    wchar_t wid[128]; MultiByteToWideChar(CP_UTF8, 0, appId, -1, wid, 128);
    swprintf(dir, MAX_PATH * 2, L"%ls\\BadaApps\\%ls", base, wid);
  }
  ensureDir(dir);

  // 2 回目の走査: 展開
  off = start + 12;
  wchar_t indexPath[MAX_PATH * 2] = L"";
  for (uint32_t i = 0; i < count; i++) {
    uint32_t nlen; uint64_t len; char name[512];
    readAt(h, off, &nlen, 4); readAt(h, off + 4, name, nlen); name[nlen] = 0; readAt(h, off + 4 + nlen, &len, 8);
    wchar_t wname[512], path[MAX_PATH * 2];
    MultiByteToWideChar(CP_UTF8, 0, name, -1, wname, 512);
    for (wchar_t *p = wname; *p; p++) if (*p == L'/' || *p == L'\\' || *p == L':') *p = L'_';
    swprintf(path, MAX_PATH * 2, L"%ls\\%ls", dir, wname);
    HANDLE o = CreateFileW(path, GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (o == INVALID_HANDLE_VALUE) fail(L"展開先に書き込めませんでした");
    uint64_t done = 0; static unsigned char buf[1 << 16];
    while (done < len) {
      DWORD n = (DWORD)((len - done) < sizeof(buf) ? (len - done) : sizeof(buf)), w = 0;
      if (!readAt(h, off + 12 + nlen + done, buf, n)) fail(L"読み込みに失敗しました");
      WriteFile(o, buf, n, &w, NULL); done += n;
    }
    CloseHandle(o);
    if (strcmp(name, "index.html") == 0) wcsncpy(indexPath, path, MAX_PATH * 2 - 1);
    off += 12 + nlen + len;
  }
  CloseHandle(h);
  if (extractOnly) return indexPath[0] ? 0 : 2;
  if (!indexPath[0]) fail(L"index.html がありません");

  // Edge のアプリ ウィンドウで開く (Windows 10 / 11 に標準搭載)
  wchar_t url[MAX_PATH * 3] = L"file:///", args[MAX_PATH * 4];
  size_t k = wcslen(url);
  for (wchar_t *p = indexPath; *p && k < MAX_PATH * 3 - 4; p++) {
    if (*p == L'\\') url[k++] = L'/';
    else if (*p == L' ') { url[k++] = L'%'; url[k++] = L'2'; url[k++] = L'0'; }
    else url[k++] = *p;
  }
  url[k] = 0;
  swprintf(args, MAX_PATH * 4, L"--app=\"%ls\"", url);
  if ((INT_PTR)ShellExecuteW(NULL, L"open", L"msedge.exe", args, NULL, SW_SHOWNORMAL) > 32) return 0;
  if ((INT_PTR)ShellExecuteW(NULL, L"open", indexPath, NULL, NULL, SW_SHOWNORMAL) > 32) return 0;
  fail(L"ブラウザを起動できませんでした");
  return 1;
}

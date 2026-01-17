以下は、実装やビルド補助目的で使える簡易的な `curl/curl.h` のモックヘッダです。libcurl 本体の完全な仕様を再現するものではありませんが、典型的な最小限の API（`CURL` 型、`CURLcode`、`curl_easy_*` とグローバル初期化、`curl_slist` ヘルダ操作、主要な `CURLOPT_*` 定数、`CURLOPT_*` の型定義など）を定義しています。実際の libcurl を使う環境では本物のヘッダ（システムの libcurl 開発パッケージ）を使ってください。

```c
/* curl/curl.h - minimal mock header for libcurl-like API
 * Not a full replacement for real libcurl headers.
 */

#ifndef CURL_CURL_H
#define CURL_CURL_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>

  /* Opaque easy handle */
  typedef struct Curl_easy CURL;

  /* Simple linked-list for headers */
  struct curl_slist {
    char *data;
    struct curl_slist *next;
  };

  /* Return codes (subset) */
  typedef enum {
    CURLE_OK = 0,
    CURLE_UNSUPPORTED_PROTOCOL = 1,
    CURLE_FAILED_INIT = 2,
    CURLE_URL_MALFORMAT = 3,
    CURLE_COULDNT_CONNECT = 7,
    CURLE_WRITE_ERROR = 23,
    CURLE_OUT_OF_MEMORY = 27,
    CURLE_OPERATION_TIMEDOUT = 28,
    /* ... add more as needed */
  } CURLcode;

  /* Option type used by curl_easy_setopt (simplified) */
  typedef int CURLoption;

  /* Typical option constants (subset) */
#define CURLOPT_URL             10002
#define CURLOPT_WRITEFUNCTION   20011
#define CURLOPT_WRITEDATA       10001
#define CURLOPT_POSTFIELDS      10015
#define CURLOPT_POSTFIELDSIZE   60
#define CURLOPT_HTTPHEADER      10023
#define CURLOPT_TIMEOUT         13
#define CURLOPT_FOLLOWLOCATION  52
#define CURLOPT_USERAGENT       10018
#define CURLOPT_VERBOSE         41

  /* Function pointer type for write callback:
   * size * nmemb bytes received, returns number of bytes actually taken.
   */
  typedef size_t (*curl_write_callback)(char *ptr, size_t size, size_t nmemb, void *userdata);

  /* Global init/cleanup */
  typedef long curl_global_init_flag;
#define CURL_GLOBAL_DEFAULT 3L

  int curl_global_init(curl_global_init_flag flags);
  void curl_global_cleanup(void);

  /* Easy interface */
  CURL *curl_easy_init(void);
  void curl_easy_cleanup(CURL *handle);
  CURLcode curl_easy_perform(CURL *handle);

  /* Simplified generic setter: supports pointers, long/int and function pointers.
   * Real libcurl uses variadic and typed macro magic; this is a simple prototype.
   */
  int curl_easy_setopt(CURL *handle, CURLoption option, ...);

  /* Error string */
  const char *curl_easy_strerror(CURLcode code);

  /* Header list helpers */
  struct curl_slist *curl_slist_append(struct curl_slist *list, const char *string);
  void curl_slist_free_all(struct curl_slist *list);

  /* Version string (optional) */
  const char *curl_version(void);

#ifdef __cplusplus
}
#endif

#endif /* CURL_CURL_H */
```

必要なら、このモックに対応する簡易実装（スタブ実装）も作成できます。

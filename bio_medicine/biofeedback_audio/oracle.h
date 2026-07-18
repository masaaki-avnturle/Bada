/*
 * oracle.h — 娯楽用「オラクル(お告げ)」メッセージ生成
 *
 * ⚠️ これは娯楽(エンタメ)機能です。未来予知でも「アカシックレコード」でも
 *    ありません。出力は擬似乱数から選ばれた定型メッセージであり、いかなる
 *    予知・透視・診断の根拠にもなりません。演出としてバイオフィードバック音
 *    (プリセット)と連動させるだけのものです。
 *
 * 仕組み:
 *   - 種(seed): 呼び出し側が渡す数値(センサー値やカウンタ等)を混ぜて決定。
 *   - seed からメッセージ(定型文)と、連動プリセット index を選ぶ。
 *   - 同じ seed なら同じ結果(再現性あり=占いではなく決定的関数)。
 */
#ifndef ORACLE_H
#define ORACLE_H

#include <stddef.h>

typedef struct {
    const char *jp;        /* 日本語メッセージ */
    const char *en;        /* 英語メッセージ */
    int         preset;    /* 連動する音プリセット index(0..) */
    int         mood;      /* 0=calm,1=focus,2=uplift,3=rest (色/演出用) */
} OracleCard;

/* 用意されているカード総数 */
size_t oracle_card_count(void);

/*
 * seed(任意の数値)から 1 枚引く。preset_count は連動プリセット数の上限。
 * 返り値のポインタは静的テーブル内(解放不要・書き換え不可)。
 */
const OracleCard *oracle_draw(unsigned long seed, size_t preset_count);

/* mood の表示名(日本語/英語) */
const char *oracle_mood_jp(int mood);
const char *oracle_mood_en(int mood);

/* 免責文(1 行) */
const char *oracle_disclaimer_jp(void);
const char *oracle_disclaimer_en(void);

#endif /* ORACLE_H */

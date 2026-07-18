/*
 * oracle.c — 娯楽用「オラクル(お告げ)」メッセージ生成の実装
 *
 * ⚠️ 娯楽機能です。未来予知・アカシックレコード等ではありません。
 *    擬似乱数で定型文を選ぶだけの決定的関数です(oracle.h 参照)。
 */
#include "oracle.h"

/*
 * カード一覧。前向き/中立の一般的な言い回しに限定し、
 * 医療・健康・投資など「助言」と誤解されうる断定は避ける。
 */
static const OracleCard CARDS[] = {
    { "今日は小さな一歩が流れを変える。",           "A small step today shifts the current.",        0, 2 },
    { "焦らず呼吸を整えると視界が開ける。",         "Steady your breath; the view will open.",       2, 0 },
    { "耳を澄ませば、答えはもうそばにある。",       "Listen closely; the answer is already near.",   3, 0 },
    { "手放すことで、次の余白が生まれる。",         "Letting go makes room for what's next.",        1, 3 },
    { "静けさの中に、あなたの軸が見える。",         "In the quiet, your center becomes clear.",      2, 0 },
    { "巡り合わせは、準備した人に微笑む。",         "Fortune favors the one who prepared.",          4, 2 },
    { "今の集中が、明日の景色をつくる。",           "Today's focus shapes tomorrow's view.",         5, 1 },
    { "休むことも前進のうち。",                     "Rest, too, is part of moving forward.",         2, 3 },
    { "小さな親切が、思わぬ縁を結ぶ。",             "A small kindness ties an unexpected bond.",     6, 2 },
    { "迷いは選択肢が豊かな証。",                   "Hesitation is a sign of rich options.",         7, 1 },
    { "波に逆らわず、リズムに乗る。",               "Don't fight the wave; ride its rhythm.",        8, 0 },
    { "灯りは、暗さを知る者に価値を持つ。",         "Light matters most to those who knew the dark.", 9, 2 },
    { "整えた足元が、遠くへ運ぶ。",                 "Firm footing carries you far.",                 10, 1 },
    { "深い息が、こわばりをほどく。",               "A deep breath loosens what is tight.",          11, 3 },
    { "縁は急がず、しかし確かに近づく。",           "Connections approach slowly but surely.",       12, 0 },
    { "今日の穏やかさを、明日への種に。",           "Let today's calm be a seed for tomorrow.",      13, 3 },
};
static const size_t CARD_COUNT = sizeof(CARDS) / sizeof(CARDS[0]);

size_t oracle_card_count(void) { return CARD_COUNT; }

/* splitmix64 相当の簡易ハッシュ(移植性重視・32/64bit どちらでも安定) */
static unsigned long mix(unsigned long x) {
    x += 0x9E3779B97F4A7C15UL;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9UL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBUL;
    x =  x ^ (x >> 31);
    return x;
}

const OracleCard *oracle_draw(unsigned long seed, size_t preset_count) {
    unsigned long h = mix(seed);
    const OracleCard *c = &CARDS[h % CARD_COUNT];
    /* preset が実在レンジを超える場合に備え、返すのは静的カードのまま。
     * 呼び出し側は c->preset を preset_count でクランプして使う。 */
    (void)preset_count;
    return c;
}

const char *oracle_mood_jp(int mood) {
    switch (mood) {
        case 0: return "静穏";
        case 1: return "集中";
        case 2: return "高揚";
        case 3: return "休息";
        default: return "-";
    }
}
const char *oracle_mood_en(int mood) {
    switch (mood) {
        case 0: return "calm";
        case 1: return "focus";
        case 2: return "uplift";
        case 3: return "rest";
        default: return "-";
    }
}

const char *oracle_disclaimer_jp(void) {
    return "※娯楽機能です。未来予知ではありません。乱数で選ばれた定型文です。";
}
const char *oracle_disclaimer_en(void) {
    return "For entertainment only. Not a prediction; a randomly chosen phrase.";
}

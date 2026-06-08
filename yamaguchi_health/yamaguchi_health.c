/*
 * YamaguchiHealth  --  wellness / breathing / meditation guidance (console app)
 * ---------------------------------------------------------------------------
 * IMPORTANT / 重要:
 *   This is an EDUCATIONAL & WELLNESS DEMO program. It is NOT a medical device.
 *   - It does NOT measure real blood values (GPT/ALT, WBC, RBC, creatinine ...).
 *     External temperature/infrared sensors physically cannot read blood
 *     chemistry; any value shown here is clearly-labelled SIMULATED demo data.
 *   - It does NOT administer or reproduce the effect of any medication. No
 *     sound/light "frequency" can deliver a drug's pharmacology. Nothing here
 *     dispenses, simulates, or substitutes for medication.
 *   - The "silent talk" feature is a MANUAL note logger, not mind/lip reading.
 *   This program cannot diagnose, treat, or replace professional medical care.
 *   If you are unwell or in distress, please contact a doctor or, in Japan,
 *   the "いのちの電話" line (0570-783-556) / emergency services (119).
 * ---------------------------------------------------------------------------
 * Build:   make            (or: cc -O2 -o yamaguchi_health yamaguchi_health.c)
 * Android: see README.md for the NDK / APK packaging notes.
 */

#define _POSIX_C_SOURCE 200809L  /* strdup, localtime, etc. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define LINE_MAX_LEN   512
#define LOG_DIR        "yh_logs"

/* ----------------------------------------------------------------------- */
/* small helpers                                                           */
/* ----------------------------------------------------------------------- */

static void flush_stdin(void)
{
    int c;
    while ((c = getchar()) != '\n' && c != EOF) { /* discard */ }
}

/* read a trimmed line; returns 0 on EOF */
static int read_line(char *buf, size_t n)
{
    if (!fgets(buf, (int)n, stdin))
        return 0;
    size_t len = strlen(buf);
    while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r'))
        buf[--len] = '\0';
    return 1;
}

static void timestamp(char *buf, size_t n)
{
    time_t t = time(NULL);
    struct tm *tm = localtime(&t);
    strftime(buf, n, "%Y-%m-%d %H:%M:%S", tm);
}

static void ensure_log_dir(void)
{
    /* portable enough for POSIX / Android; ignore "already exists" */
#if defined(_WIN32)
    system("mkdir " LOG_DIR " >NUL 2>&1");
#else
    if (system("mkdir -p " LOG_DIR " >/dev/null 2>&1") != 0) {
        /* fall back silently; saving will just report the error */
    }
#endif
}

static void pause_enter(void)
{
    printf("\n  [Enter で戻る / press Enter to continue] ");
    fflush(stdout);
    flush_stdin();
}

/* ----------------------------------------------------------------------- */
/* 1. Simulated biosensor dashboard  (DEMO ONLY -- not a measurement)       */
/* ----------------------------------------------------------------------- */

static double demo_value(double lo, double hi)
{
    double r = (double)rand() / (double)RAND_MAX;
    return lo + r * (hi - lo);
}

static void sensor_dashboard(void)
{
    printf("\n================= センサー ダッシュボード (SIMULATED) ===========\n");
    printf("  ** これはデモ表示です。実測ではありません。**\n");
    printf("  ** DEMO values only -- NOT a real medical measurement.       **\n");
    printf("  外部の温度/赤外線センサーでは血液検査値は測定できません。\n");
    printf("---------------------------------------------------------------\n");
    printf("  体表温度 / skin temp (IR)      : %5.1f  C    [simulated]\n", demo_value(35.5, 37.2));
    printf("  室温 / ambient (thermistor)    : %5.1f  C    [simulated]\n", demo_value(20.0, 28.0));
    printf("  心拍 / heart-rate (demo)       : %5.0f  bpm  [simulated]\n", demo_value(58, 92));
    printf("---------------------------------------------------------------\n");
    printf("  以下は *推定不能* の項目です。本アプリでは表示しません:\n");
    printf("  (cannot be inferred externally -- intentionally NOT shown)\n");
    printf("    GPT/ALT, WBC(白血球), RBC(赤血球), クレアチニン(creatinine)\n");
    printf("    -> これらは採血と臨床検査が必要です。\n");
    printf("===============================================================\n");
    pause_enter();
}

/* ----------------------------------------------------------------------- */
/* 2. Silent-talk note logger  (Start / Stop / Record)                      */
/*    Honest stand-in: you type the text; nothing is read from sensors.     */
/* ----------------------------------------------------------------------- */

static void silent_talk(void)
{
    char buf[LINE_MAX_LEN];
    char *lines[1024];
    int  count = 0;
    int  running = 0;

    printf("\n================= サイレントトーク / Silent-Talk ===============\n");
    printf("  注: 赤外線で思考や唇を読み取ることはできません。\n");
    printf("  これは手入力のメモ記録です (an honest manual note logger).\n");
    printf("  コマンド: start=開始  stop=停止  record=保存  quit=戻る\n");
    printf("  start 中に入力した行が文字化(記録)されます。\n");
    printf("---------------------------------------------------------------\n");

    for (;;) {
        printf("%s> ", running ? "[REC]" : "[--] ");
        fflush(stdout);
        if (!read_line(buf, sizeof buf))
            break;

        if (strcmp(buf, "start") == 0) {
            running = 1;
            printf("  ... 聞き取り開始 (started). テキストを入力してください。\n");
        } else if (strcmp(buf, "stop") == 0) {
            running = 0;
            printf("  ... 停止 (stopped). 行数=%d\n", count);
        } else if (strcmp(buf, "record") == 0) {
            ensure_log_dir();
            char ts[32]; timestamp(ts, sizeof ts);
            char path[128];
            snprintf(path, sizeof path, "%s/silenttalk_%ld.txt", LOG_DIR, (long)time(NULL));
            FILE *f = fopen(path, "w");
            if (!f) { printf("  保存失敗 (could not open %s)\n", path); continue; }
            fprintf(f, "# Silent-Talk note  %s\n", ts);
            for (int i = 0; i < count; i++)
                fprintf(f, "%s\n", lines[i]);
            fclose(f);
            printf("  保存しました -> %s  (%d 行)\n", path, count);
        } else if (strcmp(buf, "quit") == 0 || strcmp(buf, "q") == 0) {
            break;
        } else if (running) {
            if (count < (int)(sizeof lines / sizeof lines[0])) {
                lines[count] = strdup(buf);
                if (lines[count]) count++;
                printf("    文字化: \"%s\"\n", buf);
            } else {
                printf("  バッファが一杯です。record で保存してください。\n");
            }
        } else {
            printf("  (start を押すまで記録しません)\n");
        }
    }

    for (int i = 0; i < count; i++)
        free(lines[i]);
    printf("===============================================================\n");
}

/* ----------------------------------------------------------------------- */
/* 3. Breathing & meditation guidance  (Start / Stop / Record)              */
/* ----------------------------------------------------------------------- */

typedef struct {
    const char *name_jp;
    const char *name_en;
    int inhale, hold, exhale, hold2;   /* seconds */
    const char *note;
} BreathPreset;

static const BreathPreset PRESETS[] = {
    { "秘伝功",            "Hiden-ko deep breathing",   4, 4, 8, 0,
      "ゆっくり長い呼気で副交感神経を整える伝統的な呼吸。" },
    { "養生功",            "Yojo-ko balanced breathing", 5, 2, 5, 2,
      "吸気と呼気を均等に、滑らかに循環させる養生の呼吸。" },
    { "Super Reading 瞑想法", "SRS meditation",          4, 7, 8, 0,
      "4-7-8 リズムで集中と鎮静を促す瞑想呼吸。" },
    { "Super Reading 呼吸法", "SRS breathing",           6, 0, 6, 0,
      "毎分5回前後のコヒーレント呼吸で心身を安定させる。" },
    { "活夢法",            "Lucid-dream prep breathing", 4, 4, 6, 2,
      "就眠前のリラックス誘導。眠りに入りやすく整える。" },
    { "クジラ瞑想 (太平洋)", "Pacific Whale meditation",  7, 3, 11, 0,
      "広い海を悠々と泳ぐイメージ。とても長い呼気でゆったりと。" },
};
static const int N_PRESETS = (int)(sizeof PRESETS / sizeof PRESETS[0]);

/* run one guided session; returns number of completed cycles */
static int run_breathing(const BreathPreset *p, int cycles, char *log, size_t logn)
{
    size_t used = 0;
    char ts[32]; timestamp(ts, sizeof ts);
    used += (size_t)snprintf(log + used, logn - used,
              "# Breathing session: %s (%s)\n# start: %s\n# pattern in=%d hold=%d ex=%d hold=%d\n",
              p->name_jp, p->name_en, ts, p->inhale, p->hold, p->exhale, p->hold2);

    printf("\n  >>> %s / %s  開始 (Start)\n", p->name_jp, p->name_en);
    printf("      %s\n", p->note);
    printf("      (中断するには Ctrl-C)\n\n");

    int done = 0;
    for (int c = 1; c <= cycles; c++) {
        printf("  サイクル %d/%d\n", c, cycles);

        printf("    吸う / inhale "); fflush(stdout);
        for (int s = 0; s < p->inhale; s++) { printf("."); fflush(stdout); sleep(1); }
        printf("  (%ds)\n", p->inhale);

        if (p->hold) {
            printf("    止める / hold "); fflush(stdout);
            for (int s = 0; s < p->hold; s++) { printf("."); fflush(stdout); sleep(1); }
            printf("  (%ds)\n", p->hold);
        }

        printf("    吐く / exhale "); fflush(stdout);
        for (int s = 0; s < p->exhale; s++) { printf("."); fflush(stdout); sleep(1); }
        printf("  (%ds)\n", p->exhale);

        if (p->hold2) {
            printf("    止める / hold "); fflush(stdout);
            for (int s = 0; s < p->hold2; s++) { printf("."); fflush(stdout); sleep(1); }
            printf("  (%ds)\n", p->hold2);
        }
        printf("\n");
        done = c;
    }

    char te[32]; timestamp(te, sizeof te);
    snprintf(log + used, logn - used,
             "# end: %s\n# completed cycles: %d\n", te, done);
    printf("  <<< 停止 (Stop). 完了サイクル = %d\n", done);
    return done;
}

static void breathing_menu(void)
{
    char buf[LINE_MAX_LEN];

    for (;;) {
        printf("\n=============== 呼吸誘導 / Breathing Guidance ==================\n");
        for (int i = 0; i < N_PRESETS; i++)
            printf("  %d) %-22s  in%d hold%d ex%d hold%d\n",
                   i + 1, PRESETS[i].name_jp,
                   PRESETS[i].inhale, PRESETS[i].hold, PRESETS[i].exhale, PRESETS[i].hold2);
        printf("  0) 戻る / back\n");
        printf("  選択 / select: ");
        fflush(stdout);

        if (!read_line(buf, sizeof buf)) return;
        int sel = atoi(buf);
        if (sel == 0) return;
        if (sel < 1 || sel > N_PRESETS) { printf("  範囲外です。\n"); continue; }

        const BreathPreset *p = &PRESETS[sel - 1];
        printf("  サイクル数 / cycles (例 5): ");
        fflush(stdout);
        if (!read_line(buf, sizeof buf)) return;
        int cycles = atoi(buf);
        if (cycles < 1) cycles = 1;
        if (cycles > 60) cycles = 60;

        char log[1024];
        int done = run_breathing(p, cycles, log, sizeof log);

        printf("\n  この記録を保存しますか? record と入力 / 他=破棄: ");
        fflush(stdout);
        if (read_line(buf, sizeof buf) && strcmp(buf, "record") == 0) {
            ensure_log_dir();
            char path[128];
            snprintf(path, sizeof path, "%s/breath_%ld.txt", LOG_DIR, (long)time(NULL));
            FILE *f = fopen(path, "w");
            if (f) {
                fputs(log, f);
                fclose(f);
                printf("  保存しました -> %s (cycles=%d)\n", path, done);
            } else {
                printf("  保存失敗 (could not write %s)\n", path);
            }
        }
    }
}

/* ----------------------------------------------------------------------- */
/* 4. Wellness / nutrition info  (information only -- no medical claims)     */
/* ----------------------------------------------------------------------- */

static void wellness_info(void)
{
    printf("\n================ ウェルネス情報 / Wellness Info ================\n");
    printf("  ※ 情報提供のみ。診断・治療・服薬指導ではありません。\n");
    printf("  ※ Information only -- not medical advice or dosing guidance.\n");
    printf("---------------------------------------------------------------\n");
    printf("  リシン (L-lysine): 必須アミノ酸。肉・魚・豆・乳製品に含まれる\n");
    printf("    たんぱく質構成成分。サプリは食品として市販されています。\n");
    printf("  水分補給: こまめな水分は体温調節・集中の維持に役立ちます。\n");
    printf("  睡眠衛生: 就寝前の深い呼吸と一定の就寝時刻が休息を助けます。\n");
    printf("---------------------------------------------------------------\n");
    printf("  服薬・症状については必ず医師・薬剤師にご相談ください。\n");
    printf("===============================================================\n");
    pause_enter();
}

/* ----------------------------------------------------------------------- */
/* 5. About / disclaimer                                                    */
/* ----------------------------------------------------------------------- */

static void about(void)
{
    printf("\n==================== About / 免責事項 =========================\n");
    printf("  YamaguchiHealth -- 呼吸・瞑想ガイドのウェルネスデモ。\n");
    printf("  ・医療機器ではありません。診断・治療は行えません。\n");
    printf("  ・外部センサーで血液検査値(GPT/白血球/赤血球/クレアチニン等)\n");
    printf("    は測定できません。表示はすべてデモ(模擬)です。\n");
    printf("  ・いかなる薬の効果も、周波数等で再現・投与はできません。\n");
    printf("  ・サイレントトークは手入力のメモ記録機能です。\n");
    printf("  体調がすぐれない時・つらい時は、医療機関にご相談ください。\n");
    printf("  日本: いのちの電話 0570-783-556 / 緊急 119\n");
    printf("===============================================================\n");
    pause_enter();
}

/* ----------------------------------------------------------------------- */
/* main menu                                                                */
/* ----------------------------------------------------------------------- */

int main(void)
{
    char buf[LINE_MAX_LEN];
    srand((unsigned)time(NULL));

    printf("\n");
    printf("  #############################################################\n");
    printf("  #             YamaguchiHealth  (wellness demo)              #\n");
    printf("  #   呼吸誘導・瞑想・セルフケアの学習用アプリ (非医療機器)   #\n");
    printf("  #############################################################\n");

    for (;;) {
        printf("\n----------------------- メインメニュー -----------------------\n");
        printf("  1) センサー ダッシュボード (SIMULATED)\n");
        printf("  2) サイレントトーク (start/stop/record メモ記録)\n");
        printf("  3) 呼吸誘導 / 瞑想 (秘伝功・養生功・SRS・クジラ瞑想)\n");
        printf("  4) ウェルネス情報 (リシン 等)\n");
        printf("  5) About / 免責事項\n");
        printf("  0) 終了 / quit\n");
        printf("  選択 / select: ");
        fflush(stdout);

        if (!read_line(buf, sizeof buf))
            break;

        switch (atoi(buf)) {
            case 1: sensor_dashboard(); break;
            case 2: silent_talk();      break;
            case 3: breathing_menu();   break;
            case 4: wellness_info();    break;
            case 5: about();            break;
            case 0: printf("  おつかれさまでした。\n"); return 0;
            default: printf("  1-5 または 0 を入力してください。\n"); break;
        }
    }
    return 0;
}

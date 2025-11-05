/*以下は、前回の GTK アプリを拡張し、ファイル名にマウスをポイント（hover）またはクリックするとアプリ内のプレビュー領域（GtkTextView）にそのファイル内容を表示する C ソースコードです。外部端末を開かずアプリ内でプレビューするため、安全かつ実用的です。大きなファイル対策として最大文字数を制限しています。

コンパイル例:
gcc `pkg-config --cflags gtk+-3.0` -o hover_preview hover_preview.c `pkg-config --libs gtk+-3.0`

コード:
```c
*/
// hover_preview.c
#define _GNU_SOURCE
#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>

#define MAX_PREVIEW_BYTES (256 * 1024) /* 256KB max to preview */
#define PREVIEW_LINES_LIMIT 2000        /* optional line limit */

typedef struct {
  gchar *dirpath;
  GtkWidget *textview;
} AppData;

/* Read a file into a GString but limit bytes and lines for performance */
static gboolean read_file_preview(const char *filepath, GString **out, GError **error) {
  *out = g_string_new(NULL);
  FILE *f = fopen(filepath, "rb");
  if (!f) {
    g_set_error(error, G_FILE_ERROR, g_file_error_from_errno(errno), "Failed to open: %s", g_strerror(errno));
    return FALSE;
  }

  size_t total = 0;
  size_t lines = 0;
  char buf[4096];
  while (!feof(f) && total < MAX_PREVIEW_BYTES && lines < PREVIEW_LINES_LIMIT) {
    size_t r = fread(buf, 1, sizeof(buf), f);
    if (r == 0) break;
    /* Append but enforce byte limit precisely */
    size_t to_append = r;
    if (total + to_append > MAX_PREVIEW_BYTES) to_append = MAX_PREVIEW_BYTES - total;
    g_string_append_len(*out, buf, to_append);
    total += to_append;
    for (size_t i = 0; i < to_append; ++i) if (buf[i] == '\n') lines++;
    if (to_append < r) break;
  }
  if (!feof(f)) {
    g_string_append(*out, "\n--- (preview truncated) ---");
  }
  fclose(f);
  return TRUE;
}

/* Display preview text in the app's textview (main thread) */
static void display_preview(AppData *ad, const char *filename) {
  if (!ad || !ad->dirpath || !ad->textview || !filename) return;

  char *full = g_build_filename(ad->dirpath, filename, NULL);
  GError *err = NULL;
  GString *content = NULL;
  if (!read_file_preview(full, &content, &err)) {
    /* show error message */
    GtkTextBuffer *buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(ad->textview));
    gtk_text_buffer_set_text(buf, err->message ? err->message : "(error reading file)", -1);
    g_clear_error(&err);
    g_free(full);
    if (content) g_string_free(content, TRUE);
    return;
  }

  /* If file is binary-ish, we may choose to show a notice.
     Simple heuristic: if a NUL byte exists in preview, mark as binary. */
  gboolean binary = FALSE;
  if (content->len > 0 && memchr(content->str, '\0', content->len) != NULL) binary = TRUE;

  GtkTextBuffer *buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(ad->textview));
  if (binary) {
    gtk_text_buffer_set_text(buf, "(binary file preview not available)", -1);
    } else {
        /* set text, ensure UTF-8 validity: GTK expects UTF-8, but we'll trust content or replace invalids */
        gchar *utf8 = g_convert_with_fallback(content->str, content->len, "UTF-8", "UTF-8", "�", NULL, NULL, NULL);
        gtk_text_buffer_set_text(buf, utf8 ? utf8 : content->str, -1);
        g_free(utf8);
  }

  g_string_free(content, TRUE);
  g_free(full);
}

/* Callback for mouse hover (enter notify) */
static gboolean on_row_enter(GtkWidget *widget, GdkEvent *event, gpointer user_data) {
  AppData *ad = (AppData *)g_object_get_data(G_OBJECT(gtk_widget_get_toplevel(widget)), "appdata");
  const char *filename = (const char *)user_data;
  if (!ad || !filename) return FALSE;

  display_preview(ad, filename);
  return FALSE; /* allow other handlers */
}

/* Callback for row activate (clicked/pressed) - also show preview and optionally select */
static void on_row_activated(GtkListBox *box, GtkListBoxRow *row, gpointer user_data) {
  AppData *ad = (AppData *)user_data;
  GtkWidget *child = gtk_bin_get_child(GTK_BIN(row));
  const gchar *filename = gtk_label_get_text(GTK_LABEL(child));
  if (filename) display_preview(ad, filename);
}

/* Populate list box with regular files in directory */
static void populate_list(GtkListBox *listbox, const char *dirpath) {
  DIR *d = opendir(dirpath);
  if (!d) return;
  struct dirent *ent;
  while ((ent = readdir(d)) != NULL) {
    if (ent->d_name[0] == '.') continue; /* skip hidden */
    char *full = g_build_filename(dirpath, ent->d_name, NULL);
    struct stat st;
    if (stat(full, &st) == 0 && S_ISREG(st.st_mode)) {
      GtkWidget *row = gtk_list_box_row_new();
      GtkWidget *label = gtk_label_new(ent->d_name);
      gtk_label_set_xalign(GTK_LABEL(label), 0.0);
      gtk_container_add(GTK_CONTAINER(row), label);
      gtk_widget_set_margin_start(label, 6);
      gtk_widget_set_margin_top(label, 3);
      gtk_widget_set_margin_bottom(label, 3);

      /* enable enter-notify on row */
      gtk_widget_add_events(row, GDK_ENTER_NOTIFY_MASK);
      /* connect hover handler; pass filename (dup) */
      char *name_copy = g_strdup(ent->d_name);
      g_signal_connect(row, "enter-notify-event", G_CALLBACK(on_row_enter), name_copy);
      /* free name_copy when row is destroyed */
      g_signal_connect_swapped(row, "destroy", G_CALLBACK(g_free), name_copy);

      gtk_list_box_insert(listbox, row, -1);
    }
    g_free(full);
  }
  closedir(d);
  gtk_widget_show_all(GTK_WIDGET(listbox));
}

int main(int argc, char *argv[]) {
  gtk_init(&argc, &argv);

  const char *dirpath = (argc > 1) ? argv[1] : ".";
  struct stat st;
  if (stat(dirpath, &st) != 0 || !S_ISDIR(st.st_mode)) {
    g_printerr("Invalid directory: %s\n", dirpath);
    return 1;
  }

  AppData ad = {0};
  ad.dirpath = g_strdup(dirpath);

  GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  gtk_window_set_default_size(GTK_WINDOW(win), 800, 600);
  gtk_window_set_title(GTK_WINDOW(win), "Folder Hover Preview");

  /* main horizontal layout: left file list, right preview */
  GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
  gtk_container_set_border_width(GTK_CONTAINER(hbox), 6);
  gtk_container_add(GTK_CONTAINER(win), hbox);

  /* Left: scrolled list of files */
  GtkWidget *sc_left = gtk_scrolled_window_new(NULL, NULL);
  gtk_widget_set_size_request(sc_left, 300, -1);
  gtk_box_pack_start(GTK_BOX(hbox), sc_left, FALSE, TRUE, 0);

  GtkWidget *list = gtk_list_box_new();
  gtk_container_add(GTK_CONTAINER(sc_left), list);

  populate_list(GTK_LIST_BOX(list), dirpath);

  /* Connect activate (double-click or Enter) to show preview as well */
  g_signal_connect(list, "row-activated", G_CALLBACK(on_row_activated), &ad);

  /* Right: preview text view inside scrolled window */
  GtkWidget *sc_right = gtk_scrolled_window_new(NULL, NULL);
  gtk_box_pack_start(GTK_BOX(hbox), sc_right, TRUE, TRUE, 0);

  ad.textview = gtk_text_view_new();
  gtk_text_view_set_editable(GTK_TEXT_VIEW(ad.textview), FALSE);
  gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(ad.textview), GTK_WRAP_WORD_CHAR);
  gtk_container_add(GTK_CONTAINER(sc_right), ad.textview);

  /* store appdata on top-level for handlers to retrieve */
  g_object_set_data(G_OBJECT(win), "appdata", &ad);

  /* When window is destroyed, free resources */
  g_signal_connect(win, "destroy", G_CALLBACK(gtk_main_quit), NULL);

  gtk_widget_show_all(win);

  /* Optionally: select first file and show its preview */
  GtkListBoxRow *first = gtk_list_box_get_row_at_index(GTK_LIST_BOX(list), 0);
  if (first) {
    gtk_list_box_select_row(GTK_LIST_BOX(list), first);
    /* trigger activated to show preview */
    on_row_activated(GTK_LIST_BOX(list), first, &ad);
  }

  gtk_main();

  g_free(ad.dirpath);
  return 0;
}

/*
使い方:
- コンパイル（再掲）:
  gcc `pkg-config --cflags gtk+-3.0` -o hover_preview hover_preview.c `pkg-config --libs gtk+-3.0`
  - 実行:
  ./hover_preview /path/to/target/folder

必要なら、プレビュー更新の遅延（デバウンス）や検索フィルタ、シンタックスハイライト（GtkSourceView）を追加する改良版も作成します。どれを希望しますか？
*/

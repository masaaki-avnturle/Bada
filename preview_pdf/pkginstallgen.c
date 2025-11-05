// hover_preview_pdf.c
#define _GNU_SOURCE
#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#include <poppler.h>

#define MAX_PREVIEW_BYTES (256 * 1024)
#define PREVIEW_LINES_LIMIT 2000
#define PDF_PREVIEW_WIDTH 800
#define PDF_PREVIEW_HEIGHT 1000

typedef struct {
  gchar *dirpath;
  GtkWidget *preview_container; /* holds either textview or image */
  GtkWidget *textview;
  GtkWidget *image;
} AppData;

/* Read text preview (as before) */
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
    size_t to_append = r;
    if (total + to_append > MAX_PREVIEW_BYTES) to_append = MAX_PREVIEW_BYTES - total;
    g_string_append_len(*out, buf, to_append);
    total += to_append;
    for (size_t i = 0; i < to_append; ++i) if (buf[i] == '\n') lines++;
    if (to_append < r) break;
  }
  if (!feof(f)) g_string_append(*out, "\n--- (preview truncated) ---");
  fclose(f);
  return TRUE;
}

/* Utility: lowercase extension check */
static const char *get_extension_lower(const char *name) {
  const char *dot = strrchr(name, '.');
  if (!dot || dot == name) return "";
  return g_ascii_strdown(dot + 1, -1);
}

/* Render first page of PDF to GdkPixbuf, scaled to fit max_w/max_h.
   Returns newly g_object_ref'd GdkPixbuf or NULL on error. */
static GdkPixbuf *render_pdf_preview(const char *filepath, int max_w, int max_h) {
  GError *err = NULL;
  gchar *uri = g_filename_to_uri(filepath, NULL, &err);
  if (!uri) {
    g_clear_error(&err);
    return NULL;
  }

  PopplerDocument *doc = poppler_document_new_from_file(uri, NULL, &err);
  g_free(uri);
  if (!doc) {
    g_clear_error(&err);
    return NULL;
  }

  PopplerPage *page = poppler_document_get_page(doc, 0);
  if (!page) {
    g_object_unref(doc);
    return NULL;
  }

  /* get page size in points (1 point = 1/72 inch) */
  double pw, ph;
  poppler_page_get_size(page, &pw, &ph);

  /* compute scale to fit */
  double sx = (double)max_w / pw;
  double sy = (double)max_h / ph;
  double scale = sx < sy ? sx : sy;
  if (scale <= 0) scale = 1.0;

  int width = (int)(pw * scale + 0.5);
  int height = (int)(ph * scale + 0.5);

  cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, width, height);
  if (cairo_surface_status(surface) != CAIRO_STATUS_SUCCESS) {
    poppler_dest_free(page);
    g_object_unref(doc);
    return NULL;
  }

  cairo_t *cr = cairo_create(surface);
  cairo_scale(cr, scale, scale);
  /* white background */
  cairo_set_source_rgb(cr, 1, 1, 1);
  cairo_paint(cr);

  poppler_page_render(page, cr);

  cairo_destroy(cr);

  /* convert cairo surface to GdkPixbuf */
#if GTK_CHECK_VERSION(3,0,0)
  GdkPixbuf *pix = gdk_pixbuf_get_from_surface(surface, 0, 0, width, height);
#else
  GdkPixbuf *pix = NULL;
#endif

  cairo_surface_destroy(surface);
  poppler_dest_free(page);
  g_object_unref(doc);

  return pix; /* may be NULL if conversion unavailable */
}

/* Display text preview in textview */
static void display_text_preview(AppData *ad, const char *filename) {
  char *full = g_build_filename(ad->dirpath, filename, NULL);
  GError *err = NULL;
  GString *content = NULL;
  GtkTextBuffer *buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(ad->textview));

  if (!read_file_preview(full, &content, &err)) {
    gtk_text_buffer_set_text(buf, err->message ? err->message : "(error reading file)", -1);
    g_clear_error(&err);
  } else {
    gboolean binary = (content->len > 0 && memchr(content->str, '\0', content->len) != NULL);
    if (binary) {
      gtk_text_buffer_set_text(buf, "(binary file preview not available)", -1);
    } else {
      gchar *utf8 = g_convert_with_fallback(content->str, content->len, "UTF-8", "UTF-8", "�", NULL, NULL, NULL);
      gtk_text_buffer_set_text(buf, utf8 ? utf8 : content->str, -1);
      g_free(utf8);
    }
    g_string_free(content, TRUE);
  }
  g_free(full);

  /* show textview, hide image */
  gtk_widget_show(ad->textview);
  gtk_widget_hide(ad->image);
}

/* Display PDF preview in image widget */
static void display_pdf_preview(AppData *ad, const char *filename) {
  char *full = g_build_filename(ad->dirpath, filename, NULL);
  GdkPixbuf *pix = render_pdf_preview(full, PDF_PREVIEW_WIDTH, PDF_PREVIEW_HEIGHT);
  if (pix) {
    gtk_image_set_from_pixbuf(GTK_IMAGE(ad->image), pix);
    g_object_unref(pix);
  } else {
    /* show error message in textview as fallback */
    GtkTextBuffer *buf = gtk_text_view_get_buffer(GTK_TEXT_VIEW(ad->textview));
    gtk_text_buffer_set_text(buf, "(cannot render PDF preview)", -1);
    gtk_widget_show(ad->textview);
    gtk_widget_hide(ad->image);
    g_free(full);
    return;
  }
  g_free(full);

  /* show image, hide textview */
  gtk_widget_show(ad->image);
  gtk_widget_hide(ad->textview);
}

/* Unified preview dispatcher */
static void display_preview(AppData *ad, const char *filename) {
  const char *ext = get_extension_lower(filename);
  if (g_strcmp0(ext, "pdf") == 0) {
    display_pdf_preview(ad, filename);
  } else {
    display_text_preview(ad, filename);
  }
}

/* Handlers */
static gboolean on_row_enter(GtkWidget *widget, GdkEvent *event, gpointer user_data) {
  AppData *ad = (AppData *)g_object_get_data(G_OBJECT(gtk_widget_get_toplevel(widget)), "appdata");
  const char *filename = (const char *)user_data;
  if (!ad || !filename) return FALSE;

  display_preview(ad, filename);
  return FALSE;
}

static void on_row_activated(GtkListBox *box, GtkListBoxRow *row, gpointer user_data) {
  AppData *ad = (AppData *)user_data;
  GtkWidget *child = gtk_bin_get_child(GTK_BIN(row));
  const gchar *filename = gtk_label_get_text(GTK_LABEL(child));
  if (filename) display_preview(ad, filename);
}

/* Populate list */
static void populate_list(GtkListBox *listbox, const char *dirpath) {
  DIR *d = opendir(dirpath);
  if (!d) return;
  struct dirent *ent;
  while ((ent = readdir(d)) != NULL) {
    if (ent->d_name[0] == '.') continue;
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

      gtk_widget_add_events(row, GDK_ENTER_NOTIFY_MASK);
      char *name_copy = g_strdup(ent->d_name);
      g_signal_connect(row, "enter-notify-event", G_CALLBACK(on_row_enter), name_copy);
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
  gtk_window_set_default_size(GTK_WINDOW(win), 1000, 700);
  gtk_window_set_title(GTK_WINDOW(win), "Folder Hover Preview (text + PDF)");

  GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 6);
  gtk_container_set_border_width(GTK_CONTAINER(hbox), 6);
  gtk_container_add(GTK_CONTAINER(win), hbox);

  GtkWidget *sc_left = gtk_scrolled_window_new(NULL, NULL);
  gtk_widget_set_size_request(sc_left, 320, -1);
  gtk_box_pack_start(GTK_BOX(hbox), sc_left, FALSE, TRUE, 0);

  GtkWidget *list = gtk_list_box_new();
  gtk_container_add(GTK_CONTAINER(sc_left), list);

  populate_list(GTK_LIST_BOX(list), dirpath);
  g_signal_connect(list, "row-activated", G_CALLBACK(on_row_activated), &ad);

  /* Right: preview container with textview and image stacked */
  GtkWidget *sc_right = gtk_scrolled_window_new(NULL, NULL);
  gtk_box_pack_start(GTK_BOX(hbox), sc_right, TRUE, TRUE, 0);

  ad.preview_container = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  gtk_container_add(GTK_CONTAINER(sc_right), ad.preview_container);

  ad.textview = gtk_text_view_new();
  gtk_text_view_set_editable(GTK_TEXT_VIEW(ad.textview), FALSE);
  gtk_text_view_set_wrap_mode(GTK_TEXT_VIEW(ad.textview), GTK_WRAP_WORD_CHAR);
  gtk_widget_set_vexpand(ad.textview, TRUE);
  gtk_container_add(GTK_CONTAINER(ad.preview_container), ad.textview);

  ad.image = gtk_image_new();
  gtk_widget_set_valign(ad.image, GTK_ALIGN_START);
  gtk_widget_set_size_request(ad.image, -1, -1);
  gtk_container_add(GTK_CONTAINER(ad.preview_container), ad.image);

  /* Initially show textview, hide image */
  gtk_widget_show_all(ad.preview_container);
  gtk_widget_hide(ad.image);

  g_object_set_data(G_OBJECT(win), "appdata", &ad);

  g_signal_connect(win, "destroy", G_CALLBACK(gtk_main_quit), NULL);

  gtk_widget_show_all(win);

  /* select first file and preview */
  GtkListBoxRow *first = gtk_list_box_get_row_at_index(GTK_LIST_BOX(list), 0);
  if (first) {
    gtk_list_box_select_row(GTK_LIST_BOX(list), first);
    on_row_activated(GTK_LIST_BOX(list), first, &ad);
  }

  gtk_main();

  g_free(ad.dirpath);
  return 0;
}

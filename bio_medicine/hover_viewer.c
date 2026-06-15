// hover_viewer.c
#include <gtk/gtk.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>

#define PREVIEW_LINES 200

typedef struct {
  char *dirpath;
} AppData;

/* Escapes single quotes in filename so it can be safely wrapped in single quotes in sh */
static char *escape_single_quotes(const char *s) {
  size_t len = strlen(s);
  /* worst case every char becomes two (for quote escaping) + 1 for terminating NUL */
  char *out = g_malloc(len * 2 + 1);
  char *p = out;
  for (; *s; ++s) {
    if (*s == '\'') {
      memcpy(p, "'\\''", 4);
      p += 4;
    } else {
      *p++ = *s;
    }
  }
  *p = '\0';
  return out;
}

/* Spawn a terminal to show the first PREVIEW_LINES lines of filepath.
   Uses xterm -e "sh -c 'sed -n '1,NNNp' 'filepath'; printf \"\\n(press Enter to close)\"; read -r'"
   Replace xterm with preferred terminal if needed. */
static void spawn_preview_terminal(const char *filepath) {
  if (!filepath) return;

  char *escaped = escape_single_quotes(filepath);

  char cmd[4096];
  snprintf(cmd, sizeof(cmd),
	   "sh -c 'sed -n \"1,%d p\" '%s' 2>/dev/null || echo \"(cannot open file)\"; echo; printf \"--- Press Enter to close ---\"; read -r'",
	   PREVIEW_LINES, escaped);

  /* Try xterm first; if not available, you may change to gnome-terminal -- bash -c "..." */
  char *const argv[] = { "xterm", "-geometry", "80x25", "-e", cmd, NULL };

  GError *err = NULL;
  if (!g_spawn_async(NULL, argv, NULL, G_SPAWN_SEARCH_PATH | G_SPAWN_DO_NOT_REAP_CHILD, NULL, NULL, NULL, &err)) {
    /* fallback: try gnome-terminal if xterm not found */
    g_clear_error(&err);
    char *const argv2[] = { "gnome-terminal", "--", "bash", "-c", cmd, NULL };
    if (!g_spawn_async(NULL, argv2, NULL, G_SPAWN_SEARCH_PATH | G_SPAWN_DO_NOT_REAP_CHILD, NULL, NULL, NULL, &err)) {
      g_printerr("Failed to spawn terminal: %s\n", err ? err->message : "unknown");
      g_clear_error(&err);
    }
  }

  g_free(escaped);
}

/* Handler for mouse enter (hover) on a row */
static gboolean on_enter_notify(GtkWidget *widget, GdkEvent *event, gpointer user_data) {
  const char *filename = (const char *)user_data;
  if (!filename) return FALSE;

  GtkWidget *parent = gtk_widget_get_toplevel(widget);
  const char *dirpath = g_object_get_data(G_OBJECT(parent), "dirpath");
  char *full = g_build_filename(dirpath, filename, NULL);

  spawn_preview_terminal(full);

  g_free(full);
  return FALSE;
}

static void populate_list(GtkListBox *listbox, const char *dirpath) {
  DIR *d = opendir(dirpath);
  if (!d) return;
  struct dirent *ent;
  while ((ent = readdir(d)) != NULL) {
    if (ent->d_name[0] == '.') continue; /* skip hidden */
    /* check regular file */
    char *full = g_build_filename(dirpath, ent->d_name, NULL);
    struct stat st;
    if (stat(full, &st) == 0 && S_ISREG(st.st_mode)) {
      GtkWidget *row = gtk_label_new(ent->d_name);
      gtk_widget_set_halign(row, GTK_ALIGN_START);
      gtk_widget_set_margin_start(row, 6);
      gtk_list_box_insert(listbox, row, -1);
      /* enable enter-notify on label */
      gtk_widget_add_events(row, GDK_ENTER_NOTIFY_MASK);
      /* connect hover; pass filename as user_data (must be duplicated) */
      char *name_copy = g_strdup(ent->d_name);
      g_signal_connect(row, "enter-notify-event", G_CALLBACK(on_enter_notify), name_copy);
      /* free name_copy when row is destroyed */
      g_signal_connect_swapped(row, "destroy", G_CALLBACK(g_free), name_copy);
    }
    g_free(full);
  }
  closedir(d);
  gtk_widget_show_all(GTK_WIDGET(listbox));
}

int main(int argc, char *argv[]) {
  gtk_init(&argc, &argv);

  const char *dirpath = (argc > 1) ? argv[1] : ".";
  /* verify directory */
  struct stat st;
  if (stat(dirpath, &st) != 0 || !S_ISDIR(st.st_mode)) {
    g_printerr("Invalid directory: %s\n", dirpath);
    return 1;
  }

  GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  gtk_window_set_default_size(GTK_WINDOW(win), 400, 600);
  char *title = g_strdup_printf("Hover Viewer: %s", dirpath);
  gtk_window_set_title(GTK_WINDOW(win), title);
  g_free(title);

  g_object_set_data(G_OBJECT(win), "dirpath", (gpointer)dirpath);

  GtkWidget *sc = gtk_scrolled_window_new(NULL, NULL);
  gtk_container_add(GTK_CONTAINER(win), sc);

  GtkWidget *list = gtk_list_box_new();
  gtk_container_add(GTK_CONTAINER(sc), list);

  populate_list(GTK_LIST_BOX(list), dirpath);

  g_signal_connect(win, "destroy", G_CALLBACK(gtk_main_quit), NULL);
  gtk_widget_show_all(win);

  gtk_main();
  return 0;
}

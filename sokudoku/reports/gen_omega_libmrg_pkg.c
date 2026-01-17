    /*
      * gen_omega_libmgr_pkg.c
      *
      * Generates omega_libmgr_pkg/ with:
      *  - bin/server.c      : simple HTTP + API server (sqlite3, calls pdftotext, launches editor via xterm)
      *  - lib/db.c          : sqlite helper to init DB and CRUD
      *  - include/lib.h     : APIs
      *  - etc/www/*         : web UI (HTML/JS) for listing/search/upload/search/edit
      *  - bin/editor        : placeholder launcher (assumes omega_vimfull_pkg/bin/editor exists or replace)
      *  - Makefile, examples/
      *
      * Notes:
      *  - Requires: pdftotext, xterm, sqlite3 development headers/libs
      *  - Build server with -lsqlite3
      */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

     static int ensure_dir(const char *p){
     int r = MKDIR(p);
     if(r==0) return 0;
     if(errno==EEXIST) return 0;
     return -1;
   }
static int write_file(const char *path, const char *data){
  FILE *f = fopen(path, "wb");
  if(!f) return -1;
  size_t n = strlen(data);
  if(fwrite(data,1,n,f) != n){ fclose(f); return -1; }
  fclose(f);
  return 0;
}

int main(void){
  const char *root = "omega_libmgr_pkg";
  char path[1024];
  const char *dirs[] = {"bin","lib","include","etc","usr","examples","etc/www"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){ fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno)); return 1; }
  }

  /* include/lib.h */
    const char *hdr =
      "/* include/lib.h */\n#ifndef OMEGA_LIBMGR_H\n#define OMEGA_LIBMGR_H\n\n/* DB init / simple API */\nint db_init(const char *dbpath);\nint db_add_book(const char *title, const char *author, const char *pdf_path, char **err);\n\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%clib.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, hdr) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/db.c (sqlite3 wrapper) */
    const char *db_c =
      "/* lib/db.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <sqlite3.h>\n#include \"../include/lib.h\"\n\nstatic sqlite3 *DB = NULL;\nint db_init(const char *dbpath){ if(!dbpath) dbpath = \"./libmgr.db\"; if(sqlite3_open(dbpath, &DB)!=SQLITE_OK){ return -1; }\n    const char *schema =\n        \"CREATE TABLE IF NOT EXISTS books(\"\n        \"id INTEGER PRIMARY KEY AUTOINCREMENT,\"\n        \"title TEXT, author TEXT, pdf_path TEXT, txt_path TEXT, added_at DATETIME DEFAULT CURRENT_TIMESTAMP);\";\n    char *err = NULL; if(sqlite3_exec(DB, schema, NULL, NULL, &err) != SQLITE_OK){ if(err){ free(err); } return -1; }\n    return 0; }\n\nint db_add_book(const char *title, const char *author, const char *pdf_path, char **err_out){ if(!DB) return -1; const char *sql = \"INSERT INTO books(title,author,pdf_path,txt_path) VALUES(?,?,?,?)\"; sqlite3_stmt *st; if(sqlite3_prepare_v2(DB, sql, -1, &st, NULL)!=SQLITE_OK){ if(err_out) *err_out = strdup(\"prepare failed\"); return -1; }\n    sqlite3_bind_text(st, 1, title?title:\"\", -1, SQLITE_STATIC);\n    sqlite3_bind_text(st, 2, author?author:\"\", -1, SQLITE_STATIC);\n    sqlite3_bind_text(st, 3, pdf_path?pdf_path:\"\", -1, SQLITE_STATIC);\n    /* txt_path initially empty */ sqlite3_bind_text(st, 4, \"\", -1, SQLITE_STATIC);\n    if(sqlite3_step(st)!=SQLITE_DONE){ if(err_out) *err_out = strdup(\"insert failed\"); sqlite3_finalize(st); return -1; }\n    sqlite3_finalize(st);\n    return 0; }\n";
    snprintf(path, sizeof path, "%s%clib%cdb.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, db_c) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/server.c : minimal HTTP server with simple routing (single-threaded) */
    const char *server_c =
      "/* bin/server.c */\n/* Simple single-thread HTTP server for local use. Serves static WWW, provides API endpoints:\n   GET  /            -> web UI\n   GET  /api/list    -> JSON list of books\n   POST /api/add     -> form fields title,author,pdf_path (server will run pdftotext to produce .txt)\n   GET  /files/<path> -> serve static files\n   GET  /edit?file=<txtpath> -> launch local xterm with editor\n*/\n\n#define _POSIX_C_SOURCE 200809L\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <unistd.h>\n#include <fcntl.h>\n#include <sys/types.h>\n#include <sys/socket.h>\n#include <netinet/in.h>\n#include <arpa/inet.h>\n#include <sys/stat.h>\n#include <pthread.h>\n#include <ctype.h>\n#include <errno.h>\n#include <sqlite3.h>\n\n#include \"../lib/db.c\" /* embed db helper for simplicity in this prototype */\n\n#define PORT 8080\n#define WWWROOT \"etc/www\"\n\nstatic int listen_fd = -1;\n\nstatic void url_decode(char *dst, const char *src){ char a,b; while(*src){ if((*src=='%') && ((a=src[1]) && (b=src[2])) && isxdigit(a) && isxdigit(b)){ char hex[3] = {a,b,0}; *dst++ = (char)strtol(hex, NULL, 16); src+=3; } else if(*src=='+'){ *dst++ = ' '; src++; } else { *dst++ = *src++; } } *dst=0; }\n\nstatic void http_send(int fd, const char *hdr, const char *body){ dprintf(fd, \"%s\\r\\n\\r\\n%s\", hdr, body); }\n\nstatic void serve_file(int fd, const char *path){ char full[1024]; snprintf(full,sizeof full, \"%s/%s\", WWWROOT, path); struct stat st; if(stat(full,&st)==-1){ http_send(fd, \"HTTP/1.1 404 Not Found\", \"Not found\"); return; }\n    if(S_ISDIR(st.st_mode)){ http_send(fd, \"HTTP/1.1 403 Forbidden\", \"Dir\"); return; }\n    int f = open(full, O_RDONLY); if(f<0){ http_send(fd, \"HTTP/1.1 500 Internal\", \"Open fail\"); return; }\n    dprintf(fd, \"HTTP/1.1 200 OK\\r\\nContent-Length: %ld\\r\\n\\r\\n\", (long)st.st_size);\n    off_t off=0; while(off < st.st_size){ ssize_t r = sendfile(fd, f, &off, st.st_size - off); if(r<=0) break; }\n    close(f);\n}\n\nstatic void handle_client(int fd){ char buf[8192]; int r = read(fd, buf, sizeof(buf)-1); if(r<=0){ close(fd); return; } buf[r]=0; /* parse request line */ char method[16], path[1024]; if(sscanf(buf, \"%15s %1023s\", method, path) != 2){ http_send(fd, \"HTTP/1.1 400 Bad Request\", \"bad\"); close(fd); return; }\n    if(strcmp(method,\"GET\")==0){ if(strcmp(path, \"/\")==0){ serve_file(fd, \"index.html\"); close(fd); return; }\n        /* static files: /static/... mapped to WWWROOT */ if(strncmp(path, \"/static/\",8)==0){ serve_file(fd, path+8); close(fd); return; }\n        if(strcmp(path, \"/api/list\")==0){ /* query sqlite and return JSON */ sqlite3 *db; if(sqlite3_open(\"libmgr.db\", &db)!=SQLITE_OK){ http_send(fd, \"HTTP/1.1 500\", \"db open\"); close(fd); return; }\n                const char *sql = \"SELECT id,title,author,pdf_path,txt_path,added_at FROM books ORDER BY added_at DESC\";\n                sqlite3_stmt *st; if(sqlite3_prepare_v2(db, sql, -1, &st, NULL)!=SQLITE_OK){ http_send(fd, \"HTTP/1.1 500\", \"db query\"); sqlite3_close(db); close(fd); return; }\n                dprintf(fd, \"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n\\r\\n[\"); int first=1; while(sqlite3_step(st)==SQLITE_ROW){ if(!first) dprintf(fd, \",\"); first=0; int id = sqlite3_column_int(st,0); const unsigned char *title = sqlite3_column_text(st,1); const unsigned char *auth = sqlite3_column_text(st,2); const unsigned char *pdf = sqlite3_column_text(st,3); const unsigned char *txt = sqlite3_column_text(st,4); const unsigned char *at = sqlite3_column_text(st,5);\n                        dprintf(fd, \"{\\\"id\\\":%d,\\\"title\\\":\\\"%s\\\",\\\"author\\\":\\\"%s\\\",\\\"pdf\\\":\\\"%s\\\",\\\"txt\\\":\\\"%s\\\",\\\"added\\\":\\\"%s\\\"}\", id, title?title:\"\", auth?auth:\"\", pdf?pdf:\"\", txt?txt:\"\", at?at:\"\"); }\n                dprintf(fd, \"]\"); sqlite3_finalize(st); sqlite3_close(db); close(fd); return; }\n        /* edit launch: /edit?file=<path> */ if(strncmp(path, \"/edit?file=\",11)==0){ char dec[1024]; url_decode(dec, path+11); /* launch xterm with editor */ char cmd[2048]; snprintf(cmd, sizeof cmd, \"xterm -e ./bin/editor %s &\", dec); system(cmd); http_send(fd, \"HTTP/1.1 200 OK\", \"Launched editor\"); close(fd); return; }\n        /* serve files under /files/ -> map to root relative */ if(strncmp(path, \"/files/\",7)==0){ serve_file(fd, path+7); close(fd); return; }\n        http_send(fd, \"HTTP/1.1 404 Not Found\", \"not handled\"); close(fd); return; }\n    else if(strcmp(method,\"POST\")==0){ /* naive parse for /api/add (form urlencoded) */ if(strcmp(path, \"/api/add\")==0){ char *p = strstr(buf, \"\\r\\n\\r\\n\"); if(!p){ http_send(fd, \"HTTP/1.1 400 Bad Req\", \"no body\"); close(fd); return; } p += 4; char body[4096]; strncpy(body, p, sizeof(body)-1); body[sizeof(body)-1]=0; /* parse title=...&author=...&pdf_path=... */ char title[512]=\"\", author[512]=\"\", pdf[1024]=\"\"; char *tok = strtok(body, \"&\"); while(tok){ char *eq = strchr(tok,'='); if(eq){ *eq=0; char key[256]; char val[1024]; strncpy(key, tok, sizeof key-1); key[sizeof key-1]=0; strncpy(val, eq+1, sizeof val-1); val[sizeof val-1]=0; char decv[1024]; url_decode(decv, val);\n                        if(strcmp(key, \"title\")==0) strncpy(title, decv, sizeof title-1);\n                        if(strcmp(key, \"author\")==0) strncpy(author, decv, sizeof author-1);\n                        if(strcmp(key, \"pdf_path\")==0) strncpy(pdf, decv, sizeof pdf-1);\n                    }\n                    tok = strtok(NULL, \"&\"); }\n                char *err = NULL; if(db_init(\"libmgr.db\")!=0){ http_send(fd, \"HTTP/1.1 500 DB\", \"db init\"); close(fd); return; }\n                if(db_add_book(title, author, pdf, &err)!=0){ http_send(fd, \"HTTP/1.1 500 DB\", err?err:\"add fail\"); if(err) free(err); close(fd); return; }\n                /* After insertion, run pdftotext to create txt (if pdf exists). Compute txt path as examples/<basename>.txt */ if(strlen(pdf)>0){ char *bn = strrchr(pdf,'/'); if(!bn) bn = pdf; else bn++; char txtpath[1024]; snprintf(txtpath,sizeof txtpath, \"examples/%s.txt\", bn); /* remove .pdf if present */ char *dot = strrchr(txtpath, '.'); if(dot) *dot = '\\0'; strcat(txtpath, \".txt\"); /* run pdftotext \"pdf\" txtpath (pdftotext without -layout gives plain text file) */ char cmd[2048]; snprintf(cmd,sizeof cmd, \"pdftotext \\\"%s\\\" \\\"%s\\\" 2>/dev/null\", pdf, txtpath); int rc = system(cmd);\n                    /* update DB with txt_path */ sqlite3 *db; sqlite3_open(\"libmgr.db\", &db); const char *up = \"UPDATE books SET txt_path = ? WHERE id = (SELECT MAX(id) FROM books)\"; sqlite3_stmt *st; sqlite3_prepare_v2(db, up, -1, &st, NULL); sqlite3_bind_text(st,1,txtpath,-1,SQLITE_STATIC); sqlite3_step(st); sqlite3_finalize(st); sqlite3_close(db); }\n                http_send(fd, \"HTTP/1.1 200 OK\", \"added\"); close(fd); return; }\n    }\n    http_send(fd, \"HTTP/1.1 405 Method Not Allowed\", \"method\"); close(fd); }\n\nint main(int argc, char **argv){ /* init db if not exists */ db_init(\"libmgr.db\"); /* create socket */ int fd = socket(AF_INET, SOCK_STREAM, 0); if(fd<0){ perror(\"socket\"); return 1; } int opt=1; setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)); struct sockaddr_in addr; addr.sin_family = AF_INET; addr.sin_addr.s_addr = INADDR_ANY; addr.sin_port = htons(PORT);\n    if(bind(fd, (struct sockaddr*)&addr, sizeof(addr))<0){ perror(\"bind\"); return 1; }\n    if(listen(fd, 10)<0){ perror(\"listen\"); return 1; }\n    printf(\"Server listening on http://localhost:%d/\\n\", PORT);\n    while(1){ struct sockaddr_in caddr; socklen_t len = sizeof(caddr); int c = accept(fd, (struct sockaddr*)&caddr, &len); if(c<0) continue; handle_client(c); }\n    close(fd); return 0; }\n";
    snprintf(path, sizeof path, "%s%cbin%cserver.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, server_c) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* etc/www/index.html (simple UI) */
    const char *index_html =
      "<!doctype html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<title>Omega Library Manager</title>\n<style>body{font-family:Arial;} #books{margin-top:1em;} .book{border-bottom:1px solid #ddd;padding:6px;} .btn{padding:4px 8px;margin:2px;background:#28a; color:#fff;text-decoration:none;border-radius:4px;}</style>\n</head>\n<body>\n<h1>Omega Library</h1>\n<form id=\"addform\">\n Title: <input name=\"title\"> Author: <input name=\"author\"> PDF path: <input name=\"pdf_path\" size=\"50\"> <button>Add</button>\n</form>\n<div>\n Search: <input id=\"q\"> <button id=\"btnq\">Search</button>\n</div>\n<div id=\"books\"></div>\n<script>\nfunction fetchList(q){ fetch('/api/list').then(r=>r.json()).then(js=>{ let cont=''; for(let b of js){ if(q && !(b.title.includes(q) || b.author.includes(q))) continue; cont += `<div class=\"book\"><b>${b.title}</b> by ${b.author} <br/> <a href=\"/files/${b.txt}\" target=\"_blank\">txt</a> <a class=\"btn\" href=\"/edit?file=${encodeURIComponent(b.txt)}\">Edit in Omega Editor</a></div>`; } document.getElementById('books').innerHTML = cont; }); }\nwindow.onload = function(){ fetchList(); document.getElementById('addform').onsubmit = function(e){ e.preventDefault(); let fd = new URLSearchParams(new FormData(e.target)); fetch('/api/add',{method:'POST', body: fd.toString(), headers:{'Content-Type':'application/x-www-form-urlencoded'}}).then(r=>{ fetchList(); }); } document.getElementById('btnq').onclick = function(){ fetchList(document.getElementById('q').value); } }\n</script>\n</body>\n</html>\n";
    snprintf(path, sizeof path, "%s%cetc%cwww% cindex.html", root, PATH_SEP, PATH_SEP, PATH_SEP); /* placeholder then fix */
    snprintf(path, sizeof path, "%s%cetc%cwww%cindex.html", root, PATH_SEP, PATH_SEP, PATH_SEP);
    if(write_file(path, index_html) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/sample.pdf: we cannot include an actual PDF; instead a README instructing how to add PDFs */ */
    const char *examples_readme =
      "Examples folder: place your PDF files here (or provide absolute paths when adding via the web UI).\nWhen you add a book and provide a PDF path, server runs `pdftotext` to produce examples/<basename>.txt which becomes available in the UI.\n";
    snprintf(path, sizeof path, "%s%cexamples%creadme.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, examples_readme) != 0){ /* ignore */ ; }

    /* bin/editor placeholder: if user previously generated Omega editor packages, they can copy binary here.
       We'll write a small launcher script that tries to run ../omega_vimfull_pkg/bin/editor if present, otherwise prints instructions.
    */
    const char *editor_launcher =
"#!/bin/sh\n# launcher wrapper for Omega Editor\nED=\"./editor.real\"\nif [ -x \"./editor.real\" ]; then exec ./editor.real \"$@\"; fi\nif [ -x \"../omega_vimfull_pkg/bin/editor\" ]; then exec ../omega_vimfull_pkg/bin/editor \"$@\"; fi\necho \"No editor binary found. Build or place your omega_vimfull editor as bin/editor or ../omega_vimfull_pkg/bin/editor\";\nexit 1\n";
    snprintf(path, sizeof path, "%s% cbin%ceditor", root, PATH_SEP, PATH_SEP); /* fix */
    snprintf(path, sizeof path, "%s%cbin%ceditor", root, PATH_SEP, PATH_SEP);
    if(write_file(path, editor_launcher) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    chmod(path, 0755);
#endif

    /* Makefile */
    const char *makefile =
"CC=gcc\nCFLAGS=-O2 -Iinclude\nLDFLAGS=-lsqlite3\n\nall: bin/server\n\nbin/server: bin/server.c lib/db.c\n\t$(CC) $(CFLAGS) -o bin/server bin/server.c lib/db.c $(LDFLAGS)\n\nclean:\n\trm -f bin/server\n";
    snprintf(path, sizeof path, "%s%cMakefile", root, PATH_SEP);
    if(write_file(path, makefile) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* README */
    const char *readme =
"omega_libmgr_pkg\n\nSimple local library manager.\n\nRequirements: pdftotext (poppler-utils), xterm (or adjust editor launcher), sqlite3 dev libs.\n\nBuild:\n  make\n\nRun:\n  ./bin/server\n  open http://localhost:8080/ in browser\n\nNotes:\n  - When adding a book, give the path to a PDF file accessible to the server. The server will run pdftotext to create a txt under examples/.\n  - The web UI can launch a local editor via xterm. Ensure you have a working omega editor binary at ../omega_vimfull_pkg/bin/editor or bin/editor.real.\n";
	       snprintf(path, sizeof path, "%s%creadme.txt", root, PATH_SEP);
if(write_file(path, readme) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

printf("Package '%s' created.\n", root);
printf("Build & run:\n  cd %s\n  make\n  ./bin/server\n  open http://localhost:8080/\n", root);
return 0;
}

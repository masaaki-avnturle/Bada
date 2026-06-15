/* Windows-only module (uses <windows.h>). Compiled only on Windows;
   on other platforms this is an (empty) translation unit. */
#if defined(_WIN32)
/* remapper.c - main entry for remapper (educational demo)
   Uses emacs_bindings and vim_bindings modules. Loads targets.txt for process filtering.
*/
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include "keymap.h"
#include "emacs_bindings.h"
#include "vim_bindings.h"

static HHOOK g_hHook = NULL;
static int g_mode = MODE_INSERT; /* MODE_INSERT / MODE_NORMAL / MODE_COMMAND */

/* dynamic targets (simple, same as other sample) */
#define MAX_TARGETS 128
static wchar_t *g_targets[MAX_TARGETS]; static int g_target_count = 0;
static void free_targets(void){ for(int i=0;i<g_target_count;i++){ free(g_targets[i]); g_targets[i]=NULL; } g_target_count=0; }
static void load_targets(void){ FILE *f = _wfopen(L"targets.txt", L"r, ccs=UTF-8"); if(!f) return; wchar_t line[512]; while(fgetws(line, 512, f)){ wchar_t *p=line; while(*p==L' '||*p==L'\t') p++; wchar_t *e=p+wcslen(p)-1; while(e>=p && (*e==L'\n'||*e==L'\r'||*e==L' '||*e==L'\t')) *e--=L'\0'; if(*p==L'#'||*p==L'\0') continue; if(g_target_count<MAX_TARGETS) g_targets[g_target_count++]=_wcsdup(p); } fclose(f); }
static wchar_t *get_foreground_proc(void){ HWND hwnd=GetForegroundWindow(); if(!hwnd) return NULL; DWORD pid=0; GetWindowThreadProcessId(hwnd,&pid); if(!pid) return NULL; HANDLE h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION|PROCESS_VM_READ,FALSE,pid); if(!h) return NULL; wchar_t path[MAX_PATH]; DWORD sz=MAX_PATH; if(QueryFullProcessImageNameW(h,0,path,&sz)){ wchar_t *b=wcsrchr(path,L'\\'); wchar_t *name=b?_wcsdup(b+1):_wcsdup(path); CloseHandle(h); return name; } CloseHandle(h); return NULL; }
static int is_target_foreground(void){ if(g_target_count==0) return 0; wchar_t *name=get_foreground_proc(); if(!name) return 0; int ok=0; for(int i=0;i<g_target_count;i++){ if(_wcsicmp(name,g_targets[i])==0){ ok=1; break; } } free(name); return ok; }

LRESULT CALLBACK LowLevelProc(int nCode, WPARAM wParam, LPARAM lParam){ if(nCode==HC_ACTION){ KBDLLHOOKSTRUCT *p=(KBDLLHOOKSTRUCT*)lParam; int down=(wParam==WM_KEYDOWN||wParam==WM_SYSKEYDOWN); if(down){ if(!is_target_foreground()) return CallNextHookEx(g_hHook,nCode,wParam,lParam);
            /* dispatch to binding modules based on mode */
            if(g_mode==MODE_INSERT){ if(emacs_handle_key(p->vkCode)) return 1; /* allow Emacs keys in insert */ }
            else if(g_mode==MODE_NORMAL){ if(vim_handle_key(p->vkCode)) return 1; }
            /* mode toggles */
            if(p->vkCode==VK_ESCAPE){ g_mode=MODE_NORMAL; return 1; }
            if(p->vkCode==0x49){ g_mode=MODE_INSERT; return 1; } /* 'i' */
            if(p->vkCode==VK_OEM_1){ g_mode=MODE_COMMAND; return 1; }
        } }
    return CallNextHookEx(g_hHook,nCode,wParam,lParam); }

int wmain(int argc, wchar_t **argv){ load_targets(); if(g_target_count==0){ g_targets[0]=_wcsdup(L"notepad++.exe"); g_target_count=1; }
    wprintf(L"remapper: starting. targets:\n"); for(int i=0;i<g_target_count;i++) wprintf(L"  %ls\n", g_targets[i]);
    g_hHook = SetWindowsHookExW(WH_KEYBOARD_LL, LowLevelProc, GetModuleHandleW(NULL), 0);
    if(!g_hHook){ fwprintf(stderr,L"failed to install hook (%lu)\n", GetLastError()); free_targets(); return 1; }
    MSG msg; while(GetMessage(&msg,NULL,0,0)){ TranslateMessage(&msg); DispatchMessage(&msg); }
    UnhookWindowsHookEx(g_hHook); free_targets(); return 0; }

#endif /* _WIN32 */
typedef int emacskeys_translation_unit_not_empty;

/* emacs_bindings.c - simple Emacs-like handlers (Ctrl-A/E/B/F etc.) */
#include <windows.h>
#include "emacs_bindings.h"

static void send_vk(WORD vk){ INPUT in[2]; ZeroMemory(in,sizeof(in)); in[0].type=INPUT_KEYBOARD; in[0].ki.wVk=vk; in[1].type=INPUT_KEYBOARD; in[1].ki.wVk=vk; in[1].ki.dwFlags=KEYEVENTF_KEYUP; SendInput(2,in,sizeof(INPUT)); }

int emacs_handle_key(unsigned int vk){ SHORT ctrl = GetAsyncKeyState(VK_CONTROL); if(!(ctrl & 0x8000)) return 0; switch(vk){ case 0x41: send_vk(VK_HOME); return 1; case 0x45: send_vk(VK_END); return 1; case 0x42: send_vk(VK_LEFT); return 1; case 0x46: send_vk(VK_RIGHT); return 1; case 0x4e: send_vk(VK_DOWN); return 1; case 0x50: send_vk(VK_UP); return 1;default: return 0; } }


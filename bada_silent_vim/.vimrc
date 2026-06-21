" .vimrc — Bada language support for Vim
" =====================================
" Usage:  copy/symlink this file to ~/.vimrc, or  :source /path/to/.vimrc
" Point Vim at the Bada toolchain (the bada_silent_vim directory):
"     export BADA_HOME=/path/to/Bada/bada_silent_vim
" or set it here:
if !exists('g:bada_home')
  let g:bada_home = $BADA_HOME
  if g:bada_home ==# ''
    " default: the directory that contains this .vimrc
    let g:bada_home = expand('<sfile>:p:h')
  endif
endif

set nocompatible
filetype plugin indent on
syntax on

" --- file type detection: *.bada -------------------------------------------
augroup bada_ft
  autocmd!
  autocmd BufRead,BufNewFile *.bada setfiletype bada
  autocmd FileType bada call s:BadaSetup()
augroup END

" --- syntax highlighting ---------------------------------------------------
function! s:BadaSyntax() abort
  syntax clear
  " comments  //...
  syntax match badaComment "//.*$"
  " strings
  syntax region badaString start=+"+ skip=+\\"+ end=+"+
  syntax region badaString start=+'+ skip=+\\'+ end=+'+
  " numbers
  syntax match badaNumber "\<[0-9]\+\(\.[0-9]\+\)\?\>"
  " reserved keywords
  syntax keyword badaKeyword print say if else while repeat return def
  syntax keyword badaKeyword push pop true false nil
  syntax keyword badaNamespace Omega
  " builtin functions
  syntax keyword badaBuiltin len append idiv imod abs pow2 str
  " instruction-oriented directive objects + manifold operators
  syntax match badaDirective "<->\|<-\|-<\|->\|>-\|>>\|=>\|::"

  highlight default link badaComment   Comment
  highlight default link badaString    String
  highlight default link badaNumber    Number
  highlight default link badaKeyword   Keyword
  highlight default link badaNamespace Type
  highlight default link badaBuiltin   Function
  highlight default link badaDirective Operator
endfunction

" --- completion: reserved words + builtins + buffer symbols -----------------
let g:bada_words =
      \ ['print','say','if','else','while','repeat','return','def',
      \  'push','pop','true','false','nil','Omega',
      \  'len','append','idiv','imod','abs','pow2','str']

function! BadaComplete(findstart, base) abort
  if a:findstart
    let l:line = getline('.')
    let l:start = col('.') - 1
    while l:start > 0 && l:line[l:start - 1] =~# '\k'
      let l:start -= 1
    endwhile
    return l:start
  endif
  " functional words + identifiers already in the buffer
  let l:cands = copy(g:bada_words)
  let l:seen = {}
  for l:w in l:cands | let l:seen[l:w] = 1 | endfor
  for l:lnum in range(1, line('$'))
    for l:m in split(getline(l:lnum), '\k\@!.')
      if l:m =~# '^\a\w*$' && !has_key(l:seen, l:m)
        let l:seen[l:m] = 1 | call add(l:cands, l:m)
      endif
    endfor
  endfor
  return filter(sort(l:cands), 'v:val =~# "^" . a:base')
endfunction

" --- grammar check / run via the Bada toolchain ----------------------------
function! BadaCheck() abort
  let l:py = 'PYTHONPATH=' . shellescape(g:bada_home)
        \ . ' python3 -W ignore -m bada.lint ' . shellescape(expand('%:p'))
  cexpr system(l:py)
  copen
endfunction

function! BadaRun() abort
  let l:py = 'PYTHONPATH=' . shellescape(g:bada_home)
        \ . ' python3 -W ignore -c ' . shellescape(
        \   'import sys; from bada import run_program; '
        \   . 'run_program(sys.argv[1])') . ' ' . shellescape(expand('%:p'))
  echo system(l:py)
endfunction

" --- per-buffer setup ------------------------------------------------------
function! s:BadaSetup() abort
  call s:BadaSyntax()
  setlocal expandtab shiftwidth=2 softtabstop=2
  setlocal commentstring=//\ %s
  setlocal iskeyword+=_
  setlocal completefunc=BadaComplete
  setlocal omnifunc=BadaComplete
  " quickfix knows how to parse  file:line:col: error: msg
  setlocal errorformat=%f:%l:%c:\ %t%*[^:]:\ %m
  command! -buffer BadaCheck call BadaCheck()
  command! -buffer BadaRun   call BadaRun()
  " <leader> maps:  \c grammar-check, \r run, <C-x><C-u> complete
  nnoremap <buffer> <leader>c :BadaCheck<CR>
  nnoremap <buffer> <leader>r :BadaRun<CR>
endfunction

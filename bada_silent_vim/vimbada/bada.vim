" bada.vim — Bada language plugin for Vim (and the embedded Xcode editor)
" =====================================================================
" Self-contained version of the Bada support in ../.vimrc, packaged as a
" plugin so it can be dropped into ~/.vim/plugin/, loaded from an Xcode
" external-build "Edit in Vim" step, or sourced directly:
"
"     :source /path/to/vimbada/bada.vim
"
" It provides, for *.bada files:
"   * filetype detection + syntax highlighting (insert & command friendly),
"   * completion of reserved words / builtins / buffer symbols,
"   * :BadaCheck / :BadaRun  (grammar-check / run via the Bada toolchain),
"   * :BadaVim  — run the modal vim *written in Bada* over a keystroke script,
"   * :BadaCC   — build the C receiver + class-method binaries for the vim.
"
" Point Vim at the toolchain (the bada_silent_vim directory):
"     export BADA_HOME=/path/to/Bada/bada_silent_vim
" otherwise it is inferred from this plugin's location (../).

if exists('g:loaded_bada')
  finish
endif
let g:loaded_bada = 1

if !exists('g:bada_home') || g:bada_home ==# ''
  let g:bada_home = $BADA_HOME
  if g:bada_home ==# ''
    " this file lives in  <bada_home>/vimbada/bada.vim
    let g:bada_home = expand('<sfile>:p:h:h')
  endif
endif
let g:bada_vimbada = g:bada_home . '/vimbada'

" --- file type detection: *.bada -------------------------------------------
augroup bada_ft
  autocmd!
  autocmd BufRead,BufNewFile *.bada setfiletype bada
  autocmd FileType bada call s:BadaSetup()
augroup END

" --- syntax highlighting ---------------------------------------------------
function! s:BadaSyntax() abort
  syntax clear
  syntax match badaComment "//.*$"
  syntax region badaString start=+"+ skip=+\\"+ end=+"+
  syntax region badaString start=+'+ skip=+\\'+ end=+'+
  syntax match badaNumber "\<[0-9]\+\(\.[0-9]\+\)\?\>"
  syntax keyword badaKeyword print say if else while repeat return def
  syntax keyword badaKeyword push pop true false nil
  syntax keyword badaNamespace Omega
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

" --- completion: reserved words + builtins + buffer symbols ----------------
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

" --- the modal vim written in Bada -----------------------------------------
" Run the Bada vim (lib/vim.bada) over a keystroke script and echo the result.
" e.g.  :BadaVim i h i ESC :wq
function! BadaVim(...) abort
  let l:keys = join(map(copy(a:000), 'shellescape(v:val)'), ', ')
  let l:code = 'import sys; sys.path.insert(0, ' . shellescape(g:bada_home)
        \ . '); from vimbada import bridge; '
        \ . 'r = bridge.run([' . l:keys . ']); '
        \ . 'print(r["text"])'
  echo system('python3 -W ignore -c ' . shellescape(l:code))
endfunction

" --- build the C receiver + class-method binaries --------------------------
function! BadaCC() abort
  let l:code = 'import sys; sys.path.insert(0, ' . shellescape(g:bada_home)
        \ . '); from vimbada import cbackend_vim as c; '
        \ . 'o = ' . shellescape(g:bada_vimbada . '/generated') . '; '
        \ . 'c.generate(o); print("built:", c.build(o))'
  echo system('python3 -W ignore -c ' . shellescape(l:code))
endfunction

" --- per-buffer setup ------------------------------------------------------
function! s:BadaSetup() abort
  call s:BadaSyntax()
  setlocal expandtab shiftwidth=2 softtabstop=2
  setlocal commentstring=//\ %s
  setlocal iskeyword+=_
  setlocal completefunc=BadaComplete
  setlocal omnifunc=BadaComplete
  setlocal errorformat=%f:%l:%c:\ %t%*[^:]:\ %m
  command! -buffer BadaCheck call BadaCheck()
  command! -buffer BadaRun   call BadaRun()
  command! -buffer -nargs=* BadaVim call BadaVim(<f-args>)
  command! -buffer BadaCC    call BadaCC()
  nnoremap <buffer> <leader>c :BadaCheck<CR>
  nnoremap <buffer> <leader>r :BadaRun<CR>
endfunction

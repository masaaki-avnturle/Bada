" oslo.vim

" ファイルタイプの設定
au BufNewFile,BufRead *.om set filetype=oslo

" 構文ハイライトの定義
syntax keyword oKeyword let def return
syntax match oIdentifier /\<\h\w*\>/
syntax match oNumber /\<\d\+\>/
syntax match oOperator /[-+*\/=!<>]/
syntax region oString start=/"/ end=/"/

" 構文ハイライトのグループ
highlight def link oKeyword Keyword
highlight def link oIdentifier Identifier
highlight def link oNumber Number
highlight def link oOperator Operator
highlight def link oString String

" インデントの設定
setlocal indentexpr=GetOsloIndent()
setlocal indentkeys=0{,0},0),0],!^F,o,O,e

function! GetOsloIndent()
  let prevline = getline(v:lnum - 1)
  let thisline = getline(v:lnum)

  if prevline =~# '^\s*\(let\|def\)'
    return shiftwidth()
  elseif thisline =~# '^\s*\(}\|)\)'
    return 0
  else
    return indent(v:lnum - 1)
  endif
endfunction

" 自動補完の設定
setlocal omnifunc=OsloComplete

function! OsloComplete(findstart, base)
  if a:findstart
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~# '\w'
      let start -= 1
    endwhile
    return start
  else
    " 補完候補の生成
    let candidates = ['let', 'def', 'return']
    return filter(candidates, 'v:val =~# "^' . a:base . '"')
  endif
endfunction

" その他の設定
setlocal comments=:#
setlocal commentstring=#%s

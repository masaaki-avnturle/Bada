はい、Omega scriptの拡張子が`.om`に設定されているときに、Vimでosloファイルを認識するためのソースコードは以下のようになります。

```vim
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
```

このVimプラグインは、以下の機能を提供します:

1. **ファイルタイプの設定**: `.om`拡張子のファイルをOslo言語として認識します。

2. **構文ハイライトの定義**: キーワード、識別子、数値、演算子、文字列に対してハイライトを定義します。

3. **インデントの設定**: `let`や`def`を含む行は1レベルインデントされ、`}`や`)`を含む行はインデントが0になるように設定します。

4. **自動補完の設定**: `let`や`def`などのキーワードを補完候補として提供します。

これにより、Vimでosloファイルを編集する際に、適切な構文ハイライト、インデント、自動補完が行われるようになります。開発者は、Vimの豊富な機能を活用して、Omega scriptの開発を効率的に行うことができます。

このVimプラグインは、Omega scriptの言語仕様に合わせて設計されていますが、他の言語にも同様の機能を提供できるように拡張することができます。
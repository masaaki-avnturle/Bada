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

" oslo.vim

" ... (省略) ...

" 文法チェック
function! OmegaCheckSyntax()
  let errors = []

  " トークンの解析
  let tokens = OmegaLex(join(getline(1, '$'), "\n"))

  " 構文解析
  try
    let ast = OmegaParse(tokens)
  catch /ParseError/
    let error = matchlist(v:exception, 'ParseError:\s*\(\d\+\):\s*\(.*\)')[1:2]
    call add(errors, {'line': str2nr(error[0]), 'message': error[1]})
  endtry

  return errors
endfunction

function! OmegaLex(input)
  let tokens = []

  let i = 0
  while i < len(a:input)
    let [token, i] = OmegaScanToken(a:input, i)
    call add(tokens, token)
  endwhile

  return tokens
endfunction

function! OmegaScanToken(input, start)
  let c = a:input[a:start]

  if c =~ '\a'
    return OmegaScanIdentifier(a:input, a:start)
  elseif c =~ '\d'
    return OmegaScanNumber(a:input, a:start)
  elseif c =~ '[+\-*/=!<>]'
    return OmegaScanOperator(a:input, a:start)
  elseif c ==# '"'
    return OmegaScanString(a:input, a:start)
  else
    throw 'ParseError:' . a:start . ': Unexpected character: ' . c
  endif
endfunction

function! OmegaScanIdentifier(input, start)
  let i = a:start
  while i < len(a:input) && a:input[i] =~ '\w'
    let i += 1
  endwhile
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Identifier', 'value': lexeme}, i]
endfunction

function! OmegaScanNumber(input, start)
  let i = a:start
  while i < len(a:input) && a:input[i] =~ '\d'
    let i += 1
  endwhile
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Number', 'value': str2nr(lexeme)}, i]
endfunction

function! OmegaScanOperator(input, start)
  let i = a:start + 1
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Operator', 'value': lexeme}, i]
endfunction

function! OmegaScanString(input, start)
  let i = a:start + 1
  while i < len(a:input) && a:input[i] !=# '"'
    let i += 1
  endwhile
  if i >= len(a:input)
    throw 'ParseError:' . a:start . ': Unterminated string'
  endif
  let lexeme = strpart(a:input, a:start + 1, i - a:start - 1)
  return [{'type': 'String', 'value': lexeme}, i + 1]
endfunction

function! OmegaParse(tokens)
  let parser = OmegaParser.new(a:tokens)
  return parser.parse_program()
endfunction

" OmegaParser クラスの実装
let s:OmegaParser = {}

function! OmegaParser.new(tokens)
  let obj = copy(s:OmegaParser)
  let obj.tokens = a:tokens
  let obj.index = 0
  return obj
endfunction

function! OmegaParser.parse_program(self)
  let statements = []
  while self.current_token().type !=# 'EOF'
    call add(statements, self.parse_statement())
  endwhile
  return {'type': 'Program', 'statements': statements}
endfunction

function! OmegaParser.parse_statement(self)
  let token = self.current_token()
  if token.type ==# 'Identifier' && self.peek_token().value ==# '='
    return self.parse_assignment()
  elseif token.type ==# 'Identifier' && self.peek_token().value ==# '('
    return self.parse_function_call()
  elseif token.value ==# 'def'
    return self.parse_function_definition()
  elseif token.value ==# 'let'
    return self.parse_variable_declaration()
  else
    throw 'ParseError:' . token.type . ': Unexpected token: ' . token.value
  endif
endfunction

" その他の構文解析メソッドの実装 (省略)

function! OmegaParser.current_token(self)
  return self.tokens[self.index]
endfunction

function! OmegaParser.peek_token(self)
  return self.tokens[self.index + 1]
endfunction

function! OmegaParser.advance(self)
  let self.index += 1
endfunction

" インデント設定
function! OmegaIndent(lnum)
  let prev_lnum = prevnonblank(a:lnum - 1)
  if prev_lnum == 0
    return 0
  endif

  let prev_line = getline(prev_lnum)
  let curr_line = getline(a:lnum)

  let indent = indent(prev_lnum)

  if prev_line =~# '^\s*def\>'
    let indent += &shiftwidth
  elseif prev_line =~# '^\s*let\>'
    let indent += &shiftwidth
  elseif prev_line =~# '^\s*if\>'
    let indent += &shiftwidth
  elseif prev_line =~# '^\s*else\>'
    let indent -= &shiftwidth
  elseif prev_line =~# '^\s*match\>'
    let indent += &shiftwidth
  elseif curr_line =~# '^\s*}\>'
    let indent -= &shiftwidth
  endif

  return indent
endfunction

augroup OmegaMode
  autocmd!
  autocmd FileType omega setlocal indentexpr=OmegaIndent(v:lnum)
  autocmd FileType omega setlocal indentkeys+=0=,0),0},0]
augroup END
```

" oslo.vim

" 字句解析器
function! OmegaLex(input)
  let tokens = []

  let i = 0
  while i < len(a:input)
    let [token, i] = OmegaScanToken(a:input, i)
    call add(tokens, token)
  endwhile

  return tokens
endfunction

function! OmegaScanToken(input, start)
  let c = a:input[a:start]

  if c =~ '\a'
    return OmegaScanIdentifier(a:input, a:start)
  elseif c =~ '\d'
    return OmegaScanNumber(a:input, a:start)
  elseif c =~ '[+\-*/=!<>]'
    return OmegaScanOperator(a:input, a:start)
  elseif c ==# '"'
    return OmegaScanString(a:input, a:start)
  else
    throw 'ParseError:' . a:start . ': Unexpected character: ' . c
  endif
endfunction

function! OmegaScanIdentifier(input, start)
  let i = a:start
  while i < len(a:input) && a:input[i] =~ '\w'
    let i += 1
  endwhile
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Identifier', 'value': lexeme}, i]
endfunction

function! OmegaScanNumber(input, start)
  let i = a:start
  while i < len(a:input) && a:input[i] =~ '\d'
    let i += 1
  endwhile
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Number', 'value': str2nr(lexeme)}, i]
endfunction

function! OmegaScanOperator(input, start)
  let i = a:start + 1
  let lexeme = strpart(a:input, a:start, i - a:start)
  return [{'type': 'Operator', 'value': lexeme}, i]
endfunction

function! OmegaScanString(input, start)
  let i = a:start + 1
  while i < len(a:input) && a:input[i] !=# '"'
    let i += 1
  endwhile
  if i >= len(a:input)
    throw 'ParseError:' . a:start . ': Unterminated string'
  endif
  let lexeme = strpart(a:input, a:start + 1, i - a:start - 1)
  return [{'type': 'String', 'value': lexeme}, i + 1]
endfunction

" 構文解析器
function! OmegaParse(tokens)
  let parser = OmegaParser.new(a:tokens)
  return parser.parse_program()
endfunction

let s:OmegaParser = {}

function! OmegaParser.new(tokens)
  let obj = copy(s:OmegaParser)
  let obj.tokens = a:tokens
  let obj.index = 0
  return obj
endfunction

function! OmegaParser.parse_program(self)
  let statements = []
  while self.current_token().type !=# 'EOF'
    call add(statements, self.parse_statement())
  endwhile
  return {'type': 'Program', 'statements': statements}
endfunction

function! OmegaParser.parse_statement(self)
  let token = self.current_token()
  if token.type ==# 'Identifier' && self.peek_token().value ==# '='
    return self.parse_assignment()
  elseif token.type ==# 'Identifier' && self.peek_token().value ==# '('
    return self.parse_function_call()
  elseif token.value ==# 'def'
    return self.parse_function_definition()
  elseif token.value ==# 'let'
    return self.parse_variable_declaration()
  else
    throw 'ParseError:' . token.type . ': Unexpected token: ' . token.value
  endif
endfunction

function! OmegaParser.current_token(self)
  return self.tokens[self.index]
endfunction

function! OmegaParser.peek_token(self)
  return self.tokens[self.index + 1]
endfunction

function! OmegaParser.advance(self)
  let self.index += 1
endfunction

" 文法チェック
function! OmegaCheckSyntax()
  let errors = []

  try
    let tokens = OmegaLex(join(getline(1, '$'), "\n"))
    let ast = OmegaParse(tokens)
  catch /ParseError/
    let error = matchlist(v:exception, 'ParseError:\s*\(\d\+\):\s*\(.*\)')[1:2]
    call add(errors, {'line': str2nr(error[0]), 'message': error[1]})
  endtry

  return errors
endfunction

" 使用例
autocmd BufWritePost *.omega call OmegaCheckSyntax()
```

" oslo.vim

" 構文ハイライト
syn keyword omegaKeyword def let if else match return
syn keyword omegaType Int Bool String List Map
syn match omegaOperator "[+\-*/=!<>]"
syn match omegaIdentifier "\<\h\w*\>"
syn match omegaNumber "\<\d\+\>"
syn region omegaString start=/"/ end=/"/

hi def link omegaKeyword Keyword
hi def link omegaType Type
hi def link omegaOperator Operator
hi def link omegaIdentifier Identifier
hi def link omegaNumber Number
hi def link omegaString String

" 単語補完
function! OmegaComplete(findstart, base)
  if a:findstart
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\w'
      let start -= 1
    endwhile
    return start
  else
    let completions = ['def', 'let', 'if', 'else', 'match', 'return']
    let res = []
    for c in completions
      if c =~ '^' . a:base
        call add(res, c)
      endif
    endfor
    return res
  endif
endfunction

setlocal omnifunc=OmegaComplete

" 文法チェック
function! OmegaCheckSyntax()
  let errors = []
  " ここに文法チェックのロジックを実装する
  return errors
endfunction

function! OmegaHighlightErrors()
  let errors = OmegaCheckSyntax()
  for error in errors
    execute 'sign define omegaError text=>> linehl=Error'
    execute 'sign place ' . error.line . ' line=' . error.line . ' name=omegaError buffer=' . bufnr('%')
  endfor
endfunction

augroup OmegaMode
  autocmd!
  autocmd BufWritePost *.omega call OmegaHighlightErrors()
augroup END

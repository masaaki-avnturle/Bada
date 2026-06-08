# Artificial Intelligence and TupleSpace of ultranetwork

**Author:** Masaaki Yamaguchi
**Source:** `Bada1.pdf` (22 pages)

> Design notes for the Omega / "asperal" operator-algebra language: a
> TupleSpace-backed, manifold-as-database scripting model with a half-static
> declarator, regular-expression rewriting, a virtual machine, and an
> ultranetwork layer. Mixed Japanese prose + Omega DSL listings.

---

## 概要 (Overview)

クラウドにデータベースを構築しておいて、この構築した多様体を数式で表現したコード通りのデータが、この多様体において、作用素関数として実行されるとする。この多様体を実現したデータが表現されている環境自体を表せられるソースとして、TupleSpace が辞書を書き換えることができないことを利便して、どのデータも上書きされないことによって、前後の記憶が無駄なコードが作用されないことを表現できる。

作用素環プログラミングとして、半静性型宣言子をつくる。この宣言子は、スクリプト型プログラミング言語では、この型を作り上げた時点で、その宣言した環境としての多様体がデータベースの仕様として、宣言した以後のソースコードがこのコード自体の性質を反映させることが多様体を表現した後の、配列、ハッシュ、文字列、ポインタ、ファイル構造体、オブジェクト、数値、関数、正規表現、行列、統計、微分、積分（この微分・積分は関数とは別の文字列と数値処理として、行列と統計をこの表現としての多様体として、微分・積分を数列を応用とした極限値として）ソースコードをコンピュータにおいて実行・表現・存在できる、コンピュータ上だけにとどまらないプログラミング言語として調べられる。

この作用素としての半静性型宣言子は、スクリプト言語において、なぜ静的宣言子が動的スクリプトで必要とされているかが、**Streem / Ruby** を学んでいく段階で浮かび上がった課題である。Ruby のオブジェクト指向を学んだ結果が、この作用素環プログラミングをプログラム思考でコンピュータに人工知能を生成出来て、人体の量子コンピュータを模擬出来て、その上に FPGA までも実行できるアスペクト型人工知能スクリプト言語が、この多様体を、数式を文字列としてだけではなく、電気信号としての表現体としてコンピュータ上に実現できることを研究課題として生まれている。

`Omega::DATABASE tuplespace` としてスクリプトに書き上げているソースをデータベースの下地とする。これをコンピュータに多様体として表現・実行・流れとして動的に実行する。スクリプト言語の動作を停止した場合は、ガベージコレクションとして破棄される。最終的な産物のゼータ関数としてのガンマ関数の大域的微分多様体を熱エントロピー値として、この熱値の性質として分類・整列される TupleSpace 上の関数の群論として研究されるべき課題になっている。

現実の世界を架空化する空間が同型としてのフェルミオンとボソンが、この空想上での入れ物に電気信号としての文字列がバーチャルネットワークに出力されて、物体や生命に現実の世界としての相対的な実存を、特徴・成分・性質・分類としてコンピュータに文字列として命を吹き込む機能を、プログラミング言語で生成されたバーチャルコードによって生み出せる可能性を秘めている。

## データベース宣言 (manifold-as-database)

```
Omega::DATABASE[tuplespace]
{
  Z \supset C \bigoplus \nabla R^{+}, \nabla(R^{+} \cap E^{+}) \ni x, \Delta(C \subset R) \ni x
  M^{+}_{-}\bigoplus R^{+}, E^{+} \in \bigoplus \nabla R^{+}, S^{+}_{-} \subset R^{+}_{2},
  V^{+}_{-} \times R^{+}_{-} \cong {V \over S}
  C^{+} \cup V^{+}_{-} \ni M_{1}\bigoplus \nabla C^{+}_{-},
  Q \supseteqq R^{+}_{-}, Q \subset \bigoplus M^{+}_{-},
  \bigotimes Q \subset \zeta(x), \bigoplus \nabla C^{+}_{-} \cong M_3
  R \subset M_3, C^{+} \bigoplus M_n, E^{+} \cap R^{+},
  E_2 \bigoplus E_1, R^{-} \subset C^{+}, M^{+}_{-}
  C^{+}_{-}, M^{+}_{-}\nabla C^{+}_{-}, C^{+}\nabla H_m,
  E^{+} \nabla R^{+}_{-}, E_2 \nabla E_1, R^{-} \nabla C^{+}_{-}
  [- \Delta v + \nabla_{i} \nabla_{j} v_{ij} - R_{ij} v_{ij}
   - v_{ij} \nabla_{i} \nabla_{j} + 2 < \nabla f, \nabla h>
   + (R + \nabla f^2)({v \over 2} - h)]
  S^3, H^1 \times E^1, E^1, S^1 \times E^1, S^2 \times E^1,
  H^1 \times S^1, H^1, S^2 \times E
}
```

クラウドにおけるデータベースを、多様体が機能する仕組みからデータの相互関係と各データの処理対応として、数学における多様体からソースコード化できる。まず始めに、ソースコードを記述する人が定義したデータベースをライブラリーとして、動的にスクリプト言語に取り込む。

```
import Omega::Tuplespace < DATABASE
{
  {\bigoplus M^{+}_{-} -> =: \nabla R^{+} \nabla C^{+}}-< [construct_emerge_equation.built]
  >> VIRTUALMACHINE[tuplespace]
  => {regexpt.pattern |w|
      w.scan(equal.value) [ > [\nabla \int \int \nabla_{i}\nabla_{j} f \circ g(x)]]
      equal.value.shift => tuplespace.value
      w.emerged >> |value| value.equation_create
      w <- value
      w.pop => tuplespace.value
     }
}
```

多様体の式をバーチャルマシンに方程式として・データベースとして `>>` で入力する。バーチャルマシンに入力されたデータを正規表現で共通要素を抽出し、配列に入っている定義済みの多様体へ数値解析として `>` と入力する。この共通データをデータの端から取り除く値を tuplespace の値としてリスト化する。抽出されたデータを、データベースに取り込んでいる多様体の規則からトリガーとして機能を発動させ、この多様体の値を再び正規表現として `<-` 入力する。データベースの全データを取り入れた段階で再構築し、生成し直す。

- もとのデータ `>>` 対象物のデータ — `>>` は文字入力機能を表す。
- もとのデータ `>-` 対象物のデータ — `>-` はデータの分岐の流れを作る。

```
{\vee (\int \nabla_{i}\nabla_{j} (R + \Delta f)^2) \over \exists (R + \Delta f)} -> =: variable array[]
>> VIRTUAL_MACHINE[tuplespace]
=> {regexpt.pattern |w|
    w.emerged => tuplespace[array]
    w <- value
    w.pop => tuplespace.value
   }
```

多様体を入力する配列を `-> =: 変数 array[]` と表す。`>>` はデータベースに配列として入力する。

```
Omega.DATABASE[tuplespace]->w.emerged >> |value| value.equation_create
{
  w.process <- Omega.space
  {=>
     cognitive_system :=> tuplespace[process.excluded].reload
     assembly_process <- w.file.reload.process
     => : [regexpt.pattern(file)=>text_included.w.process]
  }
}
```

データベースから正規表現で生成された変数値から、それにポインタされた方程式をデータベースをもとで生成する。生成された中で、ソースコードを正規表現にプロセス・マルチスレッド化して、外部のデータを後ろからポインタとして連結する（`w.process <- Omega.space`）。`cognitive_system` を一種の合言葉として `tuplespace[process.excluded]` へ `:=>` でデータを流し reload する。`assembly_process` に `w.file.reload.process` としてポインタを当て、配列のデータベースへファイルに記述されているデータとして再取り込みを行う。

```
Omega.DATABASE[tuplespace]->w.emerged >> |list| list.equation_create
{
  w.process <- Omega.space
  {=>
     poly w.process.cognitive_system :=> tuplespace[process.excluded].reload
     homology w.process :=> tuplespace[process.excluded].reload
     mesh.volume_manifold :=> tuplespace[process.excluded].reload
     \nabla_{i}\nabla_{j} w.process.excluded :=> tuplespace[process.excluded].reload
     {\exp[\int \int (R + \Delta f)^2 e^{-x \log x}dV}.emerge_equation.reality{|repository|
        repository.regexpt.pattern => tuplespace[process.excluded].reload
        tuplespace[process.excluded].rebuild >> Omega.DATABASE[tuplespace]
        {\imaginary.equation => e^{\cos \theta + i\sin \theta}} <=> Omega.DATABASE[tuplespace]
        {{d \over df}F ==> {d \over df}{1 \over {(x \log x)^2 \circ (y \log y)^{1 \over 2}}}dm}.cognitive_system.reload
        :=> [repository.scan(regexpt.pattern) { <=> btree.scan |array| <-> ultranetwork.attachment}
        repository.saved
     }
  }
}
```

作用素環の半静性宣言子としての `poly, homology, equation` が記述されているソースの式を使って、各ポインタを指しているデータ自体にリンクとして双対性をプログラミングしていく。代入子・入力子・等号入力子・倒置入力子: `:=>, >>, ==>, <=>, .emerge_equation.reality, .reload, .cognitive_system, .saved` の各レシーバはオブジェクトから保持している機能を呼び起こせる。

## アスペクト指向の構造体定義 (ultra_database)

```
import ultra_database.included
def < this.class::Omega.DATABASE[first,second,third.fourth] end
 def.first.iterator => array.emerge_equation
 def.second.iterator => array.emerge_equation
 def.third.iterator => array.emerge_equation
 def.fourth.iterator => array.emerge_equation
 _ struct_ {
    Omega.iterator => repository.reload
 }
end
typedef _ struct_ :Omega.aspective
end
```

```
Omega::DATABASE[reload]
{
  [category.repository <-> w.process] <=> catastrophe.category.selected[list]
  list.distributed => ultra_database.exist ->
  w.summurate_pattern[Omega.Database]
  btree.exclude -> this.klass
  list.scan(regexpt.pattern) <-> btree.included
  list.exclude -> [Omega.Database]
  all_of_equation.emerged <=> Omega.Database
  {
    list.summuate -> Omega.Database.excluded
  }
}
```

今までのデータをデータベースにリロードして、不変性を見つけて分類していく。分類された連想配列によるリスト構造をウルトラネットワークへ双対性 `=>` を使って `->` と統合されるべきパターンへ流す。btree 構造体にポインタをつなげてリスト化し、各リストを再びデータベースへつなげる。方程式をデータベースの多様体に入れ、相互に比較してリスト構造体を再編成する。

再編成されたリストを、自分が導いた方程式がどの範疇のデータで何の方程式かを、多様体から意思が生成された認知でもある場の理論として判断させ、未知の理論を多様体からの人工知能で見つける。

## 多様体方程式の代入 (`cognitive_system |value|`)

```
Omega::DATABASE[tuplespace] >> list.cognitive_system |value|
= { x^{{1 \over 2} + iy} = [f(x) \circ g(x), \bar{h}(x)]/ \partial f\partial g\partial h
    x^{{1 \over 2} + iy} = \mathrm{exp}[\int \nabla_{i}\nabla_{j}f(g(x))g'(x)/ \partial f\partial g]
    \mathcal{O}(x) = \{[f(x)\circ g(x) , \bar{h}(x)], g^{-1}(x)\}
    \exists [\nabla_{i} \nabla_{j} (R + \Delta f), g(x)] = \bigoplus_{k=0}^{\infty} \nabla \int \nabla_{i} \nabla_{j}f(x)dm
    \vee (\nabla_{i} \nabla_{j} f) = \bigotimes \nabla E^{+}
    g(x,y) = \mathcal{O}(x)[f(x) + \bar{h}(x)] + T^2 d^2 \phi
    \mathcal{O}(x) = \left( \int [g(x)] e^{-f}dV \right)^{'} - \sum \delta (x)
    \mathcal{O}(x) = [\nabla_{i}\nabla_{j}f(x)]^{'} \cong {}_{n}C_{r} f(x)^{n} f(y)^{n-r} \delta (x,y)
    V(\tau) = \int [f(x)]dm/ \partial f_{xy}
    \square \psi = 8 \pi G T^{\mu\nu}, (\square \psi)^{'} = \nabla_{i}\nabla_{j}(\delta (x) \circ G(x))^{\mu\nu}
    \delta (x) \phi = {\vee [\nabla_{i}\nabla_{j} f \circ g(x)] \over \exists (R + \Delta f)}
    {}_{n}C_{r} = {}_{n}C_{n-r}
    ... (continues; the block enumerates the full operator-algebra of the manifold,
        culminating in the beta/zeta closure) ...
    {\int \int {1 \over (x \log x)(y \log y)}dxy} = ({}_nC_{n-r})^2 \sum ... = \alpha
}
```

> The `cognitive_system |value|` block assigns the paper's whole equation
> catalogue — D²ψ = 8πGT^μν, Ricci flow d/dt g_ij = −2R_ij, the world-line
> norm ds² = e^{−2πT|φ|}[η+h̄_μν]dx^μν + T²d²ψ, ker/im homology, the
> Kaluza-Klein/Schwarzschild forms, V/W ≅ W/V quotient algebra, and the
> nested manifold inclusions M₁⊂M₂⊂M₃ — into the TupleSpace as data.

これまでのデータベース化された機能のもとである方程式たちを構造体としてまとめ、`=> [tuplespace]` としてポインタを当てる:

```
_ struct_ :asperal equation.emerged => [tuplespace]
tuplespace.cognitive_system => development -> Omega.Database[import]
value.equation_emerged.exclude >- Omega.Database[tuplespace]
```

## DSL: 即席スクリプト言語 / ウルトラネットワーク

以下は、多様体のデータを使ってアプリケーションプログラミングとして即席スクリプト言語を DSL として書いたもの。

```
Omega::DataBase <-> virtual_connect(VIRTUALMACHINE)
{
  blidge_base.network => localmachine.attachment
  :=> {
      dhcp.etc_load_file(this.klass) {|list|
       list.connect[XWin.display _ <- xhost.in(regexpt.pattern)]
       {
         ultranetwork.def _struct {
           asperal_language :this.network_address.included[type.system_pattern]
           {|regexpt.pattern|
             <- w.scan
             |each_string| <= { ipv4.file :file.port
                                subnetmask :file.address
                                file.port <=> file.address
                                FILE *pointer
                                int,char,str :emerge.exclude > array[]
                                BTE.each_string <-> regexpt.pattern
                                {
                                  development => file.to_excluded
                                  file.scan => regexpt.pattern
                                  this.iterator <-> each_string
                                  file.reloded => [asperal_language.rebuild]
                                }
                              }
           }
         }
       }
      }
  }
}
```

```
class Ultranetwork
 def virtual_connect
  load :file => {
   asperal :virtual_machine.attachment
   {
     system.require :file.attachment
     <- |list.file| :=> {
         tk.mainloop <- [XWin -multiwindow]
         startx => file.load.environment
         in { [blidge_base | host_base].connect(wmware.dhcp)
              net_work.connect.used[wireshark.demand => exclude(file)]
            }
        }
   }
  }
 end
```

`def < method` で、メソッドを def へリファクタリング機能で取り込む。これは `def one class` 並の等号シングルトンとして機能する。続いて `blidge_base.network.connect` / `host_base.ethernet.connect` / `etc.load_file` / `network_rout` / `launcher_application` / `terminal_port` / `kterm_port` の各 `def` が定義され、`main_loop` で `[file, launcher_application, terminal_port, kterm_port].def < included` を `encoding-utf8` でまとめる。

```
class < def {
  pholograph_data[] = [R,V,S,E,U,M_n,Z_n,Q,C,N,f,g]
  source_array <- pholograph_data[]
}
def > operator_data[] = {nabla, nabla_i nabla_j, Delta, partial,
   d, int, cap, cup, ni, in, chi, oplus, otimes, bigoplus, bigotimes, d/over df, ...}
end
def > manifold_emerge
  c = def.inject >- source_array times def.operator_data[]
  repository_data <=> c{
    c.scan(/tupplespace[]/)
    import |list| list{
      kerf = -2 \int (R + nabla_i nabla_j f)^2 e^{-f}dV
      kerf / imf
      =< {d \over df}F}
  }
  equals_data =~ /list/
  list.match(/"#{c}"/) {|list|
     list.delete
     jisyo_data_mathmatics <=> list{
        list.emerge => {asperal function >- pholograph_data[] times repository_data =< list.update}
     }
     ln -s operator_named <= {list}
     define _struct |list|
       -> list.element -> manifold_emerge
       => list.reconstruct > def.inject /^"#{pattern}"/}
end
```

`pholograph_data[]`（写像データ: R,V,S,E,U,M_n,Z_n,Q,C,N,f,g）と `operator_data[]`（微分幾何作用素）を掛け合わせて `manifold_emerge` を生成する作用素環の核。

## リバイザ (@reviser) と Streem スタイル

リバイザを使うと、独自のタプルスペースで一時保存の書き換えの分派スクリプトが出来て、例外処理機能として独自に機能拡張できる。構文解析器も文字抽出器も全部書き換えられる。書き換えたものをライブラリとしてデータベースに取り込むと、タプルスペースが働き、今まで使ってきた機能と一線を画す。

```
@reviser : def < OmegaDatabase[tuplespace].mechanism
{
  aspective : _union _ {
    int streem_style : [ > [def.each{x -> stdin | stdout > display :xhost in XWin -multiwindow}
    {
      Endire <- [ADD,EVEN,ODE,EXOR,XOR,DEL,DIFF,PARTIAL,INT].included > struct _ :-> _union
      Endire.each{def.value -> def.key :hash.define}.included > _union}
    }
}
```

```
int
streem_style {
  :Endire <- [ADD,EVEN,MOD,DEL,MIX,INCLUDED,EXCLUDED,EBN,EXN,EOR,EXOR,
              SUM,INT,DIFF,PARTIAL,ROUND,HOMOLOGY,MESH]
  Endire.interator -> {def < :Endire.element, -> def.means_each{x -> expression.define.included}
  def.each{x -> case :x.each => :lex.include_ . in [ > [x.all_expire] ]}
}
main_loop {
  FILE *fp :=> streem_style.address_objective_space
  fp.each{x -> domain_specific_language_style_included[array]}
  array << streem.DATABASE[tuplespace]
  array.each{[tuplespace] -> aimed[tuplespace] | OMEGA_DATABASE[tuplespace]}.excluded <-> array
  def.key <-> def.value => {x -> stdin | stdout |=> streem_style <- def.each.klass.value}
}
```

例外処理 (`begin / case :one_exist :other :bug / ensure`) の中では、バグ値を `cognitive_system.scan(bug[value])` で走査し、オイラー方程式の native_function を用いて
`{[e^{-f}[{2 \int (R + \nabla f^2) \over -(R + \Delta f)}e^{-f}dV}` の created_field を再構築 (`\summuate_manifold.recreated`) し、`return :success_exit => Tuplespace[DATABASE]` する。

```
import perl.lib | python.lib <-> ruby.lib
{
  int @reviser : def.each{x -> x.klass |-> $variable in $stdin | $stdout}
  .developed >= {
     ping localhost -> blidgebase <-> hostbase.virtualmachine.attachment
     { xhost :display -> streem_style.value
       networkconnect.hostbase -> localarea.virtualmachine
     } :connected -> networkrout : flow_to :localhost.attachment
  }
}
```

キーフック cmd（Emacs 風）構造体:

```
cmd _struct : {
  [ ^C-O : ^C-X-F, exit.cmd : ^C-X-C, shift-up : ^C-P, shift-down : ^C-N]
}
cmd _union : def.restructed
keyhook.cmd <- : [_struct ]
{
  @reviser :def._struct <-> def. _union
}
```

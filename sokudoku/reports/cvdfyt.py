ディレクトリ名とソースコードは、`SourceCodeExtractor`クラスの`source_code`という辞書に保存されます。

具体的な保存方法は以下の通りです:

1. **ディレクトリ名の保存**
   - ディレクトリ名は、パス形式で保存されます。
   - 例えば、`omega_script/lib/math/manifold.c`のように、ディレクトリ階層を表すパスが`source_code`の辞書のキーとなります。

2. **ソースコードの保存**
   - ディレクトリ名に対応するソースコードは、`source_code`辞書の値として保存されます。
   - 例えば、`omega_script/lib/math/manifold.c`のソースコードは、`source_code['omega_script/lib/math/manifold']`というキーに保存されます。

この`source_code`辞書の構造は以下のようになります:

```python
{
    'omega_script/lib/math/manifold': '''
#include "manifold.h"

Manifold* Manifold_create(int dimension) {
    // ...
}

void Manifold_add_point(Manifold* manifold, OmegaType* point) {
    // ...
}
    ''',
    'omega_script/lib/network/tuplespace': '''
#include "tuplespace.h"

TupleSpace* TupleSpace_create() {
    // ...
}

void TupleSpace_add_tuple(TupleSpace* tuplespace, OmegaType* tuple) {
    // ...
}
    ''',
    # ... (other directories and their source code)
}
```

この`source_code`辞書は、`create_directories_and_files`メソッドで使用されます。このメソッドでは、辞書のキー(ディレクトリ名)を使ってディレクトリを作成し、値(ソースコード)をファイルに書き出します。

このように、ディレクトリ名とソースコードを`source_code`辞書に保存することで、ソースコードの抽出と配置が効率的に行えるようになっています。

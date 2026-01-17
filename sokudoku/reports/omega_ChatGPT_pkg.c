```c
/* pkginstallgen.c
   指定されたレポート群を基に、"ChatGPT-like" トイ実装をパッケージ一式で生成する小さなジェネレータ。
   コンパイルして実行すると、カレントディレクトリにパッケージフォルダ "toy_chatgpt_pkg"
   を生成し、ソース、インストールスクリプト、README を作成します。

   使用例:
     gcc -O2 -o pkginstallgen pkginstallgen.c
     ./pkginstallgen

   生成物の構成 (toy_chatgpt_pkg):
     - bin/run.sh                : 起動スクリプト (仮想環境作成と実行)
     - src/toy_chatbot.py        : ミニマルTransformerベースのtoyモデル (Python)
     - src/omega_modules/        : Omegaスクリプト／モジュール例（レポート由来の概念をDSLで表現）
         - manifold.omega
         - tuplespace.omega
         - catastrophe.omega
     - LICENSE
     - README.md
     - setup/install.sh          : インストール（依存インストール）用スクリプト
     - pkgmeta.json              : パッケージメタ情報
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void write_file(const char *path, const char *content) {
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "Error: cannot open %s for writing\n", path); exit(1); }
  fwrite(content, 1, strlen(content), f);
  fclose(f);
}

int main(void) {
  const char *pkgdir = "toy_chatgpt_pkg";
  system("rm -rf toy_chatgpt_pkg");
  if (mkdir(pkgdir, 0755) != 0) { /* ignore error on some platforms */ }
  system("mkdir -p toy_chatgpt_pkg/src/omega_modules");
  system("mkdir -p toy_chatgpt_pkg/setup");
  system("mkdir -p toy_chatgpt_pkg/bin");

    const char *readme =
"# toy_chatgpt_pkg\n\n"
"このパッケージは、提供されたレポート群の概念（タプルスペース、多様体、カタストロフィー等）を\n"
"参照した「ChatGPT-like」教育用トイ実装一式を生成します。実運用を意図したものではなく、概念の\n"
"プロトタイプとパッケージ化手順を示すためのものです。\n\n"
"構成:\n"
"- src/toy_chatbot.py: ミニマルTransformerベースの実装（学習/対話可）\n"
"- src/omega_modules/: Omegaスクリプト風モジュール例（概念表現）\n"
"- setup/install.sh: 依存インストールとセットアップスクリプト\n"
"- bin/run.sh: 起動用ラッパースクリプト\n\n"
"使い方（UNIX系）:\n"
"  bash setup/install.sh\n"
"  bash bin/run.sh\n\n"
      "ライセンス: MIT\n";

    const char *license =
"MIT License\n\n"
"Copyright (c) 2025\n\n"
"Permission is hereby granted, free of charge, to any person obtaining a copy\n"
"of this software and associated documentation files (the \"Software\"), to deal\n"
"in the Software without restriction, including without limitation the rights\n"
"to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
"copies of the Software, and to permit persons to whom the Software is\n"
"furnished to do so, subject to the following conditions:\n\n"
      "[省略: 実際の配布では完全なMIT文を保持してください]\n";

    const char *pkgmeta =
"{\n"
"  \"name\": \"toy_chatgpt_pkg\",\n"
"  \"version\": \"0.1.0\",\n"
"  \"description\": \"Educational ChatGPT-like toy package with Omega script stubs\",\n"
"  \"author\": \"Generated\",\n"
"  \"license\": \"MIT\"\n"
      "}\n";

    const char *run_sh =
"#!/usr/bin/env bash\n"
"set -e\n"
"PKGROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\n" 
"cd \"$PKGROOT/src\"\n"
"if [ -z \"$VIRTUAL_ENV\" ]; then\n"
"  python3 -m venv .venv\n"
"  source .venv/bin/activate\n" 
"  pip install --upgrade pip\n" 
"  pip install torch --quiet || true\n"
"fi\n"
      "python3 toy_chatbot.py\n";

    const char *install_sh =
      "#!/usr/bin/env bash\nset -e\nROOT=\"$(cd \"$(dirname \"$0\")/..\" && pwd)\"\ncd \"$ROOT/src\"\npython3 -m venv .venv\n. .venv/bin/activate\npip install --upgrade pip\npip install torch\necho \"Setup complete. Run: $ROOT/bin/run.sh\"\n";

    const char *toy_chatbot_py =
      "# toy_chatbot.py\n# Minimal, original transformer toy for demonstration (derived from submitted material).\n# Requires: Python 3.8+, PyTorch (optional; fallback to a rule-based responder if absent).\n\nimport sys\ntry:\n    import torch\n    import torch.nn as nn\n    import torch.nn.functional as F\n    import math, random\n    TORCH_AVAILABLE = True\nexcept Exception:\n    TORCH_AVAILABLE = False\n\n# Very small tokenizer\nclass SimpleTokenizer:\n    def __init__(self):\n        self.special = ['<pad>','<unk>','<bos>','<eos>']\n        self.vocab = {w:i for i,w in enumerate(self.special)}\n        self.inv = {i:w for w,i in self.vocab.items()}\n    def build(self, texts):\n        freq = {}\n        for t in texts:\n            for tok in t.strip().split():\n                freq[tok]=freq.get(tok,0)+1\n        idx = len(self.vocab)\n        for tok in sorted(freq.keys()):\n            if tok not in self.vocab:\n                self.vocab[tok]=idx; idx+=1\n        self.inv = {i:w for w,i in self.vocab.items()}\n    def encode(self, text):\n        toks = ['<bos>'] + text.strip().split() + ['<eos>']\n        return [self.vocab.get(t,self.vocab['<unk>']) for t in toks]\n    def decode(self, ids):\n        words = []\n        for i in ids:\n            w = self.inv.get(int(i),'<unk>')\n            if w in ('<bos>','<eos>','<pad>'): continue\n            words.append(w)\n        return ' '.join(words)\n\n# Fallback rule-based responder\ndef rule_respond(text):\n    t = text.lower()\n    if 'hello' in t or 'hi' in t: return 'hi'\n    if 'name' in t: return 'i am toybot'\n    if 'boil' in t and 'water' in t: return 'Water boils at 100 degrees Celsius.'\n    if 'joke' in t: return 'Why did the chicken cross the road?'\n    return \"I'm a toy model. I can echo: \" + text\n\nif not TORCH_AVAILABLE:\n    def main():\n        print('Torch not available — running rule-based toy responder.')\n        while True:\n            try:\n                q = input('You: ')\n            except EOFError:\n                break\n            if q.strip().lower() in ('exit','quit'):\n                break\n            print('Bot:', rule_respond(q))\n    if __name__=='__main__': main()\n    sys.exit(0)\n\n# Minimal tiny transformer-like architecture (kept tiny to run on CPU)\nclass TinyModel(nn.Module):\n    def __init__(self, vocab_size, d_model=64, nhead=4):\n        super().__init__()\n        self.emb = nn.Embedding(vocab_size, d_model)\n        self.pos = nn.Parameter(torch.zeros(256,d_model))\n        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward=128)\n        self.enc = nn.TransformerEncoder(encoder_layer, num_layers=2)\n        self.out = nn.Linear(d_model, vocab_size)\n    def forward(self, src):\n        # src: (S, B)\n        x = self.emb(src) + self.pos[:src.size(0)].unsqueeze(1)\n        h = self.enc(x)\n        return self.out(h)\n\n# Toy dataset from reports (small examples)\npairs = [\n    (\"hello\",\"hi\"),\n    (\"what is your name\",\"i am a toybot\"),\n    (\"what is the boiling point of water\",\"water boils at 100 degrees celsius\"),\n    (\"tell me a joke\",\"why did the chicken cross the road\")\n]\n\ndef build_tokenizer(pairs):\n    t = SimpleTokenizer()\n    texts = []\n    for a,b in pairs: texts.append(a); texts.append(b)\n    t.build(texts)\n    return t\n\ndef train_loop(tok, model, device, epochs=200):\n    opt = torch.optim.Adam(model.parameters(), lr=1e-3)\n    lossfn = nn.CrossEntropyLoss()\n    model.train()\n    for ep in range(epochs):\n        total=0.0\n        for src,tgt in pairs:\n            sids = torch.tensor([tok.encode(src)], dtype=torch.long).transpose(0,1).to(device)\n            tids = torch.tensor([tok.encode(tgt)], dtype=torch.long).transpose(0,1).to(device)\n            tgt_in = tids[:-1]\n            tgt_out = tids[1:]\n            logits = model(torch.cat([sids,tgt_in], dim=0))\n            # take the tail corresponding to tgt_out\n            pred = logits[-tgt_out.size(0):]\n            loss = lossfn(pred.view(-1,pred.size(-1)), tgt_out.view(-1))\n            opt.zero_grad(); loss.backward(); opt.step()\n            total += loss.item()\n        if (ep+1) % 100 == 0:\n            print(f'Epoch {ep+1} loss {total/len(pairs):.4f}')\n\n@torch.no_grad()\ndef respond(model,tok,device,src_text,max_len=30):\n    sids = torch.tensor([tok.encode(src_text)], dtype=torch.long).transpose(0,1).to(device)\n    memory = model(torch.cat([sids],dim=0))\n    # greedy append using bos as start\n    ys = torch.tensor([[tok.vocab['<bos>']]], dtype=torch.long).to(device)\n    ys = ys.transpose(0,1)  # (1,1)\n    for i in range(max_len):\n        logits = model(torch.cat([sids, ys], dim=0))\n        next_logits = logits[-1,0]\n        nid = torch.argmax(next_logits).unsqueeze(0)\n        ys = torch.cat([ys, nid.unsqueeze(1)], dim=0)\n        if int(nid.item()) == tok.vocab['<eos>']: break\n    ids = ys.squeeze(1).cpu().numpy().tolist()\n    return tok.decode(ids)\n\ndef main():\n    device = torch.device('cpu')\n    tok = build_tokenizer(pairs)\n    model = TinyModel(vocab_size=len(tok.vocab)).to(device)\n    train_loop(tok, model, device, epochs=200)\n    print('Toy model ready. exit to quit.')\n    while True:\n        q = input('You: ')\n        if q.strip().lower() in ('exit','quit'): break\n        print('Bot:', respond(model,tok,device,q))\n\nif __name__=='__main__': main()\n";

    const char *omega_manifold =
      "# manifold.omega\n# Omegaスクリプト風モジュール (概念的スタブ)\nmodule Manifold\n  # サーストン・ペレルマン多様体を表現するための概念的インターフェース\n  def construct(knowledge)\n    # knowledge (文字列) を受け取り、多様体上の点として登録する（スタブ）\n    tuplespace.add({type:'manifold_point', text:knowledge})\n  end\n  def search(query_tuple)\n    # クエリに関連する多様体領域を返す（スタブ）\n    return tuplespace.find { |e| e[:text].include?(query_tuple) }\n  end\nend\n";

    const char *omega_tuplespace =
      "# tuplespace.omega\nmodule TupleSpace\n  def init\n    @store = []\n  end\n  def add(item)\n    @store << item\n  end\n  def find(&blk)\n    @store.select(&blk)\n  end\n  def parse(text)\n    text.downcase\n  end\nend\n";

    const char *omega_catastrophe =
      "# catastrophe.omega\nmodule Catastrophe\n  def classify(knowledge)\n    # トムの7種のカタストロフィー理論を用いた分類（概念的）\n    tuplespace.add({type:'catastrophe_class', class:'generic', text:knowledge})\n  end\n  def analyze(query)\n    # クエリに対するカタストロフィー分析（スタブ）\n    return {model:'fold', severity:0}\n  end\nend\n";

    write_file("toy_chatgpt_pkg/README.md", readme);
    write_file("toy_chatgpt_pkg/LICENSE", license);
    write_file("toy_chatgpt_pkg/pkgmeta.json", pkgmeta);
    write_file("toy_chatgpt_pkg/bin/run.sh", run_sh);
    write_file("toy_chatgpt_pkg/setup/install.sh", install_sh);
    write_file("toy_chatgpt_pkg/src/toy_chatbot.py", toy_chatbot_py);
    write_file("toy_chatgpt_pkg/src/omega_modules/manifold.omega", omega_manifold);
    write_file("toy_chatgpt_pkg/src/omega_modules/tuplespace.omega", omega_tuplespace);
    write_file("toy_chatgpt_pkg/src/omega_modules/catastrophe.omega", omega_catastrophe);

    system("chmod +x toy_chatgpt_pkg/bin/run.sh toy_chatgpt_pkg/setup/install.sh");

    puts("Package 'toy_chatgpt_pkg' created.");
    puts("Run: bash toy_chatgpt_pkg/setup/install.sh  # to setup venv and deps");
    puts("Then: bash toy_chatgpt_pkg/bin/run.sh         # to run the toy chatbot");

    return 0;
}
```

omega_langnet_pkg - generated prototype

Build: cd omega_langnet_pkg && make
Run examples: ./bin/tools --entropy "some text"
BNF parse: ./bin/tools --bnf-parse examples/sample.bnf out_ast.json
Python codegen: make pygen (requires out_ast.json and python3)

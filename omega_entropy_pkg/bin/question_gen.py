#!/usr/bin/env python3
"""
question_gen.py
Generate question templates including entropy-targeted variations.
Usage: question_gen.py out_questions.txt
"""
import sys
if len(sys.argv)<2:
    print('Usage: question_gen.py out_questions.txt'); sys.exit(2)
out = sys.argv[1]
qs = []
qs.append('このレポートから何ができるか？(What can be done based on this report?)')
qs.append('このレポートの主題は何か？(What is the main topic?)')
qs.append('定理や主要主張はどのような記法で示されているか？(In what form are theorems presented?)')
qs.append('証明の主要な手順はどの文に書かれているか？(Which sentences contain the main proof steps?)')
qs.append('結論はどこにあり、何を述べているか？(Where is the conclusion and what does it state?)')
# entropy-targeted questions: low/medium/high entropy examples
qs.append('低エントロピー(=単純/要約的)な記述はどこにあるか？(Where are low-entropy sentences?)')
qs.append('中程度のエントロピー(=説明的)な記述はどこにあるか？(Where are medium-entropy sentences?)')
qs.append('高エントロピー(=情報量高/式多)な記述はどこにあるか？(Where are high-entropy sentences?)')
qs.append('指定エントロピー値 H に最も一致する文を返してください。例: H=2.0')
open(out,'w',encoding='utf-8').write('\n'.join(qs))
print('Wrote',out)

#!/usr/bin/env python3
import sys
import math
import os
from collections import Counter

try:
    import sympy as sp
    SYMPY = True
except Exception:
    SYMPY = False

  def read_input(path):
  with open(path, 'r', encoding='utf-8') as f:
  lines = [ln.strip() for ln in f.readlines()]
  return [ln for ln in lines if ln and not ln.startswith('#')]

  def parse_expr(text):
  if SYMPY:
    try:
      e = sp.sympify(text)
            return e
        except Exception:
            return text
	    else:
        return text

	  def pseudo_jones_polynomial(expr):
	  s = str(expr)
	  seed = sum(ord(ch) for ch in s) % 9973
	  d = 1 + (seed % 5)   # degree 1..5
    coeffs = []
	  for k in range(d+1):
# 簡易: seed を基に符号付き係数を生成
	  v = ((seed * (k+1)) ^ (k * 2654435761)) & 0xffffffff
        # map to signed small integer
	    ai = ((v % 31) - 15)
	    coeffs.append(float(ai))
    # normalize so not all zero
	    if all(abs(c) < 1e-12 for c in coeffs):
        coeffs[0] = 1.0
    return coeffs

	  def coeffs_entropy(coeffs):
    # 係数を確率分布化してシャノンエントロピーを計算
    # 絶対値を使い分布を作る（係数の大きさが重要）
	  mags = [abs(c) for c in coeffs]
	    s = sum(mags)
	    if s == 0:
        return 0.0
    ps = [m / s for m in mags]
    H = 0.0
	  for p in ps:
	  if p > 0:
            H -= p * math.log2(p)
    return H

	      def branch_formulas(expr_text, H, branches=5):
    out = []
		     for i in range(branches):
        # produce a variant by appending a small numeric offset based on H and i
		   offset = ((H * 100.0) % 7.0) * (0.1 + 0.05 * i)
# create variant string: try to insert "* (1 + offset)" to top-level expression
        variant = f"({expr_text}) * (1 + {offset:.6g})"
        val = None
		     if SYMPY:
		     try:
		       val = float(sp.N(sp.sympify(variant)))
			 except Exception:
                val = None
		     else:
# try safe eval of a numeric expression if only numbers present (fallback)
		       try:
			 val = float(eval(variant, {"__builtins__":None}, {}))
			 except Exception:
                val = None
			 out.append((variant, val))
    return out

			 def merge_branches(branch_results):
			 vals = [v for (_, v) in branch_results if v is not None]
			 if not vals:
        return None
	  return sum(vals) / len(vals)

	  def infer_document_meta(formulas_info):
    # pick formula with max H
				  maxH = -1.0; maxinfo = None
						 for info in formulas_info:
						 if info['entropy'] > maxH:
						   maxH = info['entropy']; maxinfo = info
    title = f"Analysis of expression: {maxinfo['text'][:60]}"
    theorem = f"Theorem (auto): For expression '{maxinfo['text']}', the computed Jones-like invariant has entropy H = {maxinfo['entropy']:.6g}."
    # build proof text from verification results
    proof_lines = []
									     for info in formulas_info:
									     ok = info.get('verified', False)
									       proof_lines.append(f"- Expression '{info['text'][:40]}...' verification: {'VALID' if ok else 'FAILED'} (merged value={info.get('merged')})")
									       proof = "\n".join(proof_lines)
									       if all(info.get('verified', False) for info in formulas_info):
        concluded = "All expressions merged to the target Jones-like invariant; verification considered successful."
        conjectured = ""
	else:
        concluded = "Not all verifications passed; further analysis required."
        conjectured = "Conjecture: adjusting entropy substitution or polynomial model may yield convergence."
	  return dict(title=title, theorem=theorem, proof=proof, concluded=concluded, conjectured=conjectured)

	  def generate_latex(docmeta, formulas_info, outpath):
    # simple LaTeX document
	  with open(outpath, 'w', encoding='utf-8') as f:
	  f.write(r"\documentclass{article}" + "\n")
	  f.write(r"\usepackage{amsmath,amssymb}" + "\n")
	  f.write(r"\begin{document}" + "\n\n")
	  f.write(r"\title{" + escape_latex(docmeta['title']) + "}\n")
	  f.write(r"\maketitle" + "\n\n")
	  f.write(r"\section*{Theorem}\n")
	  f.write(r"\begin{quote}" + "\n")
	  f.write(escape_latex(docmeta['theorem']) + "\n")
	  f.write(r"\end{quote}" + "\n\n")
	  f.write(r"\section*{Proof (auto)}" + "\n")
	  f.write(r"\begin{verbatim}" + "\n")
	  f.write(docmeta['proof'] + "\n")
	  f.write(r"\end{verbatim}" + "\n\n")
	  f.write(r"\section*{Details}" + "\n")
	  for info in formulas_info:
	  f.write(r"\subsection*{Expression}" + "\n")
            f.write(r"\begin{verbatim}" + "\n")
            f.write(info['text'] + "\n")
            f.write(r"\end{verbatim}" + "\n")
            f.write(r"\paragraph{Jones-like polynomial coefficients:}\n")
            f.write(r"\(" + coeffs_to_tex(info['jones_coeffs']) + r"\)" + "\n\n")
            f.write(r"\paragraph{Entropy:} " + f"{info['entropy']:.6g}" + "\n\n")
            f.write(r"\paragraph{Branch results:}\n")
            f.write(r"\begin{verbatim}" + "\n")
            for v in info['branches']:
	  f.write(f"{v[0]} => {v[1]}\n")
            f.write(r"\end{verbatim}" + "\n\n")
	    f.write(r"\section*{Conclusion}\n")
	    f.write(escape_latex(docmeta['concluded']) + "\n\n")
	    if docmeta['conjectured']:
            f.write(r"\section*{Conjecture}\n")
	      f.write(escape_latex(docmeta['conjectured']) + "\n")
	      f.write(r"\end{document}" + "\n")
	      print(f"Wrote LaTeX to {outpath}")

	      def coeffs_to_tex(coeffs):
    parts = []
      for i,c in enumerate(coeffs):
      parts.append(f"{c:.6g}t^{i}")
	return " + ".join(parts)

	def escape_latex(s):
    # minimal escaping
	return s.replace('\\', r'\\').replace('_', r'\_').replace('%', r'\%')

	  def main():
	  if len(sys.argv) < 3:
	    print("Usage: omega-proof.py input.txt output.tex")
	      sys.exit(2)
	      inp = sys.argv[1]; out = sys.argv[2]
				   lines = read_input(inp)
    formulas_info = []
				   for ln in lines:
				   expr = parse_expr(ln)
				     coeffs = pseudo_jones_polynomial(expr)
				     H = coeffs_entropy(coeffs)
				     branches = branch_formulas(ln, H, branches=7)
				     merged = merge_branches(branches)
# verification rule: if merged is within small tolerance of some function of coeffs (e.g. mean(coeffs))
				     baseline = sum(coeffs)/len(coeffs) if coeffs else 0.0
        verified = False
											 if merged is not None:
				   verified = abs(merged - baseline) < (0.5 + 0.1 * abs(baseline))
				     info = {
											   'text': ln,
											   'parsed': expr,
											   'jones_coeffs': coeffs,
											   'entropy': H,
											   'branches': branches,
											   'merged': merged,
											   'verified': verified
											   }
				   formulas_info.append(info)
				   docmeta = infer_document_meta(formulas_info)
				   generate_latex(docmeta, formulas_info, out)

				   if __name__ == '__main__':
				   main()


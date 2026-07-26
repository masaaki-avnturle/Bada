# Build the paper PDF (requires a CJK-capable LaTeX engine).
PAPER=maglev_os_paper
all: $(PAPER).pdf
$(PAPER).pdf: $(PAPER).tex
	xelatex $(PAPER).tex || lualatex $(PAPER).tex
clean:
	rm -f $(PAPER).aux $(PAPER).log $(PAPER).out $(PAPER).pdf

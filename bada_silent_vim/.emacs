;;; .emacs --- Bada language support for Emacs  -*- lexical-binding: t; -*-
;;
;; Usage: copy/symlink to ~/.emacs (or load it), and point Emacs at the Bada
;; toolchain (the bada_silent_vim directory) via the BADA_HOME env var, or:
;;     (setq bada-home "/path/to/Bada/bada_silent_vim")

(defvar bada-home
  (or (getenv "BADA_HOME")
      (and load-file-name (file-name-directory load-file-name))
      default-directory)
  "Directory containing the Bada toolchain (the `bada' Python package).")

;; --- reserved words / builtins (the language's functional words) -----------
(defconst bada-keywords
  '("print" "say" "if" "else" "while" "repeat" "return" "def"
    "push" "pop" "true" "false" "nil" "Omega")
  "Bada reserved keywords.")

(defconst bada-builtins
  '("len" "append" "idiv" "imod" "abs" "pow2" "str")
  "Bada builtin functions.")

(defconst bada-all-words (append bada-keywords bada-builtins))

;; --- syntax table: // line comments, _ is a word char ----------------------
(defvar bada-mode-syntax-table
  (let ((st (make-syntax-table)))
    (modify-syntax-entry ?_ "w" st)
    (modify-syntax-entry ?/ ". 12" st)   ; // ... starts a comment
    (modify-syntax-entry ?\n ">" st)     ; newline ends it
    (modify-syntax-entry ?\" "\"" st)
    (modify-syntax-entry ?' "\"" st)
    st)
  "Syntax table for `bada-mode'.")

;; --- font-lock highlighting ------------------------------------------------
(defconst bada-font-lock-keywords
  (list
   ;; instruction-oriented directive objects + manifold operators
   (cons "<->\\|<-\\|-<\\|->\\|>-\\|>>\\|=>\\|::" 'font-lock-keyword-face)
   (cons (regexp-opt bada-keywords 'symbols) 'font-lock-keyword-face)
   (cons (regexp-opt bada-builtins 'symbols) 'font-lock-builtin-face)
   ;; def NAME -> function name
   (list "\\<def\\>[ \t]+\\(\\sw+\\)" 1 'font-lock-function-name-face)
   (cons "\\<[0-9]+\\(\\.[0-9]+\\)?\\>" 'font-lock-constant-face))
  "Highlighting for `bada-mode'.")

;; --- completion-at-point: functional words + buffer symbols ----------------
(defun bada-completion-at-point ()
  "Complete reserved words, builtins and identifiers in the buffer."
  (let ((bounds (bounds-of-thing-at-point 'symbol)))
    (when bounds
      (let ((cands (copy-sequence bada-all-words)))
        (save-excursion
          (goto-char (point-min))
          (while (re-search-forward "\\_<\\([a-zA-Z_][a-zA-Z0-9_]*\\)\\_>" nil t)
            (let ((m (match-string-no-properties 1)))
              (unless (member m cands) (push m cands)))))
        (list (car bounds) (cdr bounds) (sort cands #'string<)
              :exclusive 'no)))))

;; --- grammar check / run via the Bada toolchain ----------------------------
(defun bada--cmd (args)
  (format "PYTHONPATH=%s python3 -W ignore %s"
          (shell-quote-argument (expand-file-name bada-home)) args))

(defun bada-check ()
  "Run the Bada grammar checker on the current file (compilation buffer)."
  (interactive)
  (when buffer-file-name (save-buffer))
  (let ((compilation-error-regexp-alist '(("^\\(.*\\):\\([0-9]+\\):\\([0-9]+\\):" 1 2 3)))
        (cmd (bada--cmd (format "-m bada.lint %s"
                                (shell-quote-argument
                                 (expand-file-name buffer-file-name))))))
    (compilation-start cmd)))

(defun bada-run ()
  "Run the current Bada file on the VM."
  (interactive)
  (when buffer-file-name (save-buffer))
  (compilation-start
   (bada--cmd
    (format "-c %s %s"
            (shell-quote-argument
             "import sys; from bada import run_program; run_program(sys.argv[1])")
            (shell-quote-argument (expand-file-name buffer-file-name))))))

;; --- the mode --------------------------------------------------------------
(define-derived-mode bada-mode prog-mode "Bada"
  "Major mode for editing Bada source."
  :syntax-table bada-mode-syntax-table
  (setq-local font-lock-defaults '(bada-font-lock-keywords))
  (setq-local comment-start "// ")
  (setq-local comment-end "")
  (setq-local indent-tabs-mode nil)
  (setq-local tab-width 2)
  (add-hook 'completion-at-point-functions
            #'bada-completion-at-point nil t)
  (electric-pair-local-mode 1))

(add-to-list 'auto-mode-alist '("\\.bada\\'" . bada-mode))

(with-eval-after-load 'bada-mode
  (define-key bada-mode-map (kbd "C-c C-c") #'bada-check)
  (define-key bada-mode-map (kbd "C-c C-r") #'bada-run))

(provide 'bada-mode)
;;; .emacs ends here

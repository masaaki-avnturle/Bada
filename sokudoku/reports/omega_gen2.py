下記は、先に作成した「レポート由来のゼータ関数テンプレートで Omega スクリプト群を生成するパッケージ」を C 言語で出力するビルド可能プログラムと Makefile です。ビルドすると実行ファイル `pkginstallgen` ができ、`make install` を実行すると指定した PREFIX 配下にパッケージ（bin, lib, include, etc, sbin, usr/...）を展開します。

使い方
- 保存ファイル: `pkginstallgen.c` と `Makefile`
- ビルド: make
- インストール（デフォルト PREFIX=/usr/local/omega_pkg）: sudo make install
- 別 PREFIX へ: sudo make install PREFIX=/opt/myprefix

注意
- 生成物は Python スクリプトやテンプレート等で構成されます。実行には Python3 と sympy/mpmath 等が必要です（必要なら sbin/check_deps.sh を実行してください）。

ファイル: pkginstallgen.c
```c
/* pkginstallgen.c
   Generate the Omega-script generator package files under given prefix.
   Usage: pkginstallgen PREFIX
   If PREFIX omitted, defaults to /usr/local/omega_pkg
*/
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>

static void mkdir_p(const char *path) {
    char tmp[4096];
    char *p;
    size_t len;
    snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (len == 0) return;
    if (tmp[len-1] == '/') tmp[len-1] = '\0';
    for (p = tmp + 1; *p; ++p) {
        if (*p == '/') {
            *p = '\0';
            if (mkdir(tmp, 0755) && errno != EEXIST) {
                fprintf(stderr, "mkdir %s: %s\n", tmp, strerror(errno));
                exit(1);
            }
            *p = '/';
        }
    }
    if (mkdir(tmp, 0755) && errno != EEXIST) {
        fprintf(stderr, "mkdir %s: %s\n", tmp, strerror(errno));
        exit(1);
    }
}

static void write_file_mode(const char *path, const char *content, mode_t mode) {
    FILE *f;
    char parent[4096];
    strncpy(parent, path, sizeof(parent)-1); parent[sizeof(parent)-1]=0;
    char *s = strrchr(parent, '/');
    if (s) {
        *s = 0;
        mkdir_p(parent);
    }
    f = fopen(path, "wb");
    if (!f) { perror(path); exit(1); }
    if (fwrite(content, 1, strlen(content), f) != strlen(content)) {
        perror("fwrite");
        fclose(f);
        exit(1);
    }
    fclose(f);
    if (mode) chmod(path, mode);
}

/* Below: embedded contents (Python scripts, templates, configs) */
static const char *bin_omega_gen =
#!/usr/bin/env python3\n"
\"\"\"\n"
omega_gen.py\n"
Generate an Omega-script package guided by zeta/gamma/function-equation snippets\n"
extracted from the provided report text.\n"
\"\"\"\n"
import argparse\n"
from pathlib import Path\n"
from lib.omega.generator import OmegaGenerator\n\n"
def main():\n"
    p = argparse.ArgumentParser()\n"
    p.add_argument(\"--outdir\",\"-o\", default=\"out_omega_report_pkg\")\n"
    p.add_argument(\"--name\",\"-n\", default=\"omega_report_pkg\")\n"
    p.add_argument(\"--template\",\"-t\", default=\"report_zeta\")\n"
    p.add_argument(\"--s\",\"-s\", default=\"0.5+14.134725i\", help=\"complex s for zeta evaluation\")\n"
    args = p.parse_args()\n\n"
    gen = OmegaGenerator(package_name=args.name, outdir=Path(args.outdir))\n"
    gen.generate(template_name=args.template, s_arg=args.s)\n"
    print('Generated package at:', args.outdir)\n\n"
if __name__ == '__main__':\n"
    main()\n";

static const char *lib_generator =
# generator.py\n"
from pathlib import Path\n"
import os\n" 
from .templates import TEMPLATES\n"
from .zeta_utils import parse_complex, zeta_value, gamma_value, functional_equation_xi\n"
import json\n\n"
class OmegaGenerator:\n"
    def __init__(self, package_name='omega_pkg', outdir=Path('out_omega_pkg')):\n"
        self.package_name = package_name\n"
        self.outdir = Path(outdir)\n"
        self.pkg_root = self.outdir / self.package_name\n\n"
    def _ensure_dirs(self):\n"
        for d in ['bin','lib','include','etc','sbin','usr/share/doc','lib/omega']:\n"
            p = self.pkg_root / d\n"
            p.mkdir(parents=True, exist_ok=True)\n\n"
    def generate(self, template_name='report_zeta', s_arg='0.5+14.134725i'):\n"
        tpl = TEMPLATES.get(template_name)\n"
        if tpl is None:\n"
            raise ValueError('unknown template: ' + template_name)\n"
        self._ensure_dirs()\n\n"
        # write config\n"
        etcp = self.pkg_root / 'etc' / 'omega'\n"
        etcp.mkdir(parents=True, exist_ok=True)\n"
        (etcp / 'config.json').write_text(json.dumps({'template': template_name, 's_arg': s_arg}, indent=2), encoding='utf-8')\n\n"
        s = parse_complex(s_arg)\n"
        zval = zeta_value(s)\n"
        gval = gamma_value(s)\n"
        xi_pair = functional_equation_xi(s)\n\n"
        module_src = []\n"
        module_src.append(tpl['comment'])\n"
        module_src.append(tpl['header'].format(S=s_arg))\n"
        for fn in tpl['functions']:\n"
            module_src.append('  def {}({}) {{\\n'.format(fn['name'], ','.join(fn.get('args',[]))))\n"
            for line in fn['body']:\n"
                line_out = line.replace('{S}', str(s_arg)).replace('{ZETA_S}', str(zval)).replace('{GAMMA_S}', str(gval))\n"
                if '{XI_S}' in line_out:\n"
                    line_out = line_out.replace('{XI_S}', str(xi_pair[0])).replace('{XI_1MS}', str(xi_pair[1]))\n"
                module_src.append('    ' + line_out + '\\n')\n"
            module_src.append('  }\\n\\n')\n"
        module_src.append(tpl['footer'])\n\n"
        libdir = self.pkg_root / 'lib'\n"
        modpath = libdir / (self.package_name + '.omega')\n"
        modpath.write_text(''.join(module_src), encoding='utf-8')\n\n"
        bindir = self.pkg_root / 'bin'\n"
        runner = f\"\"\"#!/usr/bin/env python3\n\"\"\"\n"
        runner += \"# runner: print computed zeta/gamma values (from report-guided generator)\\n\"\n"
        runner += \"from lib.omega.zeta_utils import parse_complex, zeta_value, gamma_value\\n\"\n"
        runner += f\"s = parse_complex('{s_arg}')\\n\"\n"
        runner += \"print('s =', s)\\nprint('zeta(s) =', zeta_value(s))\\nprint('Gamma(s) =', gamma_value(s))\\n\"\n"
        (bindir / 'show_values.py').write_text(runner, encoding='utf-8')\n"
        os.chmod((bindir / 'show_values.py').as_posix(), 0o755)\n\n"
        utildir = self.pkg_root / 'lib' / 'omega'\n"
        utildir.mkdir(parents=True, exist_ok=True)\n        (utildir / '__init__.py').write_text('# omega helpers\\n', encoding='utf-8')\n\n"
        incdir = self.pkg_root / 'include'\n"
        (incdir / 'omega_api.h.omega').write_text('# Omega API header (report-guided)\\n', encoding='utf-8')\n\n"
        sbindir = self.pkg_root / 'sbin'\n"
        (sbindir / 'check_deps.sh').write_text('#!/usr/bin/env bash\\necho \"Checking Python deps...\"\\n', encoding='utf-8')\n"
        os.chmod((sbindir / 'check_deps.sh').as_posix(), 0o755)\n\n"
        docdir = self.pkg_root / 'usr' / 'share' / 'doc' / 'omega'\n"
        docdir.mkdir(parents=True, exist_ok=True)\n"
        (docdir / 'README').write_text('Omega generator package (report-guided). See bin/omega_gen.py\\n', encoding='utf-8')\n\n"
        (self.pkg_root / 'README_generated.txt').write_text(f'Package: {self.package_name}\\nTemplate: {template_name}\\ns: {s_arg}\\n', encoding='utf-8')\n"
        return True\n";

static const char *lib_zeta_utils =
# zeta_utils.py\n"
# Minimal zeta/gamma utilities using sympy and mpmath fallback.\n"
from sympy import symbols, zeta as sym_zeta, gamma as sym_gamma, I as symI, N as symN\n"
import mpmath as mp\n"
import re\n\n"
def parse_complex(s):\n"
    s = s.strip().replace(' ', '')\n"
    if s.endswith('i'):\n"
        s2 = s[:-1]\n"
        m = re.match(r'^([+-]?\\d*\\.?\\d+)([+-]\\d*\\.?\\d+)$', s2)\n"
        if m:\n"
            return complex(float(m.group(1)), float(m.group(2)))\n"
        return complex(0.0, float(s2))\n"
    else:\n"
        return complex(float(s), 0.0)\n\n"
def zeta_value(s):\n"
    try:\n"
        from sympy import I as symI\n"
        if isinstance(s, complex):\n"
            sx = s.real + s.imag*symI\n"
            return complex(symN(sym_zeta(sx), 50))\n"
        else:\n"
            return sym_zeta(s)\n"
    except Exception:\n"
        mp.mp.dps = 50\n"
        return mp.zeta(s)\n\n"
def gamma_value(s):\n"
    try:\n"
        from sympy import I as symI\n"
        if isinstance(s, complex):\n"
            sx = s.real + s.imag*symI\n"
            return complex(symN(sym_gamma(sx),50))\n"
        else:\n"
            return sym_gamma(s)\n"
    except Exception:\n"
        mp.mp.dps = 50\n"
        return mp.gamma(s)\n\n"
def functional_equation_xi(s):\n"
    try:\n"
        from sympy import I as symI, pi\n"
        if isinstance(s, complex):\n"
            sx = s.real + s.imag*symI\n"
            xi = sym_gamma(sx/2)*(pi**(-sx/2))*sym_zeta(sx)\n"
            sm = 1 - sx\n"
            xi_m = sym_gamma(sm/2)*(pi**(-sm/2))*sym_zeta(sm)\n"
            return (complex(symN(xi,40)), complex(symN(xi_m,40)))\n"
        else:\n"
            xi = sym_gamma(s/2)*(pi**(-s/2))*sym_zeta(s)\n"
            sm = 1 - s\n"
            xi_m = sym_gamma(sm/2)*(pi**(-sm/2))*sym_zeta(sm)\n"
            return (xi, xi_m)\n"
    except Exception:\n"
        mp.mp.dps = 50\n"
        if isinstance(s, complex):\n"
            xi = mp.gamma(s/2)*(mp.pi**(-s/2))*mp.zeta(s)\n"
            sm = 1 - s\n"
            xi_m = mp.gamma(sm/2)*(mp.pi**(-sm/2))*mp.zeta(sm)\n"
            return (xi, xi_m)\n"
        return (None, None)\n";

static const char *lib_templates =
# templates.py\n"
# Template capturing key equations and snippets inspired by the report.\n"
TEMPLATES = {\n"
    'report_zeta': {\n"
        'comment': '# Omega Script generated from report: zeta/gamma functional-equation snippets\\n',\n"
        'header': \"module ReportZeta {{\\n  const SEED_S = '{S}'\\n\",\n"
        'footer': '}\\n',\n"
        'functions': [\n"
            {\n"
                'name': 'zeta_eval',\n"
                'args': ['s'],\n"
                'body': [\n"
                    '# compute zeta(s) (numeric/symbolic)',\n"
                    \"val := zeta(s)  # inserted numeric from generator: {ZETA_S}\",\n"
                    \"puts \\\"zeta({s}) => {ZETA_S}\\\"\",\n"
                    'return val'\n"
                ]\n"
            },\n"
            {\n"
                'name': 'gamma_and_functional_demo',\n"
                'args': ['s'],\n"
                'body': [\n"
                    '# demonstrate Gamma(s) and Xi(s) functional-equation style relation',\n"
                    \"G := Gamma(s)  # generator filled: {GAMMA_S}\",\n"
                    'Xi_s := Gamma(s/2) * pi**(-s/2) * zeta(s)  # Xi(s)',\n"
                    'Xi_1ms := Gamma((1-s)/2) * pi**(-(1-s)/2) * zeta(1-s)  # Xi(1-s)',\n"
                    \"puts \\\"Gamma(s)={GAMMA_S}; Xi(s)={XI_S}; Xi(1-s)={XI_1MS}\\\"\",\n"
                    'return {G, Xi_s, Xi_1ms}'\n"
                ]\n"
            },\n"
            {\n"
                'name': 'report_notes',\n"
                'args': [],\n"
                'body': [\n"
                    '# This function carries extracted formula comments from the report:',\n"
                    \"# - Euler product, Gamma integral: Γ(s)=∫_0^∞ e^{-x} x^{s-1} dx\",\n"
                    '# - Functional equation idea: Xi(s)=Xi(1-s)',\n"
                    '# - Zeros near critical line Re(s)=1/2 (report examples like 0.5+14.134725i)',\n"
                    'puts \"Report snippets embedded.\"',\n"
                    'return true'\n"
                ]\n"
            }\n"
        ]\n"
    }\n"
}\n";

static const char *include_hdr =
# Omega API header (report-guided)\n"
# Provided functions in generated module ReportZeta:\n"
#   zeta_eval(s)\n"
#   gamma_and_functional_demo(s)\n"
#   report_notes()\n"
# Constants:\n"
#   SEED_S\n";

static const char *etc_config =
[report]\n"
# seed argument for zeta evaluation (from report examples)\n"
s_arg = 0.5+14.134725i\n";

static const char *sbin_check =
#!/usr/bin/env bash\n"
echo \"Checking Python dependencies (sympy, mpmath)...\"\n"
python3 - <<'PY'\n"
try:\n"
    import sympy, mpmath\n"
    print('sympy and mpmath OK')\n"
except Exception as e:\n"
    print('Missing deps:', e)\n"
PY\n";

static const char *usr_readme =
Omega generator (report-guided)\n"
- Run: bin/omega_gen.py\n"
- Requires: python3, sympy/mpmath for numeric/symbolic evaluation\n";

int main(int argc, char **argv) {
    const char *prefix = argc > 1 ? argv[1] : "/usr/local/omega_pkg";
    char path[4096];

    /* create dirs */
    const char *dirs[] = {
        "/bin",
        "/lib",
        "/lib/omega",
        "/include",
        "/etc/omega",
        "/sbin",
        "/usr/share/doc/omega",
        NULL
    };
    for (const char **d = dirs; *d; ++d) {
        snprintf(path, sizeof(path), "%s%s", prefix, *d);
        mkdir_p(path);
    }

    /* write files */
    snprintf(path, sizeof(path), "%s/bin/omega_gen.py", prefix);
    write_file_mode(path, bin_omega_gen, 0755);

    snprintf(path, sizeof(path), "%s/lib/omega/generator.py", prefix);
    write_file_mode(path, lib_generator, 0644);

    snprintf(path, sizeof(path), "%s/lib/omega/zeta_utils.py", prefix);
    write_file_mode(path, lib_zeta_utils, 0644);

    snprintf(path, sizeof(path), "%s/lib/omega/templates.py", prefix);
    write_file_mode(path, lib_templates, 0644);

    snprintf(path, sizeof(path), "%s/include/omega_api.h.omega", prefix);
    write_file_mode(path, include_hdr, 0644);

    snprintf(path, sizeof(path), "%s/etc/omega/config.ini", prefix);
    write_file_mode(path, etc_config, 0644);

    snprintf(path, sizeof(path), "%s/sbin/check_deps.sh", prefix);
    write_file_mode(path, sbin_check, 0755);

    snprintf(path, sizeof(path), "%s/usr/share/doc/omega/README", prefix);
    write_file_mode(path, usr_readme, 0644);

    printf("Package installed under: %s\n", prefix);
    return 0;
}
```

ファイル: Makefile
```makefile
CC = gcc
CFLAGS = -O2 -Wall
TARGET = pkginstallgen
PREFIX ?= /usr/local/omega_pkg

all: $(TARGET)

$(TARGET): pkginstallgen.c
$(CC) $(CFLAGS) -o $(TARGET) pkginstallgen.c

install: $(TARGET)
@echo "Installing package files to $(PREFIX) (may require root privileges)"
@mkdir -p $(PREFIX)
@./$(TARGET) $(PREFIX)
@echo "Install complete."

uninstall:
@echo "Uninstall not implemented: manually remove $(PREFIX)"

clean:
@rm -f $(TARGET)
```

必要に応じて
- 生成するファイルの内容を変更したければ、`pkginstallgen.c` 内の文字列を編集してください。
- 生成後、`PREFIX/bin/omega_gen.py` を実行してパッケージ生成フローを利用してください（実行には Python3 と sympy/mpmath を推奨）。

以上。

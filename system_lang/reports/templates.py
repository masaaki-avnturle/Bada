package.templates
/*
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
*/



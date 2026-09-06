/* reviser_tool.c - applies @reviser textual rules (simple) to an external BNF file */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_RULES 256
struct rule { char lhs[512]; char rhs[512]; };

static int load_rules(const char *omega_bnf, struct rule *rules){
    FILE *f = fopen(omega_bnf, "r"); if(!f) return 0;
    char line[1024]; int n=0; int in_reviser=0;
    while(fgets(line,sizeof(line),f)){
        if(!in_reviser){ if(strstr(line, "@reviser")) { in_reviser=1; continue; } }
        else {
            if(line[0]=='\n' || line[0]=='#' || line[0]==0) break;
            char *arrow = strstr(line, "=>"); if(!arrow) continue;
            *arrow = '\0'; arrow += 2;
            char *a=line; while(*a==' '||*a=='\t') a++;
            char *ae = a + strlen(a)-1; while(ae>a && (*ae=='\n'||*ae=='\r'||*ae==' '||*ae=='\t')) *ae--='\0';
            char *b = arrow; while(*b==' '||*b=='\t') b++;
            char *be = b + strlen(b)-1; while(be>b && (*be=='\n'||*be=='\r'||*be==' '||*be=='\t')) *be--='\0';
            if(n<MAX_RULES){ strncpy(rules[n].lhs, a, sizeof(rules[n].lhs)-1); strncpy(rules[n].rhs, b, sizeof(rules[n].rhs)-1); n++; }
        }
    }
    fclose(f); return n;
}

static void apply_rules(const char *infile, struct rule *rules, int rcnt){
    FILE *f = fopen(infile, "r"); if(!f){ perror(infile); return; }
    char buf[8192];
    while(fgets(buf, sizeof(buf), f)){
        char out[16384]; out[0]=0; strncpy(out, buf, sizeof(out)-1);
        for(int i=0;i<rcnt;i++){
            char *p = strstr(out, rules[i].lhs);
            if(!p) continue;
            char tmp[16384]; tmp[0]=0;
            size_t pre = (size_t)(p - out);
            if(pre) strncat(tmp, out, pre);
            strncat(tmp, rules[i].rhs, sizeof(tmp)-strlen(tmp)-1);
            strncat(tmp, p + strlen(rules[i].lhs), sizeof(tmp)-strlen(tmp)-1);
            strncpy(out, tmp, sizeof(out)-1);
        }
        fputs(out, stdout);
    }
    fclose(f);
}

int main(int argc, char **argv){
    if(argc<2){ fprintf(stderr, "Usage: %s <external.bnf>\n", argv[0]); return 1; }
    struct rule rules[MAX_RULES]; memset(rules, 0, sizeof(rules));
    int rc = load_rules("omega_script.bnf", rules);
    if(rc<=0) fprintf(stderr, "No reviser rules found in omega_script.bnf; emitting original file.\n");
    apply_rules(argv[1], rules, rc);
    return 0;
}


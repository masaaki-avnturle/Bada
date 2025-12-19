/* bnf_loader.c -- loads bnfs/ files and prints summary (stub for integrating BNFs) */
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>

int main(int argc, char **argv){
    const char *dir = "bnfs";
    DIR *d = opendir(dir); if(!d){ perror("opendir"); return 1; }
    struct dirent *ent; int count = 0;
    while((ent = readdir(d))){
        if(ent->d_name[0]=='.') continue;
        printf("bnf: %s/%s\n", dir, ent->d_name); count++;
    }
    closedir(d);
    printf("Total BNFs available: %d\n", count);
    printf("To feed a BNF into Omega (stub): ./compiler <some.omega>\n");
    return 0;
}

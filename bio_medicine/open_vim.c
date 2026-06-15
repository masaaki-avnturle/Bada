#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <string.h>

int main(int argc, char *argv[]) {
  if (argc != 3) {
    fprintf(stderr, "Usage: %s <target_dir> <filename>\n", argv[0]);
    return 1;
  }

  const char *target_dir = argv[1];
  const char *filename = argv[2];

  pid_t pid = fork();
  if (pid < 0) {
    perror("fork");
    return 1;
  }

  if (pid == 0) {
    /* child: change to target directory and exec bash -c "cd ... && exec vim file" */
    if (chdir(target_dir) != 0) {
      fprintf(stderr, "chdir(%s) failed: %s\n", target_dir, strerror(errno));
      _exit(2);
    }

    /* Use execvp to replace child with bash running vim in the same terminal.
       The "exec vim" ensures the shell is replaced by vim (so exiting vim exits child). */
    execlp("bash", "bash", "-c", "exec vim \"$1\"", "bash", filename, (char *)NULL);

        /* If exec fails */
        fprintf(stderr, "execlp failed: %s\n", strerror(errno));
        _exit(3);
    } else {
        /* parent: wait for child (vim) to exit */
        int status;
        if (waitpid(pid, &status, 0) < 0) {
            perror("waitpid");
            return 1;
        }
        if (WIFEXITED(status)) {
            return WEXITSTATUS(status);
        } else if (WIFSIGNALED(status)) {
            fprintf(stderr, "Child terminated by signal %d\n", WTERMSIG(status));
            return 128 + WTERMSIG(status);
        }
    }
    return 0;
}

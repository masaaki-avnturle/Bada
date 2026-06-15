#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <string.h>

int main(int argc, char *argv[]) {
  if (argc != 4) {
    fprintf(stderr, "Usage: %s <target_dir> <viewer_app> <pdf_file>\n", argv[0]);
    return 1;
  }

  const char *target_dir = argv[1];
  const char *viewer = argv[2];
  const char *pdf = argv[3];

  pid_t pid = fork();
  if (pid < 0) {
    perror("fork");
    return 1;
  }

  if (pid == 0) {
    /* child: change directory, then exec bash which runs the viewer */
    if (chdir(target_dir) != 0) {
      fprintf(stderr, "chdir(%s) failed: %s\n", target_dir, strerror(errno));
      _exit(2);
    }

    /* Use bash -c with positional parameters to safely pass app and file */
    execlp("bash", "bash", "-c", "exec \"$1\" \"$2\"", "bash", viewer, pdf, (char *)NULL);

    /* if exec fails */
    fprintf(stderr, "execlp failed: %s\n", strerror(errno));
    _exit(3);
  } else {
    int status;
    if (waitpid(pid, &status, 0) < 0) {
      perror("waitpid");
      return 1;
    }
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
  }
  return 0;
}

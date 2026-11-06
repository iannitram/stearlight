/* Locked test: stearlight_fd_has_shrink_seal() reads the seal set of an fd. */
#define _GNU_SOURCE
#include "../packages/stearlight-runtime/memfd_seals.h"
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>

static int failures;
#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "FAILED line %d: %s\n", __LINE__, #condition); failures++; } } while (0)

static int sealable(void) {
  int fd = memfd_create("seal-test", MFD_CLOEXEC | MFD_ALLOW_SEALING);
  if (fd < 0 || ftruncate(fd, 16)) { perror("memfd_create"); exit(2); }
  return fd;
}

int main(void) {
  int fd = sealable();
  CHECK(stearlight_fd_has_shrink_seal(fd) == 0);               /* unsealed */
  CHECK(fcntl(fd, F_ADD_SEALS, F_SEAL_GROW) == 0);
  CHECK(stearlight_fd_has_shrink_seal(fd) == 0);               /* grow only */
  CHECK(fcntl(fd, F_ADD_SEALS, F_SEAL_SHRINK) == 0);
  CHECK(stearlight_fd_has_shrink_seal(fd) == 1);               /* shrink added */
  close(fd);

  fd = sealable();
  CHECK(fcntl(fd, F_ADD_SEALS, F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_SEAL) == 0);
  CHECK(stearlight_fd_has_shrink_seal(fd) == 1);               /* the exporter's seal set */
  close(fd);

  fd = memfd_create("no-sealing", MFD_CLOEXEC);                /* sealing not allowed: F_SEAL_SEAL only */
  CHECK(fd >= 0 && ftruncate(fd, 16) == 0 && stearlight_fd_has_shrink_seal(fd) == 0);
  close(fd);

  int pipefd[2];
  CHECK(pipe(pipefd) == 0);
  CHECK(stearlight_fd_has_shrink_seal(pipefd[0]) == 0);        /* an fd that holds no seals */
  close(pipefd[0]); close(pipefd[1]);
  CHECK(stearlight_fd_has_shrink_seal(-1) == 0);               /* an invalid fd */

  if (failures) return 1;
  puts("memfd seals: unsealed, grow-only, shrink, exporter set, other fds passed");
  return 0;
}

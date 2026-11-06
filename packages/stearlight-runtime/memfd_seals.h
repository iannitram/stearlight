#pragma once
#include <fcntl.h>

/* Needs _GNU_SOURCE defined before the first system include (the shim and the
   test already do). */
static inline int stearlight_fd_has_shrink_seal(int fd) {
  const int seals = fcntl(fd, F_GET_SEALS);
  return seals >= 0 && (seals & F_SEAL_SHRINK);
}

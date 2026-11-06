#pragma once

#include <stddef.h>

/* Copy an app-supplied name for logging, replacing control bytes with '?'.
 * Bytes from 0x20 to 0x7e and bytes above 0x7f are copied unchanged. At most
 * size - 1 bytes are copied, and the output is always NUL-terminated when
 * size > 0. Returns the number of bytes copied, not counting the NUL. */
static inline size_t stearlight_log_text(char *out, size_t size, const char *name) {
  size_t copied = 0;
  if (size > 0 && name != NULL) {
    while (copied + 1 < size && name[copied] != '\0') {
      unsigned char byte = (unsigned char)name[copied];
      out[copied] = (byte < 0x20 || byte == 0x7f) ? '?' : (char)byte;
      copied++;
    }
  }
  if (size > 0) out[copied] = '\0';
  return copied;
}

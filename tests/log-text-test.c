/* Locked test: stearlight_log_text() makes an app-supplied name safe to log. */
#include "../packages/stearlight-runtime/log_text.h"
#include <stdio.h>
#include <string.h>

static int failures;
#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "FAILED line %d: %s\n", __LINE__, #condition); failures++; } } while (0)

int main(void) {
  char out[64];
  const char *plain = "vkGetPhysicalDeviceDisplayPropertiesKHR";
  CHECK(stearlight_log_text(out, sizeof out, plain) == strlen(plain) && !strcmp(out, plain));

  CHECK(stearlight_log_text(out, sizeof out, "a\nb") == 3 && !strcmp(out, "a?b"));            /* newline */
  CHECK(stearlight_log_text(out, sizeof out, "x\x1b[2Jy") == 6 && !strcmp(out, "x?[2Jy"));    /* escape */
  CHECK(!strcmp((stearlight_log_text(out, sizeof out, "\r\t\x01\x1f\x7f"), out), "?????"));   /* 0x00-0x1f and 0x7f */
  CHECK(!strcmp((stearlight_log_text(out, sizeof out, "a b~"), out), "a b~"));                /* 0x20 and 0x7e stay */
  CHECK(!strcmp((stearlight_log_text(out, sizeof out, "caf\xc3\xa9"), out), "caf\xc3\xa9"));  /* bytes above 0x7f stay */

  char small[8];
  CHECK(stearlight_log_text(small, sizeof small, "abcdefghij") == 7 && !strcmp(small, "abcdefg"));
  CHECK(stearlight_log_text(small, sizeof small, "abcdefg") == 7 && !strcmp(small, "abcdefg"));
  CHECK(stearlight_log_text(small, sizeof small, "ab\ncdefghij") == 7 && !strcmp(small, "ab?cdef"));

  char one[1] = {'z'};
  CHECK(stearlight_log_text(one, sizeof one, "abc") == 0 && one[0] == '\0');
  char none[2] = {'q', 'q'};
  CHECK(stearlight_log_text(none, 0, "abc") == 0 && none[0] == 'q' && none[1] == 'q');
  CHECK(stearlight_log_text(out, sizeof out, NULL) == 0 && out[0] == '\0');

  char input[] = "keep\nme";
  stearlight_log_text(out, sizeof out, input);
  CHECK(!strcmp(input, "keep\nme"));                                                           /* input untouched */

  /* The shim formats "gipa %s" into a 160-byte message from a 128-byte buffer. */
  char name[300], clean[128], message[160];
  memset(name, 'n', sizeof name - 1); name[100] = '\n'; name[sizeof name - 1] = '\0';
  stearlight_log_text(clean, sizeof clean, name);
  snprintf(message, sizeof message, "gipa %s", clean);
  CHECK(strlen(message) == 5 + 127 && !strchr(message, '\n') && message[5 + 100] == '?');

  if (failures) return 1;
  puts("log text: control bytes replaced, limit kept passed");
  return 0;
}

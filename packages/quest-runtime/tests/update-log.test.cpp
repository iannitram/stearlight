// Locked test: openUpdateLog() creates the update log fresh and never follows a link.
#include "../linux/update-log.h"
#include <cerrno>
#include <fcntl.h>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

static int failures = 0;
#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "FAILED line %d: %s\n", __LINE__, #condition); ++failures; } } while (0)

static std::string readAll(const std::string& path) {
 std::string text; char buffer[64]; size_t count;
 FILE* file = fopen(path.c_str(), "rb");
 if (!file) return "<missing>";
 while ((count = fread(buffer, 1, sizeof buffer, file)) > 0) text.append(buffer, count);
 fclose(file);
 return text;
}
static void put(const std::string& path, const char* text) {
 FILE* file = fopen(path.c_str(), "wb"); fputs(text, file); fclose(file);
}

int main() {
 char pattern[] = "/tmp/update-log-test-XXXXXX";
 std::string dir = mkdtemp(pattern), log = dir + "/updater.log", victim = dir + "/victim.txt";
 struct stat status;

 // A fresh path: a new private read-write file that is not inherited across exec.
 int fd = openUpdateLog(log.c_str());
 CHECK(fd >= 0);
 CHECK(fstat(fd, &status) == 0 && S_ISREG(status.st_mode) && (status.st_mode & 0777) == 0600 && status.st_size == 0);
 CHECK(fcntl(fd, F_GETFD) & FD_CLOEXEC);
 CHECK(write(fd, "one", 3) == 3 && lseek(fd, 0, SEEK_SET) == 0);
 char back[4] = {0}; CHECK(read(fd, back, 3) == 3 && std::string(back) == "one");
 close(fd);

 // An old log is replaced by an empty file.
 put(log, "old log text");
 fd = openUpdateLog(log.c_str());
 CHECK(fd >= 0 && fstat(fd, &status) == 0 && status.st_size == 0);
 close(fd);
 CHECK(readAll(log).empty());

 // A symlink to a file is replaced by a regular file; the file behind it is untouched.
 put(victim, "keep me"); unlink(log.c_str()); CHECK(symlink(victim.c_str(), log.c_str()) == 0);
 fd = openUpdateLog(log.c_str());
 CHECK(fd >= 0 && write(fd, "log", 3) == 3);
 close(fd);
 CHECK(readAll(victim) == "keep me");
 CHECK(lstat(log.c_str(), &status) == 0 && S_ISREG(status.st_mode));

 // A dangling symlink must not make the open create the file it points to.
 std::string target = dir + "/created-through-link.txt";
 unlink(log.c_str()); CHECK(symlink(target.c_str(), log.c_str()) == 0);
 fd = openUpdateLog(log.c_str());
 if (fd >= 0) close(fd);
 CHECK(stat(target.c_str(), &status) != 0 && errno == ENOENT);

 // When the path cannot be replaced, the caller gets -1 and keeps running without a log.
 unlink(log.c_str()); CHECK(mkdir(log.c_str(), 0700) == 0);
 CHECK(openUpdateLog(log.c_str()) == -1);
 CHECK(openUpdateLog((dir + "/missing-folder/updater.log").c_str()) == -1);

 if (failures) return 1;
 puts("update log: fresh file, replaced link, no follow, failure passed");
 return 0;
}

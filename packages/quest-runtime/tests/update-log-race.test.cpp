// Race check: a link that appears at the log path between the unlink and the open must be refused, never followed.
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

static int failures = 0;
#define CHECK(condition) do { if (!(condition)) { fprintf(stderr, "FAILED line %d: %s\n", __LINE__, #condition); ++failures; } } while (0)

// Stands in for unlink() inside openUpdateLog(): after the real unlink, a link to gRaceTarget appears at the path.
static std::string gRaceTarget;
static int race_unlink(const char* path) {
 int result = unlink(path);
 if (!gRaceTarget.empty()) symlink(gRaceTarget.c_str(), path);
 return result;
}
#define unlink(path) race_unlink(path)
#include "../linux/update-log.h"
#undef unlink

static std::string readAll(const std::string& path) {
 std::string text; char buffer[64]; size_t count;
 FILE* file = fopen(path.c_str(), "rb");
 if (!file) return "<missing>";
 while ((count = fread(buffer, 1, sizeof buffer, file)) > 0) text.append(buffer, count);
 fclose(file);
 return text;
}

int main() {
 char pattern[] = "/tmp/update-log-race-XXXXXX";
 std::string dir = mkdtemp(pattern), log = dir + "/updater.log", victim = dir + "/victim.txt", target = dir + "/created-through-link.txt";
 struct stat status;

 FILE* file = fopen(victim.c_str(), "wb"); fputs("keep me", file); fclose(file);

 // A link to an existing file appears at the path: the open must refuse it and leave the file alone.
 gRaceTarget = victim;
 CHECK(openUpdateLog(log.c_str()) == -1);
 CHECK(readAll(victim) == "keep me");

 // A link to a missing file appears at the path: the open must not create the file it points to.
 gRaceTarget = target;
 CHECK(openUpdateLog(log.c_str()) == -1);
 CHECK(stat(target.c_str(), &status) != 0 && errno == ENOENT);

 gRaceTarget.clear();
 std::remove(log.c_str()); std::remove(victim.c_str());
 rmdir(dir.c_str());

 if (failures) return 1;
 puts("update log race: link at the path refused, not followed");
 return 0;
}

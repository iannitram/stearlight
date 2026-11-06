// The update UI writes its log as a fresh private file; a link at the path is replaced, never followed.
#pragma once

#include <fcntl.h>
#include <unistd.h>

inline int openUpdateLog(const char* path){
 unlink(path);
 return open(path, O_RDWR | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
}

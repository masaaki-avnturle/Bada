"""A small in-memory virtual filesystem for the BadaWebOS terminal.

Every terminal app (the bash shell, vim, emacs) reads and writes through this
VFS rather than the host disk, so the whole terminal is sandbox-safe and fully
scriptable/testable.  Paths are POSIX; directories are tracked explicitly.
"""

from __future__ import annotations

import posixpath


class VFSError(Exception):
    pass


class VFS:
    def __init__(self, home: str = "/home/bada"):
        self.files: dict[str, str] = {}
        self.dirs: set[str] = {"/"}
        self.cwd = "/"
        self._mkdirs(home)
        self.cwd = home
        # a couple of starter files
        self.write(posixpath.join(home, "welcome.txt"),
                   "welcome to BadaWebOS terminal\n")

    # -- path helpers ------------------------------------------------------
    def resolve(self, path: str) -> str:
        if not path:
            return self.cwd
        if not path.startswith("/"):
            path = posixpath.join(self.cwd, path)
        return posixpath.normpath(path)

    def _parent(self, path: str) -> str:
        return posixpath.dirname(path.rstrip("/")) or "/"

    def _mkdirs(self, path: str):
        path = self.resolve(path)
        parts = path.strip("/").split("/")
        cur = ""
        for p in parts:
            cur = cur + "/" + p
            self.dirs.add(cur)

    # -- predicates --------------------------------------------------------
    def is_dir(self, path: str) -> bool:
        return self.resolve(path) in self.dirs

    def is_file(self, path: str) -> bool:
        return self.resolve(path) in self.files

    def exists(self, path: str) -> bool:
        return self.is_dir(path) or self.is_file(path)

    # -- operations --------------------------------------------------------
    def mkdir(self, path: str):
        self._mkdirs(path)

    def chdir(self, path: str):
        target = self.resolve(path)
        if target not in self.dirs:
            raise VFSError(f"cd: {path}: No such directory")
        self.cwd = target

    def write(self, path: str, content: str):
        path = self.resolve(path)
        parent = self._parent(path)
        if parent not in self.dirs:
            self._mkdirs(parent)
        self.files[path] = content

    def read(self, path: str) -> str:
        path = self.resolve(path)
        if path not in self.files:
            raise VFSError(f"{path}: No such file")
        return self.files[path]

    def remove(self, path: str):
        path = self.resolve(path)
        if path in self.files:
            del self.files[path]
        elif path in self.dirs:
            if any(p.startswith(path + "/") for p in self.files | self.dirs):
                raise VFSError(f"rm: {path}: directory not empty")
            self.dirs.discard(path)
        else:
            raise VFSError(f"rm: {path}: No such file or directory")

    def listdir(self, path: str | None = None) -> list[str]:
        d = self.resolve(path or self.cwd)
        if d not in self.dirs:
            raise VFSError(f"ls: {path}: No such directory")
        names = set()
        for f in self.files:
            if self._parent(f) == d:
                names.add(posixpath.basename(f))
        for sub in self.dirs:
            if sub != d and self._parent(sub) == d:
                names.add(posixpath.basename(sub) + "/")
        return sorted(names)

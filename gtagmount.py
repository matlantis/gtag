import pdb
import time
import threading
import argparse
import unittest
import fuse
import os
from os.path import basename, dirname, join

GTAG_MOUNT_ROOT = os.path.join(os.getenv("HOME"), "gtag3")
GTAG_STAGING_DIR = join(os.getenv("HOME"), ".gtag", "stage")

def make_unique_name(name, onames):
    # assume that all names have same basenames
    # remove the name itself from onames (even if it appears more than once)
    while name in onames:
        del onames[onames.index(name)]

    outname = basename(name)
    while basename(name) in (basename(f) for f in onames):
        onames = (dirname(f) for f in onames)
        name = dirname(name)

    if name == "/":
        # keep the slash
        bname = name
    else:
        bname = basename(name)
    # now the basename is unique
    outname = "[{}]{}".format(bname, outname)
    return outname

class MakeUniqueNameTester(unittest.TestCase):
    def test_it(self):
        self.assertEqual(make_unique_name("/alpha/file.txt", ["/alpha/file.txt", "/beta/file.txt"]), "[alpha]file.txt")
        self.assertEqual(make_unique_name("/file.txt", ["/alpha/file.txt", "/beta/file.txt"]), "[/]file.txt")
        self.assertEqual(make_unique_name("file.txt", ["/file.txt", "/beta/file.txt"]), "[]file.txt")
        self.assertEqual(make_unique_name("/file.txt", ["file.txt", "/beta/file.txt"]), "[/]file.txt")

def file_mapping(root, files):
    # take the root and the last component of the file
    # and join them together

    # make a list of basenames
    basenames = {}
    for f in files:
        bname = basename(f)
        if not bname in basenames:
            basenames[bname] = []
        basenames[bname].append(f)

    mapping = {}
    for f in files:
        bname = basename(f)
        # check for uniquness
        if len(basenames[bname]) > 1:
            uniquename = make_unique_name(f, basenames[bname])
            mountfile = join(root, uniquename)
        else:
            mountfile = join(root, basename(f))

        mapping[mountfile] = f

    return mapping


class GutenTagMount(fuse.Operations):
    def __init__(self, gt):
        self._gt = gt
        self._gt.openDb()

        self._mounts = []

        os.makedirs(GTAG_STAGING_DIR, exist_ok = True)
        os.makedirs(GTAG_MOUNT_ROOT, exist_ok = True)

        self._lock_mounts = threading.Lock()

    def start(self):
        fuse.FUSE(self, GTAG_MOUNT_ROOT, nothreads=True, foreground=True)

    # Private methods
    # ===============

    def _files(self, tagterm):
        return self._gt.files(tagterm)

    def _true_path(self, path):
        """
        for a file which is listed in mappings, this returns the true path for that file
        for a file or dir that is not listed in mappings, this returns a path in staging dir
        for a tagterm mount this should not be called
        """
        # path always starts with a '/'
        path_split = path.split('/')
        if len(path_split) < 3:
            raise Exception("path has to few components: {}".format(path))

        tagterm = path_split[1]

        if not tagterm in self._mounts:
            raise Exception("unknown mount path: {}".format(path))

        files = self._files(tagterm)
        mapping = file_mapping("/", files)

        # mapping filenames do net contain the tagterm, so remove it
        relpath = path[len(tagterm)+1:]
        if relpath in mapping:
            true_path = mapping[relpath]
        else:
            true_path = join(GTAG_STAGING_DIR, path.lstrip('/'))

        return true_path

    # Public methods
    # ==============

    def add_mount(self, tagterm):
        with self._lock_mounts:
            if tagterm in self._mounts:
                raise Exception("mount already exists: {}".format(tagterm))
            self._mounts.append(tagterm)

    def delete_mount(self, tagterm):
        with self._lock_mounts:
            if not tagterm in self._mounts:
                raise Exception("mount not existent: {}".format(tagterm))
            del self._mounts[self._mounts.index(tagterm)]

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print("access to {}".format(path))

        path_split = path.rstrip('/').split('/')
        if len(path_split) < 2:
            # this is root
            pass
        elif len(path_split) < 3:
            # this is a mount
            tagterm = path_split[1]
            if not tagterm in self._mounts:
                raise Exception("unknown mount path: {}".format(path))
                # TODO idea: mount the tagterm on the fly
        else:
            true_path = self._true_path(path)
            if not os.access(true_path, mode):
                raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        # raises on mount or root
        true_path = self._true_path(path)
        return os.chmod(true_path, mode)

    def chown(self, path, uid, gid):
        # raises on mount or root
        true_path = self._true_path(path)
        return os.chown(true_path, uid, gid)

    def getattr(self, path, fh=None):
        print("getattr {})".format(path))
        path_split = path.rstrip('/').split('/')
        ret = {'st_atime': 0, 'st_ctime': 0, 'st_gid': os.getgid(), 'st_mode': int('0o40700', 8), 'st_mtime': 0, 'st_nlink': 0, 'st_size': 0, 'st_uid': os.getuid()}
        if len(path_split) < 2:
            # this is root
            # TODO maybe remove write permissions here
            return ret

        elif len(path_split) < 3:
            # this is a mount
            # first approach give the stat of the root
            # TODO later change atime, ctime, mtime
            tagterm = path_split[1]
            if not tagterm in self._mounts:
                raise FileNotFoundError("unknown mount path: {}".format(path))
                # TODO idea: mount the tagterm on the fly
            return ret
        else:
            true_path = self._true_path(path)

            st = os.lstat(true_path)
            print("getattr {} ({})".format(path, true_path))
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        print("readdir {}".format(path))
        path_split = path.rstrip('/').split('/')
        dirents = ['.', '..']
        if len(path_split) < 2:
            # this is root
            dirents.extend(self._mounts)

        elif len(path_split) < 3:
            # this is a mount
            tagterm = path_split[1]
            if not tagterm in self._mounts:
                raise Exception("unknown mount path: {}".format(path))

            mapping = file_mapping("/", self._files(tagterm))
            for f in mapping:
                print("f = {}".format(f))
                file_split = f.rstrip('/').split('/')
                dirents.append(file_split[1])

            # make unique
            dirents = list(set(dirents))

        else:
            true_path = self._true_path(path)
            if os.path.isdir(true_path):
                dirents.extend(os.listdir(true_path))

        for r in dirents:
            yield r

    # def readlink(self, path):
    #     pathname = os.readlink(self._true_path(path))
    #     if pathname.startswith("/"):
    #         # Path name is absolute, sanitize it.
    #         return os.path.relpath(pathname, self.root)
    #     else:
    #         return pathname

    # def mknod(self, path, mode, dev):
    #     return os.mknod(self._true_path(path), mode, dev)

    # def rmdir(self, path):
    #     true_path = self._true_path(path)
    #     return os.rmdir(true_path)

    # def mkdir(self, path, mode):
    #     return os.mkdir(self._true_path(path), mode)

    # def statfs(self, path):
    #     print("statfs {}".format(path))
    #     true_path = self._true_path(path)
    #     stv = os.statvfs(true_path)
    #     return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
    #         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
    #         'f_frsize', 'f_namemax'))

    # def unlink(self, path):
    #     return os.unlink(self._true_path(path))

    # def symlink(self, name, target):
    #     return os.symlink(name, self._true_path(target))

    # def rename(self, old, new):
    #     # TODO: not so easy
    #     return os.rename(self._true_path(old), self._true_path(new))

    # def link(self, target, name):
    #     return os.link(self._true_path(target), self._true_path(name))

    # def utimens(self, path, times=None):
    #     return os.utime(self._true_path(path), times)

    # File methods
    # ============

    # def open(self, path, flags):
    #     true_path = self._true_path(path)
    #     return os.open(true_path, flags)

    # def create(self, path, mode, fi=None):
    #     true_path = self._true_path(path)
    #     ret = os.open(true_path, os.O_WRONLY | os.O_CREAT, mode)
    #     self._mapping[path.lstrip("/")] = true_path # TODO: what to do, if the file already exists in stage?
    #     return ret

    # def read(self, path, length, offset, fh):
    #     os.lseek(fh, offset, os.SEEK_SET)
    #     return os.read(fh, length)

    # def write(self, path, buf, offset, fh):
    #     os.lseek(fh, offset, os.SEEK_SET)
    #     return os.write(fh, buf)

    # def truncate(self, path, length, fh=None):
    #     true_path = self._true_path(path)
    #     with open(true_path, 'r+') as f:
    #         f.truncate(length)

    # def flush(self, path, fh):
    #     return os.fsync(fh)

    # def release(self, path, fh):
    #     return os.close(fh)

    # def fsync(self, path, fdatasync, fh):
    #     return self.flush(path, fh)

class DummyDaemon:
    def files(self):
        return ['/a', '/b']

def main():
    dummy_daemon = DummyDaemon()
    operations = GutenTagMount(dummy_daemon)

if __name__ == "__main__":
    main()

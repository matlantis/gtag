import argparse
import unittest
import fuse
import os
from os.path import basename, dirname, join
from gtagd import GutenTagDaemon

GTAG_MOUNT_ROOT = os.path.join(os.getenv("HOME"), "gtag")
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
    # take the root, the tagterm and the last component of the file
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

class GutenTagFuseOperations(fuse.Operations):
    def __init__(self, tagterm):
        gtd = GutenTagDaemon()

        # check if mount location already exists and is not empty
        self._mountpoint = join(GTAG_MOUNT_ROOT, tagterm)
        if os.path.exists(self._mountpoint) and ( not os.path.isdir(self._mountpoint) or not os.listdir(self._mountpoint)) == []:
            raise Exception("Mountpoint already existent")

        files = gtd.files(tagterm)
        self._mapping = file_mapping("", files)

        os.makedirs(GTAG_STAGING_DIR, exist_ok = True)
        os.makedirs(self._mountpoint, exist_ok = True)

    def _true_path(self, partial):
        partial = partial.lstrip("/")
        if partial in self._mapping:
            path = self._mapping[partial]
        else:
            path = join(GTAG_STAGING_DIR, partial)

        return path

    def mountpoint(self):
        return self._mountpoint

    def access(self, path, mode):
        print("access to {}".format(path))
        true_path = self._true_path(path)
        if not os.access(true_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        true_path = self._true_path(path)
        return os.chmod(true_path, mode)

    def chown(self, path, uid, gid):
        true_path = self._true_path(path)
        return os.chown(true_path, uid, gid)

    def getattr(self, path, fh=None):
        true_path = self._true_path(path)
        print("getattr {} ({})".format(path, true_path))
        st = os.lstat(true_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        print("readdir {}".format(path))
        dirents = ['.', '..']
        if path == "/":
            dirents.extend(self._mapping.keys())

        else:
            true_path = self._true_path(path)
            if os.path.isdir(true_path):
                dirents.extend(os.listdir(true_path))

        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._true_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return os.mknod(self._true_path(path), mode, dev)

    def rmdir(self, path):
        true_path = self._true_path(path)
        return os.rmdir(true_path)

    def mkdir(self, path, mode):
        return os.mkdir(self._true_path(path), mode)

    def statfs(self, path):
        print("statfs {}".format(path))
        true_path = self._true_path(path)
        stv = os.statvfs(true_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
            'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
            'f_frsize', 'f_namemax'))

    def unlink(self, path):
        return os.unlink(self._true_path(path))

    def symlink(self, name, target):
        return os.symlink(name, self._true_path(target))

    def rename(self, old, new):
        # TODO: not so easy
        return os.rename(self._true_path(old), self._true_path(new))

    def link(self, target, name):
        return os.link(self._true_path(target), self._true_path(name))

    def utimens(self, path, times=None):
        return os.utime(self._true_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        true_path = self._true_path(path)
        return os.open(true_path, flags)

    def create(self, path, mode, fi=None):
        true_path = self._true_path(path)
        ret = os.open(true_path, os.O_WRONLY | os.O_CREAT, mode)
        self._mapping[path.lstrip("/")] = true_path # TODO: what to do, if the file already exists in stage?
        return ret

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        true_path = self._true_path(path)
        with open(true_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        return os.fsync(fh)

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)

def main():
    parser = argparse.ArgumentParser(description="create a gtag mount")
    parser.add_argument('tagterm', help="the tag term")
    args = parser.parse_args()

    operations = GutenTagFuseOperations(args.tagterm)
    fuse.FUSE(operations, operations.mountpoint(), nothreads=True, foreground=True)

if __name__ == "__main__":
    main()

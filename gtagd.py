#!/usr/bin/env python3

# the gutentag daemon
import pdb
#import sys
import threading
import sqlite3
import os
import sys
import traceback
import parser
import re
import unittest
import signal
from xmlrpc.server import SimpleXMLRPCServer
from gtagmount import GutenTagMount
import gtag_common

SQLITE3_FILE = os.path.join(os.getenv("HOME"), ".gtagdb.sqlite3")

def checkfiles(files):
    """
    check each file for existence, and throw if not
    """
    for f in files:
        if not os.path.isfile(f):
            raise Exception("file does not exist: %s" %(str(f)))

def evalTagterm(tagterm, tags):
    """
    Do the tags match the tagterm?
    """
    # print("---")
    # print("tagterm: '{}'".format(tagterm))

    # replace all tags in tagterm with True
    for t in tags:
        tagterm = tagterm.replace(t, "True")

    tagterm = tagterm.replace('"True"', "True")

    # make a list of all remaining tags in tagterm
    # replace all other tags with False
    quotedusedtags = re.findall('"([^\"]+)"', tagterm)
    for t in quotedusedtags:
        tagterm = tagterm.replace('"{}"'.format(t), "False")

    usedtags = re.findall("([^/(/)\"|&! ]+)", tagterm)
    for t in usedtags:
        if t == "True":
            continue
        tagterm = tagterm.replace(t, "False")

    # check if there are invalid tags
    for t in tags:
        if t == "True" or t == "False":
            raise Exception("Dont use 'True' or 'False' as tags")

    tagterm = tagterm.replace("!", " not ")
    tagterm = tagterm.replace("|", " or ")
    tagterm = tagterm.replace("&", " and ")

    # print("quotedusedtags: {}".format(quotedusedtags))
    # print("usedtags: {}".format(usedtags))
    # print("tags: {}".format(tags))
    # print("eval: '{}'".format(tagterm))

    # hopefully the tagterm is now valid python syntax
    return eval(tagterm)

class EvalTagtermTester(unittest.TestCase):
    def test_tagterms(self):
        self.assertTrue(evalTagterm("mietz", ["mietz", "katz"]))
        self.assertTrue(evalTagterm("mietz&katz", ["mietz", "katz"]))
        self.assertTrue(evalTagterm("mietz|katz", ["mietz", "katz"]))
        self.assertFalse(evalTagterm("mietz", ["katz"]))
        self.assertFalse(evalTagterm("mietz&katz", ["katz"]))
        self.assertTrue(evalTagterm("mietz|katz", ["katz"]))
        self.assertFalse(evalTagterm("!mietz", ["mietz", "katz"]))

        self.assertTrue(evalTagterm("lauf!", ["lauf!"]))
        self.assertTrue(evalTagterm("!lauf!", ["!lauf!"]))

        self.assertFalse(evalTagterm("schau", ["schau mal"]))
        self.assertRaises(SyntaxError, evalTagterm, "schau mal", ["schau"])
        self.assertTrue(evalTagterm('"schau mal"', ["schau mal"]))

def specToTree(spec):
    """
    spec is  a string, e.g. "Music | (Photo & Jara)"
    Creates a Tree with Nodes and Leafs, where a nodes is either a AND node or a OR node, both of which have two children
    """
    # TODO: see the code in ProtectorRuleParser.py:defineRules() to transform the string into the tree
    # TODO: see FeatureTree.py for a treeclass
    pass

class GutenTagDb:
    def __init__(self, dbfile):
        self._parser = parser.Parser()
        self._dbfile = dbfile

    def setMount(self, mount):
        self._mount = mount

    def openDb(self):
        """call it from within the thread to run the xmlrpc server"""
        # open sqlite3 database
        self._dbcxn = sqlite3.connect(self._dbfile)
        # create the table if not exists
        cur = self._dbcxn.cursor()
        # cur.execute("CREATE TABLE IF NOT EXISTS files_tags(id INTEGER PRIMARY KEY, file TEXT, tag TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY, path TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS tags(id INTEGER PRIMARY KEY, label TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS file_tags(id INTEGER PRIMARY KEY, file_id INTEGER, tag_id INTEGER)")
        self._dbcxn.commit()

    def shutdown(self, num, stackframe):
        print("shutting down")
        if hasattr(self, _server):
            self._server.shutdown()

    def delete_mount(self, tagterm):
        if hasattr(self, "_mount"):
            self._mount.delete_mount(tagterm)

            return True

        return False

    def add_mount(self, tagterm):
        if hasattr(self, "_mount"):
            self._mount.add_mount(tagterm)

            return True

        return False

    def add(self, files, tags):
        """
        files: list of files
        tags: list of tags
        adds all the tags to all the specified files (dont care for double entries)
        """
        print("tag %i files with %i tags" % (len(files), len(tags)))
        cur = self._dbcxn.cursor()
        try:
            for f in files:
                for t in tags:
                    # insert tag or retrieve id from existent
                    cur.execute('SELECT id FROM tags WHERE label = ?', [t])
                    res = cur.fetchone()
                    if not res:
                        cur.execute("INSERT OR IGNORE INTO tags(label) VALUES (?)", [t])
                        t_id = cur.lastrowid
                    else:
                        t_id = res[0]

                    # insert file or retrieve id from existent
                    cur.execute('SELECT id FROM files WHERE path = ?', [f])
                    res = cur.fetchone()
                    if not res:
                        cur.execute("INSERT OR IGNORE INTO files(path) VALUES (?)", [f])
                        f_id = cur.lastrowid
                    else:
                        f_id = res[0]

                    cur.execute('INSERT INTO file_tags(file_id, tag_id) VALUES(?, ?)', [f_id, t_id])

            self._dbcxn.commit()

        except:
            if self._dbcxn:
                self._dbcxn.rollback()

            traceback.print_exc()
            raise Exception("Daemon Error")

        return True

    def remove(self, files, tags):
        """
        files: list of files
        tags: list of tags
        removes all the tags from all the specified files (dont care for unknown tags or files).
        if one of the lists is empty, the items in the other one will be completely deleted from db.
        in the other case only the correlation are delete (from file_tags table)
        """
        print("untag %i files with %i tags" % (len(files), len(tags)))
        cur = self._dbcxn.cursor()
        try:
            if f == []:
                for t in tags:
                    # retrieve tag id
                    cur.execute('SELECT id FROM tags WHERE label = ?', [t])
                    res = cur.fetchone()
                    if not res:
                        print("tag not registered {}, ignoring".format(t))
                        continue
                    t_id = res[0]

                    cur.execute("DELETE FROM file_tags WHERE tag_id = ?", [t_id])
                    cur.execute("DELETE FROM tags WHERE id = ?", [t_id])

            for f in files:
                # retrieve file id
                cur.execute('SELECT id FROM files WHERE path = ?', [f])
                res = cur.fetchone()
                if not res:
                    print("file not registered {}, ignoring".format(f))
                    continue
                f_id = res[0]

                if tags == []:
                    cur.execute("DELETE FROM file_tags WHERE file_id = ?", [f_id])
                    cur.execute("DELETE FROM files WHERE id = ?", [f_id])

                for t in tags:
                    # retrieve tag id
                    cur.execute('SELECT id FROM tags WHERE label = ?', [t])
                    res = cur.fetchone()
                    if not res:
                        print("tag not registered {}, ignoring".format(t))
                        continue
                    t_id = res[0]

                    cur.execute("DELETE FROM file_tags WHERE file_id = ? AND tag_id = ?", [f_id, t_id])

            self._dbcxn.commit()

        except:
            if self._dbcxn:
                self._dbcxn.rollback()

            traceback.print_exc()
            raise Exception("Daemon Error")

        return True

    def tags(self, filename):
        cur = self._dbcxn.cursor()
        tags = []
        try:
            if filename == "":
                cur.execute('SELECT label FROM tags')

            else:
                cur.execute('SELECT label FROM tags LEFT JOIN file_tags ON tags.id = file_tags.tag_id LEFT JOIN files ON file_tags.file_id = files.id WHERE path = ?', [filename])

            rows = cur.fetchall()
            for r in rows:
                tags.append(r[0])

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return list(set(tags))

    def files(self, tagterm):
        cur = self._dbcxn.cursor()
        matches = []
        try:
            # get list fo files
            files = []
            cur.execute('SELECT path FROM files')
            rows = cur.fetchall()
            for r in rows:
                files.append(r[0])
            files = set(files)

            if tagterm == "":
                matches = list(files)

            else:
                for f in files:
                    tags = self.tags(f)
                    if evalTagterm(tagterm, tags):
                        matches.append(f)

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return matches

    def pid(self):
        return os.getpid()

class GutenTagServerThread(threading.Thread):
    def __init__(self, gtdb):
        threading.Thread.__init__(self)
        self._gtdb = gtdb

        self._server = SimpleXMLRPCServer(("localhost", gtag_common.RPC_PORT))
        self._server.register_introspection_functions()
        self._server.register_instance(self._gtdb)

    def run(self):
        self._gtdb.openDb()
        self._server.serve_forever()

def main():
    dbfile = SQLITE3_FILE
    # check if there is an db file in the arguments list
    if len(sys.argv) > 1:
        dbfile = sys.argv[1]

    print("Using database file: {}".format(dbfile))

    # need two db connections, cause they run in different threads
    gtdb_mount = GutenTagDb(dbfile)
    gtdb_server = GutenTagDb(dbfile)
    server_thread = GutenTagServerThread(gtdb_server)
    mount = GutenTagMount(gtdb_mount)

    gtdb_server.setMount(mount)

    server_thread.start()
    mount.start() # this blocks, so call it at last

    # signal.signal(signal.SIGTERM, self.shutdown)
if __name__ == "__main__":
    main()

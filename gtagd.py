#!/usr/bin/env python3

# the gutentag daemon
#import sys
import pdb
import ast
import os.path
import traceback
import parser
import re
import unittest

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
    print("---")
    print("tagterm: '{}'".format(tagterm))

    # pdb.set_trace()
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

    print("quotedusedtags: {}".format(quotedusedtags))
    print("usedtags: {}".format(usedtags))
    print("tags: {}".format(tags))
    print("eval: '{}'".format(tagterm))

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

class GutenTagDaemon:
    def __init__(self):
        self._files = {} # key: filename, value: list of tags
        self._tags = {} # key: tag, value: list of files
        self._parser = parser.Parser()

        # TODO save and load the database, better use a MySQL database

    def setRPCServer(self, server):
        self._server = server

    def __check_integrity__(self):
        """
        integrity means, each tag in the tagsset of a file, must contain that file in its filesset, and vice versa
        """
        for f in self._files:
            for t in self._files[f]:
                if not t in self._tags:
                    raise Exception("tag %s not in tags list" % t)

                if f not in self._tags[t]:
                    raise Exception("filesset of %s does not contain file %s, but file's tagsset contains the tag" % (t, f))


        for t in self._tags:
            for f in self._tags[t]:
                if not f in self._files:
                    raise Exception("file %s not in files list" % f)

                if t not in self._files[f]:
                    raise Exception("tagsset of %s does not contain tag %s, but tag's filesset contains the file" % (f, t))

    def add(self, files, tags):
        """
        files: list of files
        tags: list of tags
        adds all the tags to all the specified files (dont care for double entries)
        """
        print("tag %i files with %i tags" % (len(files), len(tags)))
        try:
            checkfiles(files)
            for f in files:
                if not f in self._files.keys():
                    self._files[f] = set()

                self._files[f].update(set(tags))

            for t in tags:
                if not t in self._tags.keys():
                    self._tags[t] = set()

                self._tags[t].update(set(files))

            self.__check_integrity__()

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return True

    def remove(self, files, tags):
        """
        files: list of files
        tags: list of tags
        removes all the tags from all the specified files (dont care for unknown tags or files)
        """
        print("untag %i files with %i tags" % (len(files), len(tags)))
        try:
            checkfiles(files)
            for f in files:
                if f in self._files.keys():
                    self._files[f].difference_update(set(tags))

            for t in tags:
                if t in self._tags.keys():
                    self._tags[f].difference_update(set(files))

            self.__check_integrity__()

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return True

    def tags(self, filename):
        try:
            tags = []
            if filename == "":
                tags = list(self._tags.keys())

            elif filename in self._files:
                tags = list(self._files[filename])

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return tags

    def files(self, tagterm):
        try:
            matches = []
            if tagterm == "":
                matches = list(self._files.keys())

            else:
                for f in self._files:
                    if evalTagterm(tagterm, self._files[f]):
                        matches.append(f)

                # # create a tree
                # self._parser.clear()
                # tree = self._parser.parse(tagterm)
                # print("tagterm: {}".format(tagterm))
                # print("tree: {}".format(tree))
                # # evaluate the tree for the tags of each file
                # for f in self._files:
                #     if tree.eval(self._files[f]):
                #         matches.append(f)

        except:
            traceback.print_exc()
            raise Exception("Daemon Error")

        return matches

    def mount(self, tag_spec, mount_name):
        pass

    def unmount(self, mount_name):
        pass

    def listMounts(self):
        pass

    def getMountSpec(self, mount_name):
        pass

    def pid(self):
        return os.getpid()

def main():
    from xmlrpc.server import SimpleXMLRPCServer
    # Create server
    server = SimpleXMLRPCServer(("localhost", 8000))
    server.register_introspection_functions()

    gtagd = GutenTagDaemon()
    gtagd.setRPCServer(server)

    server.register_instance(gtagd)
    server.serve_forever()

if __name__ == "__main__":
    main()

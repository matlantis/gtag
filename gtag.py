#!/usr/bin/env python3

import os
import psutil
import getopt
import sys
import xmlrpc.client
import subprocess

# TODO: use argparse to parse parameters

def usage():
    """
    print some usage information.
    """
    print("""This is GutenTag
    usage:

    gtag add -f <files> -t <tags> - tag files with the tags specified. tags will be created
    gtag add <file> <tag> - shortform

    gtag remove -f <files> -t <tags> - removes the tags from the files - if present
    gtag remove <file> <tag> - shortform

    gtag tags <file> - list the tags of file
    gtag files <tagsterm> - list the files that match tagsterm

    gtag search <pattern> - list files with a tag that contains pattern

    gtag mount <tagsterm>
    gtag umount <tagsterm>

    gtag start - start the daemon
    gtag restart - restart the daemon
    gtag stop - stop the daemon

    gtag dir <dir> <tagterm> - creates a directory <dir> with symlinks to all files that match tagterm

    gtag export <tagterm> - create a zip file with all the files and a tag definition file
    gtag import <exported_zip_file> - import previously exported files and their tags
    """)

def parseTagsAndFiles():
    files = []
    tags = []
    mode = None
    if (len(sys.argv) < 5) and (len(sys.argv) > 2) and (not '-f' in sys.argv) and (not '-t' in sys.argv):
        # shortform
        if len(sys.argv) > 3:
            tags = [sys.argv[3]]
        files = [sys.argv[2]]

    else:
        for arg in sys.argv[2:]:
            if arg in ['-f', '-t']:
                mode = arg
                continue

            if mode == '-f':
                files.append(arg)

            if mode == '-t':
                tags.append(arg)

    return [tags, files]

def add(server):
    [tags, files] = parseTagsAndFiles()

    # ensure files have absolute paths
    files = list(os.path.abspath(f) for f in files)
    output = server.add(files, tags)

def remove(server):
    [tags, files] = parseTagsAndFiles()
    output = server.remove(files, tags)

def tags(server):
    filename = ""
    if len(sys.argv) > 2:
        filename = sys.argv[2]
    tags = server.tags(filename)

    for t in tags:
        print(str(t))

def files(server):
    tagterm = ""
    if len(sys.argv) > 2:
        tagterm = sys.argv[2]
    files = server.files(tagterm)

    for f in files:
        print(f)

def start():
    subprocess.Popen(["gtagd"])

def stop(server):
    pid = server.pid()
    p = psutil.Process(pid)
    p.terminate()  #or p.kill()

def restart(server):
    try:
        stop(server)

    except:
        print("stopping failed - ignoring")

    start()

def umount(server):
    tagterm = sys.argv[2]
    server.remove_mount(tagterm)

def mount(server):
    tagterm = sys.argv[2]
    server.add_mount(tagterm)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    output = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"

    # check action
    if len(sys.argv) < 2 or not sys.argv[1] in ['add', 'remove', 'tags', 'files', 'start', 'stop', 'restart', 'mount', 'umount']:
        usage()
        sys.exit()

    action = sys.argv[1]
    server = xmlrpc.client.ServerProxy('http://localhost:8000')

    if action == 'stop':
        stop(server)
    elif action == 'start':
        start()
    elif action == 'restart':
        restart(server)
    if action == 'add':
        add(server)
    elif action == 'remove':
        remove(server)
    elif action == 'tags':
        tags(server)
    elif action == 'files':
        files(server)
    elif action == 'umount':
        umount(server)
    elif action == 'mount':
        mount(server)

if __name__ == "__main__":
    main()

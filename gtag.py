#!/usr/bin/env python3

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
    gtag remove -f <files> -t <tags> - removes the tags from the files - if present
    gtag tags <file> - list the tags of file
    gtag files <tagsterm> - list the files that match tagsterm

    gtag start - start the daemon
    gtag restart - restart the daemon
    gtag stop - stop the daemon

    gtag dir <dir> [-t <tags>] [-e <extags>] - creates a directory <dir> with symlinks to all files tagged with all the tags <tags>, but not with <extags>
    """)

def parseTagsAndFiles():
    files = []
    tags = []
    mode = None
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
    subprocess.Popen(["./gtagd.py"])

def stop(server):
    pid = server.pid()
    p = psutil.Process(pid)
    p.terminate()  #or p.kill()

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
    if len(sys.argv) < 2 or not sys.argv[1] in ['add', 'remove', 'tags', 'files', 'start', 'stop', 'restart']:
        usage()
        sys.exit()

    action = sys.argv[1]
    server = xmlrpc.client.ServerProxy('http://localhost:8000')

    if action == 'stop':
        stop(server)
    elif action == 'start':
        start()
    elif action == 'restart':
        stop(server)
        start()
    if action == 'add':
        add(server)
    elif action == 'remove':
        remove(server)
    elif action == 'tags':
        tags(server)
    elif action == 'files':
        files(server)

if __name__ == "__main__":
    main()

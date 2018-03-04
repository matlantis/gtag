#!/usr/bin/env python3

import getopt, sys
import xmlrpc.client

# TODO: use argparse to parse parameters

def usage():
    """
    print some usage information.
    """
    print("""This is GutenTag
    usage:
    gtag tag -f <files> -t <tags> - tag files with the tags specified. tags will be created
    gtag untag -f <files> -t <tags> - removes the tags from the files - if present

    this is shitty: symetric behavior with -t and -f is needed, so -f should return only the _common_ tags. therefore a method for previos behavior is needed, also for tags
    gtag list -f [<file>] - list all tags on the files
    gtag list [-t <tags>] [-e <extags>] lists all files tags with <tags>, but not with <extags>
    gtag list -e lists all files

    gtag dir <dir> [-t <tags>] [-e <extags>] - creates a directory <dir> with symlinks to all files tagged with all the tags <tags>, but not with <extags>
    """)

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
    if len(sys.argv) < 2 or not sys.argv[1] in ['tag', 'untag', 'list', 'stop']:
        usage()
        sys.exit()

    action = sys.argv[1]
    server = xmlrpc.client.ServerProxy('http://localhost:8000')

    if action == 'stop':
        server.stop()

    # scan files and tags
    files = []
    tags = []
    extags = []

    mode = None
    for arg in sys.argv[2:]:
        if arg in ['-f', '-t', '-e']:
            mode = arg
            continue

        if mode == '-f':
            files.append(arg)

        if mode == '-t':
            tags.append(arg)

        if mode == '-e':
            extags.append(arg)

    output = server.__getattr__(action)(files, tags, extags)
    print(output) # TODO format the output, so that a list prints linewise, without quotes

if __name__ == "__main__":
    main()

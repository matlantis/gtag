import os
import unittest
import subprocess
import pdb
# from plumbum import local

TEST_DB_FILE = os.path.join(os.getenv("HOME"), ".gtagdb.test.sqlite3")


class GutenTagTest(unittest.TestCase):
    def _validate_list_out(self, out, l):
        exp = ""
        for i in sorted(l):
            exp += i + "\n"

        self.assertEqual(out, bytes(exp, 'utf8'))

    def setUp(self):
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)

        # run gtag start
        p = subprocess.run(['gtag', 'start', TEST_DB_FILE])
        # test if commands succeeded without error
        p.check_returncode()
        # test if instance is running - skipped

    def tearDown(self):
        # run gtag stop
        p = subprocess.run(['gtag', 'stop'])
        p.check_returncode()

        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)

    def test_start_stop(self):
        # test if db is empty
        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [])

    def test_add_remove_relative_file(self):
        # test with an relative filepath
        file1 = 'doesntexist.txt'
        file1_abs = os.path.join(os.getcwd(), file1)
        p = subprocess.run(['gtag', 'add', file1])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [file1_abs])

        p = subprocess.run(['gtag', 'remove', file1_abs])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [])

    def test_add_absolute_file(self):
        # test with an absolute filepath
        file1 = '/dir/doesntexist.txt'
        p = subprocess.run(['gtag', 'add', file1, 'TestTag'])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [file1])

    def test_add_remove_multiple_files(self):
        file1 = '/dir/doesntexist.txt'
        file2 = '/dir/doesnteigtherexist.txt'
        p = subprocess.run(['gtag', 'add', '-f', file1, file2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [file1, file2])

        p = subprocess.run(['gtag', 'remove', '-f', file1, file2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self._validate_list_out(out, [])

    def test_add_tags_and_list(self):
        file1 = 'doesntexist.txt'
        file1_abs = os.path.join(os.getcwd(), file1)
        tag1 = 'TestTag1'
        tag2 = 'TestTag2'

        # add a file with one tag
        p = subprocess.run(['gtag', 'add', file1, tag1])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags', file1_abs])
        self._validate_list_out(out, [tag1])

        # add another tag for that file
        p = subprocess.run(['gtag', 'add', file1, tag2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags', file1_abs])
        self._validate_list_out(out, [tag1, tag2])

    def add_and_remove_multiple_tags_to_multiple_files_and_list(self):
        file1 = '/dir/doesntexist.txt'
        file2 = '/dir/doesnteigtherexist.txt'
        file3 = '/dir/alsonot.txt'
        tag1 = 'TestTag1'
        tag2 = 'TestTag2'
        tag3 = 'TestTag3'
        p = subprocess.run(['gtag', 'add', '-f', file1, file2, '-t', tag1, tag2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags', file1])
        self._validate_list_out(out, [tag1, tag2])

        out = subprocess.check_output(['gtag', 'tags', file2])
        self._validate_list_out(out, [tag1, tag2])

        out = subprocess.check_output(['gtag', 'tags', file3])
        self._validate_list_out(out, [])

        # add another tag
        p = subprocess.run(['gtag', 'add', '-f', file1, file2, '-t', tag3])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags', file1])
        self._validate_list_out(out, [tag1, tag2, tag3])

        out = subprocess.check_output(['gtag', 'tags', file2])
        self._validate_list_out(out, [tag1, tag2, tag3])

        out = subprocess.check_output(['gtag', 'tags', file3])
        self._validate_list_out(out, [])

        # remove two tags
        p = subprocess.run(['gtag', 'remove', '-f', file1, file2, '-t', tag3, tag2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags', file1])
        self._validate_list_out(out, [tag1])

        out = subprocess.check_output(['gtag', 'tags', file2])
        self._validate_list_out(out, [tag1])

        out = subprocess.check_output(['gtag', 'tags', file3])
        self._validate_list_out(out, [])

    def add_remove_list_tags(self):
        tag1 = 'TestTag1'
        tag2 = 'TestTag2'
        p = subprocess.run(['gtag', 'add', '-t', tag1, tag2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags'])
        self._validate_list_out(out, [tag1, tag2])

        p = subprocess.run(['gtag', 'remove', '-t', tag1, tag2])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'tags'])
        self._validate_list_out(out, [])

    def test_list_files_2tags(self):
        # setup:
        # file1 TAG1
        # file2 TAG2
        # file3
        # file4 TAG1 TAG2
        tag1 = 'TestTag1'
        tag2 = 'TestTag2'
        file1 = '/dir/has_tag1.txt'
        file2 = '/dir/has_tag2.txt'
        file3 = '/dir/has_no_tag.txt'
        file4 = '/dir/has_tag1_and_tag2.txt'
        p = subprocess.run(['gtag', 'add', file1, tag1])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', file2, tag2])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', '-f', file3])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', '-f', file4, '-t', tag1, tag2])
        p.check_returncode()

        # tagterms to test:
        # TAG1 --> file1 file4
        # TAG1 & TAG2 --> file4
        # TAG1 | TAG2 --> file1 file2 file4
        # !TAG1 --> file2 file3
        # !TAG1 & TAG2 --> file2
        # TAG1 & !TAG2 --> file1
        # !(TAG1 & TAG2) --> file1 file2 file3
        out = subprocess.check_output(['gtag', 'files', tag1])
        self._validate_list_out(out, [file1, file4])
        out = subprocess.check_output(['gtag', 'files', tag1 + ' & ' + tag2])
        self._validate_list_out(out, [file4])
        out = subprocess.check_output(['gtag', 'files', tag1 + ' | ' + tag2])
        self._validate_list_out(out, [file1, file2, file4])
        out = subprocess.check_output(['gtag', 'files', '!' + tag1])
        self._validate_list_out(out, [file2, file3])
        out = subprocess.check_output(['gtag', 'files', '!' + tag1 + ' & ' + tag2])
        self._validate_list_out(out, [file2])
        out = subprocess.check_output(['gtag', 'files', tag1 + ' & ' + '!' + tag2])
        self._validate_list_out(out, [file1])
        out = subprocess.check_output(['gtag', 'files', '!(' + tag1 + ' & ' + tag2 +')'])
        self._validate_list_out(out, [file1, file2, file3])

    def test_list_files_3tags(self):
        # setup:
        # file1 TAG1
        # file2 TAG2
        # file3 TAG3
        # file4 TAG1 TAG2 TAG3
        # file5 TAG2 TAG3
        # file6 TAG1 TAG2
        # file7 TAG1 TAG3
        # file8
        tag1 = 'TestTag1'
        tag2 = 'TestTag2'
        tag3 = 'TestTag3'
        file1 = '/dir/has_tag1.txt'
        file2 = '/dir/has_tag2.txt'
        file3 = '/dir/has_tag3.txt'
        file4 = '/dir/has_tag1_and_tag2_and_tag3.txt'
        file5 = '/dir/has_tag2_and_tag3.txt'
        file6 = '/dir/has_tag1_and_tag2.txt'
        file7 = '/dir/has_tag1_and_tag3.txt'
        file8 = '/dir/has_no_tag.txt'
        p = subprocess.run(['gtag', 'add', '-f', file1, file4, file6, file7, '-t', tag1])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', '-f', file2, file4, file5, file6, '-t', tag2])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', '-f', file3, file4, file5, file7, '-t', tag3])
        p.check_returncode()
        p = subprocess.run(['gtag', 'add', '-f', file8])
        p.check_returncode()

        # tagterms to test:
        # TAG1 & TAG2 & TAG3 --> file4
        # TAG1 | TAG2 | TAG3 --> file1 file2 file3 file4 file5 file6 file7
        # ( TAG1 & TAG2 ) | TAG3 --> file3 file4 file5 file6 file7
        # TAG1 & ( TAG2 | TAG3 ) --> file4 file6 file7
        out = subprocess.check_output(['gtag', 'files', tag1 + ' & ' + tag2 + '&' + tag3])
        self._validate_list_out(out, [file4])
        out = subprocess.check_output(['gtag', 'files', tag1 + ' | ' + tag2 + '|' + tag3])
        self._validate_list_out(out, [file1, file2, file3, file4, file5, file6, file7])
        out = subprocess.check_output(['gtag', 'files', '(' + tag1 + ' & ' + tag2 + ') |' + tag3])
        self._validate_list_out(out, [file3, file4, file5, file6, file7])
        out = subprocess.check_output(['gtag', 'files', tag1 + ' & (' + tag2 + '|' + tag3 + ')'])
        self._validate_list_out(out, [file4, file6, file7])

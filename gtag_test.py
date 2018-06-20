import os
import unittest
import subprocess
import pdb
# from plumbum import local

TEST_DB_FILE = os.path.join(os.getenv("HOME"), ".gtagdb.test.sqlite3")

class GutenTagTest(unittest.TestCase):
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
        self.assertEqual(len(out), 0, "expected no output since db should be empty")

    def test_add_remove_relative_file(self):
        # test with an relative filepath
        testfilename = 'doesntexist.txt'
        testfilename_abs = os.path.join(os.getcwd(), testfilename)
        testtag = 'TestTag'
        p = subprocess.run(['gtag', 'add', testfilename, testtag])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self.assertEqual(out, bytes(testfilename_abs + "\n", 'utf8'))

        p = subprocess.run(['gtag', 'remove', testfilename_abs])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self.assertEqual(len(out), 0, "expected no output since db should be empty")

    def test_add_absolute_file(self):
        # test with an absolute filepath
        testfilename = '/dir/doesntexist.txt'
        p = subprocess.run(['gtag', 'add', testfilename, 'TestTag'])
        p.check_returncode()

        out = subprocess.check_output(['gtag', 'files'])
        self.assertEqual(out, bytes(testfilename + "\n", 'utf8'))


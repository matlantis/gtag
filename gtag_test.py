import os
import unittest
import subprocess
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

    def tearDown(self):
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)

        # run gtag stop
        p = subprocess.run(['gtag', 'stop'])
        p.check_returncode()

    def test_start_stop(self):
        # test if instance is running - skipped
        # test if db is empty
        out = subprocess.check_output(['gtag', 'files'])
        self.assertEqual(len(out), 0, "expected no output since db should be empty")


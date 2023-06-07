""" Test for lib modules """

import shutil
import unittest
import tempfile
from os import path

import lib.finder as finder
import lib.portal as portal
import lib.wildcards as wildcards

class TestStringMethods(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_get_files_with_ending(self):
        with open(path.join(self.test_dir, 'test.txt'), 'w') as test_file:
            test_file.write("Spam! Spam! Spam! Spam! Lovely spam! Wonderful spam!")
        with portal.In(self.test_dir):
            result = finder.get_files_with_ending(".txt")
            self.assertEqual([path.join(".", "test.txt")], result)


    def test_wildcard_double_star_match(self):
        pattern = "../something/otherthing/component/src/x.h"
        wildcard = "**/component/**"
        self.assertTrue(wildcards.matches_wildcard_pattern(pattern, wildcard))

    def test_wildcard_no_match(self):
        pattern = "../something/otherthing/component/src/x.h"
        wildcard = "**/component/*"
        self.assertFalse(wildcards.matches_wildcard_pattern(pattern, wildcard))

    def test_wildcard_wrong_start(self):
        pattern = "../something/otherthing/component/src/x.h"
        wildcard = "component/**"
        self.assertFalse(wildcards.matches_wildcard_pattern(pattern, wildcard))

    def test_wildcard_single_star_match(self):
        pattern = "../something/otherthing/component/src/x.h"
        wildcard = "../something/otherthing/component/src/*.h"
        self.assertTrue(wildcards.matches_wildcard_pattern(pattern, wildcard))
        pattern2 = "../something/otherthing/component/src/x.hpp"
        self.assertFalse(wildcards.matches_wildcard_pattern(pattern2, wildcard))

if __name__ == "__main__":
    unittest.main()

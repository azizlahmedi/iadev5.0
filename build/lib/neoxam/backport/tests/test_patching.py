#! /usr/bin/env python
# -*- coding:utf-8 -*-
import neoxam.tests
neoxam.tests.setup()

import os
import unittest

import tempfile

from neoxam.backport.backends import _generate_patch, generate_patch, Flag


class TestPatching(unittest.TestCase):
   
    def assertPatch(self, retcode, from_previous_content, from_content, to_content):
        with tempfile.TemporaryDirectory() as work:
            from_path = os.path.join(work, 'from.txt')
            from_previous_path = os.path.join(work, 'from_previous.txt')
            to_path = os.path.join(work, 'to.txt')
            for path, content in ((from_path, from_content), (from_previous_path, from_previous_content), (to_path, to_content)):
                with open(path, 'w', encoding='latin-1') as fd:
                    fd.write(content)
            found_retcode, content, _ = _generate_patch(work, from_path, from_previous_path, to_path)
            self.assertEquals(retcode, found_retcode)
            
    def assertEncoding(self, retcode, from_previous_content, from_content, to_content, encoding, patch_content=None, leading_path=""):
        with tempfile.TemporaryDirectory() as work:
            from_path = os.path.join(work, 'from.txt')
            from_previous_path = os.path.join(work, 'from_previous.txt')
            to_path = os.path.join(work, 'to.txt')
            for path, content in ((from_path, from_content), (from_previous_path, from_previous_content), (to_path, to_content)):
                with open(path, 'w', encoding='latin-1') as fd:
                    fd.write(content)
            found_retcode, content, _ = _generate_patch(work, from_path, from_previous_path, to_path, leading_path)
            self.assertEquals(retcode, found_retcode)
            if patch_content is not None:
                self.assertIn(patch_content.encode(encoding), content)

    def assertLeadingPaths(self, retcode, from_previous_content, from_content, to_content, leading_path):
        with tempfile.TemporaryDirectory() as work:
            from_path = os.path.join(work, 'from.txt')
            from_previous_path = os.path.join(work, 'from_previous.txt')
            to_path = os.path.join(work, 'to.txt')
            for path, content in ((from_path, from_content), (from_previous_path, from_previous_content), (to_path, to_content)):
                with open(path, 'w', encoding='latin-1') as fd:
                    fd.write(content)
            found_retcode, content, _ = _generate_patch(work, from_path, from_previous_path, to_path, leading_path)
            self.assertEquals(retcode, found_retcode)
            leading_lines = content.decode('latin-1').splitlines()[:2]
            self.assertIn(os.path.join("/", leading_path), leading_lines[0])
            self.assertIn(os.path.join("/", leading_path), leading_lines[1])

    
    def test_success(self):
        self.assertPatch(Flag.OK, 'héllo\n', 'world\n', 'héllo\n')
        
    def test_fuzzy(self):
        self.assertPatch(Flag.FUZZY, 'héllo\n', 'world\n', 'toto\nhéllo\n')

    def test_conflict(self):
        self.assertPatch(Flag.CONFLICT, 'héllo\n', 'world\n', 'toto\n')

    def test_errors(self):
        returncode, _, _ = generate_patch("bad_url1", "bad_url2", "bad_url3")
        self.assertEqual(Flag.ERROR, returncode)

    def test_encoding(self):
        expected_patch = """@@ -1 +1 @@
-héllo
+world
"""
        self.assertEncoding(Flag.OK, 'héllo\n', 'world\n', 'héllo\n', encoding='latin-1' , patch_content=expected_patch)
    
    def test_leading_path_names(self):
        self.assertLeadingPaths(Flag.OK, 'héllo\n', 'world\n', 'héllo\n', leading_path="path_to_the_file_to_be_patched.txt")

if __name__ == "__main__":
    suite = unittest.makeSuite(TestPatching, 'test')
    runner = unittest.TextTestRunner()
    runner.run(suite)

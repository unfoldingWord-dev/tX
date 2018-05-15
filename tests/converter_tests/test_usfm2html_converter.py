from __future__ import absolute_import, unicode_literals, print_function
import codecs
import os
import tempfile
import unittest
import shutil
from contextlib import closing

from src.services.converters.usfm2html_converter import Usfm2HtmlConverter
from src.general_tools.file_utils import remove_tree, unzip, remove
from src.app.app import App


class TestUsfmHtmlConverter(unittest.TestCase):

    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName))
        self.temp_dir = tempfile.mkdtemp(prefix='TestUsfmHtmlConverter')

    def tearDown(self):
        """Runs after each test."""
        # delete temp files
        remove_tree(self.temp_dir)

    @classmethod
    def setUpClass(cls):
        """Called before tests in this class are run."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Called after tests in this class are run."""
        pass

    def test_close(self):
        """This tests that the temp directories are deleted when the class is closed."""

        with closing(Usfm2HtmlConverter('', '')) as tx:
            download_dir = tx.download_dir
            files_dir = tx.files_dir
            out_dir = tx.output_dir

            # verify the directories are present
            self.assertTrue(os.path.isdir(download_dir))
            self.assertTrue(os.path.isdir(files_dir))
            self.assertTrue(os.path.isdir(out_dir))

        # now they should have been deleted
        self.assertFalse(os.path.isdir(download_dir))
        self.assertFalse(os.path.isdir(files_dir))
        self.assertFalse(os.path.isdir(out_dir))

    def test_run(self):
        """Runs the converter and verifies the output."""
        # test with the English OBS
        zip_file = os.path.join(self.resources_dir, 'eight_bible_books.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        with closing(Usfm2HtmlConverter('', 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['60-JAS.html', '61-1PE.html', '62-2PE.html', '63-1JN.html', '64-2JN.html', '65-3JN.html',
                           '66-JUD.html', '67-REV.html']
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))

    def test_convert_only_jas(self):
        """Runs the converter and verifies the output."""
        # test with the English OBS
        zip_file = os.path.join(self.resources_dir, 'eight_bible_books.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        source_url = 'http://test.com/preconvert/22f3d09f7a.zip?convert_only=60-JAS.usfm'
        with closing(Usfm2HtmlConverter(source_url, 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['60-JAS.html']
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))
        files_to_not_verify = ['61-1PE.html', '62-2PE.html', '63-1JN.html', '64-2JN.html', '65-3JN.html',
                               '66-JUD.html', '67-REV.html']
        for file_to_verify in files_to_not_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertFalse(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))
        self.assertEqual(tx.source, source_url.split('?')[0])

    def test_convert_only_jas_and_jud(self):
        """Runs the converter and verifies the output."""
        # test with the English OBS
        zip_file = os.path.join(self.resources_dir, 'eight_bible_books.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        source_url = 'http://test.com/preconvert/22f3d09f7a.zip?convert_only=60-JAS.usfm,66-JUD.usfm'
        with closing(Usfm2HtmlConverter(source_url, 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['66-JUD.html', '60-JAS.html']
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))
        files_to_not_verify = ['61-1PE.html', '62-2PE.html', '63-1JN.html', '64-2JN.html', '65-3JN.html',
                               '67-REV.html']
        for file_to_verify in files_to_not_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertFalse(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))
        self.assertEqual(tx.source, source_url.split('?')[0])

    def test_php_complete(self):
        """
        Runs the converter and verifies the output
        """
        # test with the English OBS
        zip_file = os.path.join(self.resources_dir, '51-PHP.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        with closing(Usfm2HtmlConverter('', 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['51-PHP.html']
        self.verify_files(files_to_verify)

    def test_php_illegal_url(self):
        """
        Runs the converter and verifies the output
        """
        # test with the English OBS
        zip_file = os.path.join(self.resources_dir, '51-PHP.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        with closing(Usfm2HtmlConverter(' ', 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['51-PHP.html']
        self.verify_files(files_to_verify)

    def test_matt_complete_with_backslash(self):
        """
        Runs the converter and verifies the output
        """
        zip_file = os.path.join(self.resources_dir, 'kpb_mat_text_udb.zip')
        zip_file = self.make_duplicate_zip_that_can_be_deleted(zip_file)
        out_zip_file = tempfile.mktemp('.zip', dir=self.temp_dir)
        with closing(Usfm2HtmlConverter('', 'udb', out_zip_file)) as tx:
            tx.input_zip_file = zip_file
            results = tx.run()
        # verify the output
        self.assertTrue(os.path.isfile(out_zip_file), "There was no output zip file produced.")
        self.assertIsNotNone(results)
        self.out_dir = tempfile.mkdtemp(prefix='udb_', dir=self.temp_dir)
        unzip(out_zip_file, self.out_dir)
        files_to_verify = ['41-MAT.html']
        self.verify_files(files_to_verify)

    def test_bad_source(self):
        """This tests giving a bad source to the converter"""
        with closing(Usfm2HtmlConverter('bad_source', 'bad_resource')) as tx:
            result = tx.run()
        self.assertFalse(result['success'])
        self.assertEqual(result['errors'], [u'Conversion process ended abnormally: Failed to download bad_source'])

    #
    # helpers
    #

    def verify_files(self, files_to_verify):
        for file_to_verify in files_to_verify:
            file_name = os.path.join(self.out_dir, file_to_verify)
            self.assertTrue(os.path.isfile(file_name), 'UDB HTML file not found: {0}'.format(file_name))

            usfm = None
            with codecs.open(file_name, 'r', 'utf-8-sig') as usfm_file:
                usfm = usfm_file.read()

            self.assertIsNotNone(usfm)
            self.assertTrue(len(usfm) > 10, 'Bible usfm file contents missing: {0}'.format(file_to_verify))

    def make_duplicate_zip_that_can_be_deleted(self, zip_file):
        in_zip_file = tempfile.mktemp(prefix="test_data", suffix=".zip", dir=self.temp_dir)
        shutil.copy(zip_file, in_zip_file)
        zip_file = in_zip_file
        return zip_file


if __name__ == '__main__':
    unittest.main()

from __future__ import absolute_import, unicode_literals, print_function
import datetime
import os
import unittest

from moto import mock_dynamodb2

from tools.door43_tools.page_metrics import PageMetrics
from tools.general_tools import file_utils
from models.language_stats import LanguageStats
from app.app import App


@mock_dynamodb2
class ViewCountTest(unittest.TestCase):
    LANG_CODE = "en"
    INITIAL_VIEW_COUNT = 5
    resources_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')

    def setUp(self):
        """Runs before each test."""
        App(prefix='{0}-'.format(self._testMethodName), db_connection_string='sqlite:///:memory:')
        self.init_table(ViewCountTest.INITIAL_VIEW_COUNT)

    def test_valid(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validIncrement(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_invalidLanguageStatsTableShouldFail(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT + 1
        App._language_stats_db_handler = None
        App.language_stats_table_name = None
        self.lang_url = "https://live.door43.org/en/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.DB_ACCESS_ERROR)

    def test_validLangNotInManifestTable(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_validLangNotInManifestTableIncrement(self):
        # given
        vc = PageMetrics()
        expected_view_count = 1
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_validLangTextIncrement(self):
        # given
        vc = PageMetrics()
        expected_view_count = 1
        self.lang_url = "https://live.door43.org/zzz/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results)

    def test_missingPathShouldFail(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.lang_url = ""

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_unsupportedPathShouldFail(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.lang_url = "https://other_url.com/dummy/stuff2/stuff3/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_shortUrlShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_shortLanguageShouldFail(self):
        # given
        vc = PageMetrics(**{})
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/e/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=1)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/enxx/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail2(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail3(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-a/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail4(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-x/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_longLanguageShouldFail5(self):
        # given
        vc = PageMetrics()
        expected_view_count = ViewCountTest.INITIAL_VIEW_COUNT
        self.lang_url = "https://live.door43.org/eng-x-/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results, error_type=PageMetrics.INVALID_LANG_URL_ERROR)

    def test_extendedLanguage(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/eng-x-a/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_localizedLanguage2(self):
        # given
        vc = PageMetrics()
        expected_view_count = 0
        self.lang_url = "https://live.door43.org/es-419/"

        # when
        results = vc.get_language_view_count(self.lang_url, increment=0)

        # then
        self.validateResults(expected_view_count, results)

    def test_listOfLanguageNames(self):
        lang_names_file = os.path.join(self.resources_dir, "langnames.json")
        lang_names = file_utils.load_json_object(lang_names_file)
        vc = PageMetrics()
        success = True
        msg = ""
        for lang_name in lang_names:

            # given
            code = lang_name["lc"]
            language_name = lang_name["ln"]
            expected_language_code = code.lower()
            self.lang_url = "https://live.door43.org/pt-BR/"

            # when
            lang_code = vc.validate_language_code(code)

            # then
            if lang_code != expected_language_code:
                msg = "FAILURE: For language '{0}', expected code '{2}' but got '{1}'".format(language_name, lang_code,
                                                                                              expected_language_code)
                App.logger.debug(msg)
                success = False

        if not success:
            self.assertTrue(success, msg)

    def test_listOfTempLanguageNames(self):
        lang_names_file = os.path.join(self.resources_dir, "templanguages.json")
        lang_names = file_utils.load_json_object(lang_names_file)
        vc = PageMetrics()
        success = True
        msg = ""
        for lang_name in lang_names:

            # given
            code = lang_name["lc"]
            language_name = lang_name["ln"]
            expected_language_code = code.lower()
            self.lang_url = "https://live.door43.org/pt-BR/"

            # when
            lang_code = vc.validate_language_code(code)

            # then
            if lang_code != expected_language_code:
                msg = "FAILURE: For language '{0}', expected code '{2}' but got '{1}'".format(language_name, lang_code,
                                                                                              expected_language_code)
                App.logger.debug(msg)
                success = False

        if not success:
            self.assertTrue(success, msg)

    #
    # helpers
    #

    def validateResults(self, expected_view_count, results, error_type=None):
        self.assertIsNotNone(results)
        if error_type:
            self.assertEquals(results['ErrorMessage'], error_type + self.lang_url, "Error message mismatch")
        else:
            self.assertTrue('ErrorMessage' not in results)
            self.assertEquals(results['view_count'], expected_view_count)

    def init_table(self, view_count):
        try:
            App.language_stats_db_handler().table.delete()
        except:
            pass

        App.language_stats_db_handler().resource.create_table(
            TableName=App.language_stats_table_name,
            KeySchema=[
                {
                    'AttributeName': 'lang_code',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'lang_code',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            },
        )

        lang_stats_data = {
            'lang_code': ViewCountTest.LANG_CODE.lower(),
            'last_updated': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'manifest': '{}',
            'views': view_count
        }

        lang_stats = LanguageStats(lang_stats_data).insert()
        App.logger.debug("new language: " + lang_stats.lang_code)


if __name__ == "__main__":
    unittest.main()

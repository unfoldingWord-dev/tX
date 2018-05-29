from __future__ import print_function, unicode_literals
import os
import json
try: from HTMLParser import HTMLParser
except ModuleNotFoundError: # in Python3
    from html.parser import HTMLParser

from .linter import Linter
from tools.aws_tools.lambda_handler import LambdaHandler
from tools.general_tools.file_utils import read_file, get_files
from app.app import App


class MarkdownLinter(Linter):

    def __init__(self, *args, **kwargs):
        super(MarkdownLinter, self).__init__(*args, **kwargs)
        self.single_file = None
        self.single_dir = None

    def lint(self):
        """
        Checks for issues with all Markdown project, such as bad use of headers, bullets, etc.

        Use self.log.warning("message") to log any issues.
        self.source_dir is the directory of source files (.md)
        :return bool:
        """
        md_data = self.get_strings()
        App.logger.debug("Size of markdown data={0}".format(len(md_data)))
        lint_data = self.invoke_markdown_linter(self.get_invoke_payload(md_data))
        if not lint_data:
            return False
        for f in lint_data.keys():
            file_url = 'https://git.door43.org/{0}/{1}/src/master/{2}'.format(self.repo_owner, self.rc.repo_name, f)
            for item in lint_data[f]:
                error_context = ''
                if item['errorContext']:
                    error_context = 'See "{0}"'.format(self.strip_tags(item['errorContext']))
                line = '<a href="{0}" target="_blank">{1}</a> - Line {2}: {3}. {4}'. \
                    format(file_url, f, item['lineNumber'], item['ruleDescription'], error_context)
                self.log.warning(line)
        return True

    def get_strings(self):
        if self.single_dir:
            dir_path = os.path.join(self.source_dir, self.single_dir)
            sub_files = sorted(get_files(directory=dir_path, relative_paths=True, exclude=self.EXCLUDED_FILES,
                                         extensions=['.md']))
            files = []
            for f in sub_files:
                files.append(os.path.join(self.single_dir, f))
        else:
            files = sorted(get_files(directory=self.source_dir, relative_paths=True, exclude=self.EXCLUDED_FILES,
                                     extensions=['.md']))
        strings = {}
        for f in files:
            path = os.path.join(self.source_dir, f)
            text = read_file(path)
            strings[f] = text
        return strings

    def get_invoke_payload(self, strings):
        return {
            'options': {
                'strings': strings,
                'config': {
                    'default': True,
                    'no-hard-tabs': False,  # MD010
                    'whitespace': False,  # MD009, MD010, MD012, MD027, MD028, MD030, MD037, MD038, MD039
                    'line-length': False,  # MD013
                    'no-inline-html': False,  # MD033
                    'no-duplicate-header': False,  # MD024
                    'single-h1': False,  # MD025
                    'no-trailing-punctuation': False,  # MD026
                    'no-emphasis-as-header': False,  # MD036
                    'first-header-h1': False,  # MD002
                    'first-line-h1': False,  # MD041
                    'no-bare-urls': False,  # MD034
                }
            }
        }

    def invoke_markdown_linter(self, payload):
        lambda_handler = LambdaHandler()
        lint_function = '{0}tx_markdown_linter'.format(App.prefix)
        App.logger.debug("Size of {0} lint data={1}".format(self.s3_results_key, len(payload)))
        response = lambda_handler.invoke(lint_function, payload)
        if 'errorMessage' in response:
            App.logger.error(response['errorMessage'])
            return None
        elif 'Payload' in response:
            return json.loads(response['Payload'].read())

    def get_dir_for_book(self, book):
        parts = book.split('-')
        link = book
        if len(parts) > 1:
            link = parts[1].lower()
        return link

    @staticmethod
    def strip_tags(html):
        ts = TagStripper()
        ts.feed(html)
        return ts.get_data()


class TagStripper(HTMLParser):

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

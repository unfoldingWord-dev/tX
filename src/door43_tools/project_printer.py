from __future__ import print_function, unicode_literals
import os
import tempfile
import codecs
from bs4 import BeautifulSoup
from glob import glob
from general_tools.file_utils import read_file
from resource_container.ResourceContainer import RC
from app.app import App


class ProjectPrinter(object):
    """
    Prints a project given the project ID

    Read from the project's dir in the cdn.door43.org bucket all the .html file and compile them into one for printing,
    if the print_all.html page doesn't already exist. Return the contents of print_all.html
    """

    def __init__(self):
        self.project_id = None

    def print_project(self, project_id):
        """
        :param string project_id: 
        :return string: 
        """
        self.project_id = project_id
        if len(project_id.split('/')) != 3:
            raise Exception('Project not found.')
        user_name, repo_name, commit_id = project_id.split('/')
        source_path = 'u/{0}'.format(project_id)
        print_all_key = '{0}/print_all.html'.format(source_path)
        print_all_file = tempfile.mktemp(prefix='print_all_')
        if App.cdn_s3_handler().key_exists(print_all_key):
            return App.cdn_s3_handler().bucket_name + '/' + print_all_key
        files_dir = tempfile.mkdtemp(prefix='files_')
        App.cdn_s3_handler().download_dir(source_path, files_dir)
        project_dir = os.path.join(files_dir, source_path.replace('/', os.path.sep))
        if not os.path.isdir(project_dir):
            raise Exception('Project not found.')
        rc = RC(project_dir, repo_name)
        with codecs.open(print_all_file, 'w', 'utf-8-sig') as print_all:
            print_all.write("""<html lang="{0}" dir="{1}">
<head>
    <meta charset="UTF-8"/>
    <title>{2}: {3}</title>
    <style type="text/css">
        body > div {{
            page-break-after: always;
        }}
    </style>
</head>
<body onLoad="window.print()">
    <h1>{2}: {3}</h1>
""".format(rc.resource.language.identifier, rc.resource.language.direction, rc.resource.language.title,
       rc.resource.title))
            for fname in sorted(glob(os.path.join(project_dir, '*.html')), key=self.front_to_back):
                with codecs.open(fname, 'r') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    # get the body of the raw html file
                    content = soup.div
                    if not content:
                        content = BeautifulSoup('<div>No content</div>', 'html.parser').find('div').extract()
                    content['id'] = os.path.basename(fname)
                    print_all.write(unicode(content))
            print_all.write("""
</body>
</html>
""")
            App.cdn_s3_handler().upload_file(print_all_file, print_all_key, cache_time=0, content_type='text/html')
        return App.cdn_s3_handler().bucket_name + '/' + print_all_key

    @staticmethod
    def front_to_back(file_path):
        """
        Prefixes any "front" or "back" file with a number so they are first and last respectively
        Used with sorting. Primarily used with OBS
        :param string file_path:
        :return string:
        """
        parent_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        if file_name == 'front.html':
            return os.path.join(parent_dir, '00_{0}'.format(file_name))
        elif file_name == 'back.html':
            return os.path.join(parent_dir, '99_{0}'.format(file_name))
        else:
            return file_path

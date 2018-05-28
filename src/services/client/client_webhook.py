from __future__ import print_function, unicode_literals
import urllib
import os
import tempfile
import json
import hashlib
from datetime import datetime, timedelta

from flask import request, url_for
from flask_api import status

from general_tools.file_utils import unzip, write_file, add_contents_to_zip, remove_tree
from general_tools.url_utils import download_file
from resource_container.ResourceContainer import RC
from services.client.preprocessors import do_preprocess
from models.manifest import TxManifest
from models.module import TxModule
from models.job import TxJob
from app.app import App


def ClientWebhookHandler():
    """
    Accepts webhook notification from DCS.

    :param dict commit_data:
    """
    # Bail if this is not a POST with a payload
    if not request.data:
        return {'error': 'No payload found. You must submit a POST request via a DCS webhook notification'}
    # Bail if this is not from DCS
    if 'X-Gogs-Event' not in request.headers:
        return {'error': 'This does not appear to be from DCS.'}
    # Bail if this is not a push event
    if not request.headers['X-Gogs-Event'] == 'push':
        return {'error': 'This does not appear to be a push.'}

    # Bail if the URL to the repo is invalid
    if not request.data['repository']['html_url'].startswith(App.gogs_url):
        return {'error': 'The repo does not belong to {0}.'.format(App.gogs_url)}

    # Bail if the commit branch is not the default branch
    try:
        commit_branch = request.data['ref'].split('/')[2]
    except IndexError:
        return {'error': 'Could not determine commit branch, exiting.'}
    except KeyError:
        return {'error': 'This does not appear to be a push, exiting.'}
    if commit_branch != request.data['repository']['default_branch']:
        return {'error': 'Commit branch: {0} is not the default branch.'.format(commit_branch)}

    # Check that the user token is valid
    #if not App.gogs_user_token:
        #raise Exception('DCS user token not given in Payload.')
    #user = App.gogs_handler().get_user(App.gogs_user_token)
    #if not user:
        #raise Exception('Invalid DCS user token given in Payload')

    webhook = ClientWebhook(request.data)
    webhook.process_webhook()
    print("ClientWebhookHandler() has finished")


class ClientWebhook(object):

    def __init__(self, commit_data=None):
        """
        :param dict commit_data:
        """
        self.commit_data = commit_data
        if App.pre_convert_bucket:
            self.source_url_base = 'https://s3-{0}.amazonaws.com/{1}'.format(App.aws_region_name, App.pre_convert_bucket)
        else:
            self.source_url_base = None
        # move everything down one directory level for simple delete
        self.intermediate_dir = 'converter_webhook'
        self.base_temp_dir = os.path.join(tempfile.gettempdir(), self.intermediate_dir)
        try:
            os.makedirs(self.base_temp_dir)
        except:
            pass
        self.converter_callback = '{0}/client/callback/converter'.format(App.api_url)
        self.linter_callback = '{0}/client/callback/linter'.format(App.api_url)

    def process_webhook(self):
        # Get the commit_id, commit_url
        commit_id = self.commit_data['after']
        commit = None
        for commit in self.commit_data['commits']:
            if commit['id'] == commit_id:
                break
        commit_id = commit_id[:10]  # Only use the short form
        commit_url = commit['url']


        # Gather other details from the commit that we will note for the job(s)
        user_name = self.commit_data['repository']['owner']['username']
        repo_name = self.commit_data['repository']['name']
        compare_url = self.commit_data['compare_url']
        commit_message = commit['message']

        if 'pusher' in self.commit_data:
            pusher = self.commit_data['pusher']
        else:
            pusher = {'username': commit['author']['username']}
        pusher_username = pusher['username']

        # Download and unzip the repo files
        repo_dir = self.get_repo_files(commit_url, repo_name)

        # Get the resource container
        rc = RC(repo_dir, repo_name)

        # Save manifest to manifest table
        manifest_data = {
            'repo_name': repo_name,
            'user_name': user_name,
            'lang_code': rc.resource.language.identifier,
            'resource_id': rc.resource.identifier,
            'resource_type': rc.resource.type,
            'title': rc.resource.title,
            'manifest': json.dumps(rc.as_dict()),
            'last_updated': datetime.utcnow()
        }
        print("client_webhook got manifest_data:", manifest_data ) # RJH
        # First see if manifest already exists in DB and update it if it is
        print("client_webhook getting manifest for {!r} with user {!r}".format(repo_name,user_name)) # RJH
        # RJH: Next line always fails on the first call! Why?
        tx_manifest = TxManifest.get(repo_name=repo_name, user_name=user_name)
        if tx_manifest:
            for key, value in manifest_data.items():
                setattr(tx_manifest, key, value)
            App.logger.debug('Updating manifest in manifest table: {0}'.format(manifest_data))
            tx_manifest.update()
        else:
            tx_manifest = TxManifest(**manifest_data)
            App.logger.debug('Inserting manifest into manifest table: {0}'.format(tx_manifest))
            tx_manifest.insert()

        # Preprocess the files
        preprocess_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='preprocess_')
        results, preprocessor = do_preprocess(rc, repo_dir, preprocess_dir)

        # Zip up the massaged files
        zip_filepath = tempfile.mktemp(dir=self.base_temp_dir, suffix='.zip')
        App.logger.debug('Zipping files from {0} to {1}...'.format(preprocess_dir, zip_filepath))
        add_contents_to_zip(zip_filepath, preprocess_dir)
        App.logger.debug('finished.')

        # Upload zipped file to the S3 bucket
        file_key = self.upload_zip_file(commit_id, zip_filepath)

        #print("ClientWebhook.process_webhook setting up TxJob with username={0}...".format(user.username))
        print("ClientWebhook.process_webhook setting up TxJob...")
        job = TxJob()
        job.job_id = self.get_unique_job_id()
        job.identifier = job.job_id
        job.user_name = user_name
        job.repo_name = repo_name
        job.commit_id = commit_id
        job.manifests_id = tx_manifest.id
        job.created_at = datetime.utcnow()
        # Seems never used (RJH)
        #job.user = user.username  # Username of the token, not necessarily the repo's owner
        job.input_format = rc.resource.file_ext
        job.resource_type = rc.resource.identifier
        job.source = self.source_url_base + "/" + file_key
        job.cdn_bucket = App.cdn_bucket
        job.cdn_file = 'tx/job/{0}.zip'.format(job.job_id)
        job.output = 'https://{0}/{1}'.format(App.cdn_bucket, job.cdn_file)
        job.callback = App.api_url + '/client/callback'
        job.output_format = 'html'
        job.links = {
            "href": "{0}/tx/job/{1}".format(App.api_url, job.job_id),
            "rel": "self",
            "method": "GET"
        }
        job.success = False

        converter = self.get_converter_module(job)
        linter = self.get_linter_module(job)

        if converter:
            job.convert_module = converter.name
            job.started_at = datetime.utcnow()
            job.expires_at = job.started_at + timedelta(days=1)
            job.eta = job.started_at + timedelta(minutes=5)
            job.status = 'started'
            job.message = 'Conversion started...'
            job.log_message('Started job for {0}/{1}/{2}'.format(job.user_name, job.repo_name, job.commit_id))
        else:
            job.error_message('No converter was found to convert {0} from {1} to {2}'.format(job.resource_type,
                                                                                             job.input_format,
                                                                                             job.output_format))
            job.message = 'No converter found'
            job.status = 'failed'

        if linter:
            job.lint_module = linter.name
        else:
            App.logger.debug('No linter was found to lint {0}'.format(job.resource_type))

        job.insert()

        # Get S3 bucket/dir ready
        s3_commit_key = 'u/{0}/{1}/{2}'.format(job.user_name, job.repo_name, job.commit_id)
        self.clear_commit_directory_in_cdn(s3_commit_key)

        # Create a build log
        build_log_json = self.create_build_log(commit_id, commit_message, commit_url, compare_url, job,
                                               pusher_username, repo_name, user_name)
        # Upload an initial build_log
        self.upload_build_log_to_s3(build_log_json, s3_commit_key)

        # Update the project.json file
        self.update_project_json(commit_id, job, repo_name, user_name)

        # Convert and lint
        if converter:
            if not preprocessor.is_multiple_jobs():
                self.send_request_to_converter(job, converter)
                if linter:
                    extra_payload = {
                        's3_results_key': s3_commit_key
                    }
                    self.send_request_to_linter(job, linter, commit_url, extra_payload=extra_payload)
            else:
                # -----------------------------
                # multiple book project
                # -----------------------------
                books = preprocessor.get_book_list()
                App.logger.debug('Splitting job into separate parts for books: ' + ','.join(books))
                book_count = len(books)
                build_log_json['multiple'] = True
                build_log_json['build_logs'] = []
                for i in range(0, len(books)):
                    book = books[i]
                    App.logger.debug('Adding job for {0}, part {1} of {2}'.format(book, i, book_count))
                    # Send job request to tx-manager
                    if i == 0:
                        book_job = job  # use the original job created above for the first book
                        book_job.identifier = '{0}/{1}/{2}/{3}'.format(job.job_id, book_count, i, book)
                    else:
                        book_job = job.clone()  # copy the original job for this book's job
                        book_job.job_id = self.get_unique_job_id()
                        book_job.identifier = '{0}/{1}/{2}/{3}'.format(book_job.job_id, book_count, i, book)
                        book_job.cdn_file = 'tx/job/{0}.zip'.format(book_job.job_id)
                        book_job.output = 'https://{0}/{1}'.format(App.cdn_bucket, book_job.cdn_file)
                        book_job.links = {
                            "href": "{0}/tx/job/{1}".format(App.api_url, book_job.job_id),
                            "rel": "self",
                            "method": "GET"
                        }
                        book_job.insert()

                    book_job.source = self.build_multipart_source(file_key, book)
                    book_job.update()
                    book_build_log = self.create_build_log(commit_id, commit_message, commit_url, compare_url, book_job,
                                                           pusher_username, repo_name, user_name)
                    if len(book) > 0:
                        part = str(i)
                        book_build_log['book'] = book
                        book_build_log['part'] = part
                    build_log_json['build_logs'].append(book_build_log)
                    self.upload_build_log_to_s3(book_build_log, s3_commit_key, str(i) + "/")
                    self.send_request_to_converter(book_job, converter)
                    if linter:
                        extra_payload = {
                            'single_file': book,
                            's3_results_key': '{0}/{1}'.format(s3_commit_key, i)
                        }
                        self.send_request_to_linter(book_job, linter, commit_url, extra_payload)

        remove_tree(self.base_temp_dir)  # cleanup
        print("process_webhook() is returning:", build_log_json )
        return build_log_json

    def build_multipart_source(self, file_key, book):
        params = urllib.urlencode({'convert_only': book})
        source_url = '{0}/{1}?{2}'.format(self.source_url_base, file_key, params)
        return source_url

    def clear_commit_directory_in_cdn(self, s3_commit_key):
        # clear out the commit directory in the cdn bucket for this project revision
        for obj in App.cdn_s3_handler().get_objects(prefix=s3_commit_key):
            App.logger.debug('Removing file: ' + obj.key)
            App.cdn_s3_handler().delete_file(obj.key)

    def upload_build_log_to_s3(self, build_log, s3_commit_key, part=''):
        """
        :param dict build_log:
        :param string s3_commit_key:
        :param string part:
        :return:
        """
        build_log_file = os.path.join(self.base_temp_dir, 'build_log.json')
        write_file(build_log_file, build_log)
        upload_key = '{0}/{1}build_log.json'.format(s3_commit_key, part)
        App.logger.debug('Saving build log to {}/{}'.format(App.cdn_bucket,upload_key))
        App.cdn_s3_handler().upload_file(build_log_file, upload_key, cache_time=0)
        # App.logger.debug('build log contains: ' + json.dumps(build_log_json))

    def create_build_log(self, commit_id, commit_message, commit_url, compare_url, job, pusher_username, repo_name,
                         repo_owner):
        """
        :param string commit_id:
        :param string commit_message:
        :param string commit_url:
        :param string compare_url:
        :param TxJob job:
        :param string pusher_username:
        :param string repo_name:
        :param string repo_owner:
        :return dict:
        """
        build_log_json = dict(job)
        build_log_json['repo_name'] = repo_name
        build_log_json['repo_owner'] = repo_owner
        build_log_json['commit_id'] = commit_id
        build_log_json['committed_by'] = pusher_username
        build_log_json['commit_url'] = commit_url
        build_log_json['compare_url'] = compare_url
        build_log_json['commit_message'] = commit_message

        return build_log_json

    def update_project_json(self, commit_id, job, repo_name, repo_owner):
        """
        :param string commit_id:
        :param TxJob job:
        :param string repo_name:
        :param string repo_owner:
        :return:
        """
        project_json_key = 'u/{0}/{1}/project.json'.format(repo_owner, repo_name)
        project_json = App.cdn_s3_handler().get_json(project_json_key)
        project_json['user'] = repo_owner
        project_json['repo'] = repo_name
        project_json['repo_url'] = 'https://git.door43.org/{0}/{1}'.format(repo_owner, repo_name)
        commit = {
            'id': commit_id,
            'created_at': job.created_at,
            'status': job.status,
            'success': job.success,
            'started_at': None,
            'ended_at': None
        }
        if 'commits' not in project_json:
            project_json['commits'] = []
        commits = []
        for c in project_json['commits']:
            if c['id'] != commit_id:
                commits.append(c)
        commits.append(commit)
        project_json['commits'] = commits
        project_file = os.path.join(self.base_temp_dir, 'project.json')
        write_file(project_file, project_json)
        App.cdn_s3_handler().upload_file(project_file, project_json_key)

    def upload_zip_file(self, commit_id, zip_filepath):
        file_key = 'preconvert/{0}.zip'.format(commit_id)
        App.logger.debug('Uploading {0} to {1}/{2}...'.format(zip_filepath, App.pre_convert_bucket, file_key))
        try:
            App.pre_convert_s3_handler().upload_file(zip_filepath, file_key, cache_time=0)
        except Exception as e:
            App.logger.error('Failed to upload zipped repo up to server')
            App.logger.exception(e)
        finally:
            App.logger.debug('finished.')
        return file_key

    def get_repo_files(self, commit_url, repo_name):
        temp_dir = tempfile.mkdtemp(dir=self.base_temp_dir, prefix='{0}_'.format(repo_name))
        self.download_repo(commit_url, temp_dir)
        repo_dir = os.path.join(temp_dir, repo_name.lower())
        if not os.path.isdir(repo_dir):
            repo_dir = temp_dir

        return repo_dir

    def send_request_to_converter(self, job, converter):
        """
        :param TxJob job:
        :param TxModule converter:
        :return bool:
        """
        payload = {
            'identifier': job.identifier,
            'source_url': job.source,
            'resource_id': job.resource_type,
            'cdn_bucket': job.cdn_bucket,
            'cdn_file': job.cdn_file,
            'options': job.options,
            'convert_callback': self.converter_callback
        }
        return self.send_payload_to_converter(payload, converter)

    def send_payload_to_converter(self, payload, converter):
        """
        :param dict payload:
        :param TxModule converter:
        :return bool:
        """
        # TODO: Make this use urllib2 to make a async POST to the API. Currently invokes Lambda directly XXXXXXXXXXXXXXXXX
        payload = {
            'data': payload,
            'vars': {
                'prefix': App.prefix
            }
        }
        converter_name = converter.name
        if not isinstance(converter_name,str): # bytes in Python3 -- not sure where it gets set
            converter_name = converter_name.decode()
        print("converter_name", repr(converter_name))
        App.logger.debug('Sending Payload to converter {0}:'.format(converter_name))
        App.logger.debug(payload)
        converter_function = '{0}tx_convert_{1}'.format(App.prefix, converter_name)
        print("send_payload_to_converter: converter_function is {!r} payload={}".format(converter_function,payload))
        # TODO: Put an alternative function call in here RJH
        #response = App.lambda_handler().invoke(function_name=converter_function, payload=payload, async=True)
        response = {'What?':'Did no conversion!'}
        App.logger.debug('finished.')
        return response

    def send_request_to_linter(self, job, linter, commit_url, extra_payload=None):
        """
        :param TxJob job:
        :param TxModule linter:
        :param string commit_url:
        :param dict extra_payload:
        :return bool:
        """
        payload = {
            'identifier': job.identifier,
            'resource_id': job.resource_type,
            'cdn_bucket': job.cdn_bucket,
            'cdn_file': job.cdn_file,
            'options': job.options,
            'lint_callback': self.linter_callback,
            'commit_data': self.commit_data
        }
        if extra_payload:
            payload.update(extra_payload)
        if job.input_format == 'usfm' or job.resource_type == 'obs':
            # Need to give the massaged source since it maybe was in chunks originally
            payload['source_url'] = job.source
        else:
            payload['source_url'] = commit_url.replace('commit', 'archive') + '.zip'
        return self.send_payload_to_linter(payload, linter)

    def send_payload_to_linter(self, payload, linter):
        """
        :param dict payload:
        :param TxModule linter:
        :return bool:
        """
        # TODO: Make this use urllib2 to make a async POST to the API. Currently invokes Lambda directly
        payload = {
            'data': payload,
            'vars': {
                'prefix': App.prefix
            }
        }
        linter_name = linter.name
        if not isinstance(linter_name,str): # bytes in Python3 -- not sure where it gets set
            linter_name = linter_name.decode()
        print("linter_name",repr(linter_name))
        App.logger.debug('Sending Payload to linter {0}:'.format(linter_name))
        App.logger.debug(payload)
        linter_function = '{0}tx_lint_{1}'.format(App.prefix, linter_name)
        print("send_payload_to_linter: linter_function is {!r}, payload={}".format(linter_function,payload))
        # TODO: Put an alternative function call in here RJH
        #response = App.lambda_handler().invoke(function_name=linter_function, payload=payload, async=True)
        response = {'What?':'Did no linting!'}
        App.logger.debug('finished.')
        return response

    def download_repo(self, commit_url, repo_dir):
        """
        Downloads and unzips a git repository from Github or git.door43.org

        :param str|unicode commit_url: The URL of the repository to download
        :param str|unicode repo_dir:   The directory where the downloaded file should be unzipped
        :return: None
        """
        repo_zip_url = commit_url.replace('commit', 'archive') + '.zip'
        repo_zip_file = os.path.join(self.base_temp_dir, repo_zip_url.rpartition(os.path.sep)[2])

        try:
            App.logger.debug('Downloading {0}...'.format(repo_zip_url))

            # if the file already exists, remove it, we want a fresh copy
            if os.path.isfile(repo_zip_file):
                os.remove(repo_zip_file)

            download_file(repo_zip_url, repo_zip_file)
        finally:
            App.logger.debug('finished.')

        try:
            App.logger.debug('Unzipping {0}...'.format(repo_zip_file))
            unzip(repo_zip_file, repo_dir)
        finally:
            App.logger.debug('finished.')

        # clean up the downloaded zip file
        if os.path.isfile(repo_zip_file):
            os.remove(repo_zip_file)

    def get_unique_job_id(self):
        """
        :return string:
        """
        try: job_id = hashlib.sha256(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")).hexdigest()
        except TypeError: # in Python3
            job_id = hashlib.sha256(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f").encode('utf-8')).hexdigest()
        while TxJob.get(job_id):
            try: job_id = hashlib.sha256(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")).hexdigest()
            except TypeError: # in Python3
                job_id = hashlib.sha256(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f").encode('utf-8')).hexdigest()
        return job_id

    def get_converter_module(self, job):
        """
        :param TxJob job:
        :return TxModule:
        """
        converters = TxModule.query().filter(TxModule.type=='converter') \
            .filter(TxModule.input_format.contains(job.input_format)) \
            .filter(TxModule.output_format.contains(job.output_format))
        converter = converters.filter(TxModule.resource_types.contains(job.resource_type)).first()
        if not converter:
            converter = converters.filter(TxModule.resource_types.contains('other')).first()
        return converter

    def get_linter_module(self, job):
        """
        :param TxJob job:
        :return TxModule:
        """
        linters = TxModule.query().filter(TxModule.type=='linter') \
            .filter(TxModule.input_format.contains(job.input_format))
        linter = linters.filter(TxModule.resource_types.contains(job.resource_type)).first()
        if not linter:
            linter = linters.filter(TxModule.resource_types.contains('other')).first()
        return linter

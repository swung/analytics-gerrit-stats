#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gerrit-stats: Generate codereview stats based from Gerrit commits
Copyright (C) 2012  Diederik van Liere, Wikimedia Foundation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import os
import fnmatch
import logging
import paramiko


from repo import Repo
from utils import unsuccessful_exit

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


class Gerrit(object):
    '''
    This object contains the settings to interact with the gerrit server,
    nothing fancy these are just sensible defaults. Plus the properties that
    apply to all repositories, including the queries that will be run to
    generate the statistics, a list of repositories to ignore and a set of
    engineers that do not use a WMF email address and hence will be classified
    as volunteer.
    '''
    def __init__(self, args, settings):
        self.dataset = args.datasets
        self.my_cnf = args.sql
        self.csv_location, self.yaml_location = self.init_locations()
        self.toolkit = args.toolkit
        self.ssh_username = args.ssh_username
        self.ssh_identity = args.ssh_identity
        self.ssh_password = args.ssh_password
        self.host = settings.get('host')
        self.port = settings.get('port')
        self.ignore_repos = settings.get('ignore_repos')
        self.parents = settings.get('parents')
        self.creation_date = settings.get('creation_date')
        self.repos = {}
        self.is_valid_path(self.yaml_location)
        self.is_valid_path(self.csv_location)
        self.is_valid_path(self.my_cnf)
        self.remove_old_datasets()

    def __str__(self):
        return 'Gerrit-stats general settings object.'

    def run_query(self, query):
        ssh = paramiko.SSHClient()
        #ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.host, port=self.port,
                    username=self.ssh_username,
                    key_filename=self.ssh_identity,
                    password=self.ssh_password,
                    allow_agent=False)
        except paramiko.PasswordRequiredException, e:
            logging.warning('Please specify on the command line the ssh-password parameter correctly.')
            unsuccessful_exit()
        except Exception, e:
            logging.warning('Encountered error:\n %s' % e)
            unsuccessful_exit()

        stdin, stdout, stderr = ssh.exec_command(query)
        data = stdout.readlines()
        try:
            error = stderr.readlines()
        except IOError:
            pass

        if error:
            logging.warning('Could not retrieve list with Gerrit repositories. Error %s' % error.strip())
            unsuccessful_exit()
        return data

    def init_locations(self):
        csv = os.path.join(self.dataset, 'datafiles')
        yaml = os.path.join(self.dataset, 'datasources')
        return csv, yaml

    def walk_directory(self, folder, pattern):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.join(root, filename)

    def remove_old_datasets(self):
        sources = [self.csv_location, self.yaml_location]
        for source in sources:
            for filename in self.walk_directory(source, '*.*'):
                logging.info('Removing %s...' % (
                    os.path.join(source, filename)))
                try:
                    os.unlink(filename)
                except OSError, e:
                    logging.warning('Failed to remove %s but get error %s' % (os.path.join(source, filename), e))
                    unsuccessful_exit()
            logging.info('Successfully removed %s' % source)

    def is_valid_path(self, path):
        if path.startswith('~'):
            path = os.path.expanduser(path)
        if os.path.isabs(path) is False:
            logging.warning('%s is not an absolute path, please specify an existing absolute path.' % path)
            unsuccessful_exit()
        elif os.path.exists(path) is False:
            logging.warning('%s does not exist, make sure that the file exists.' % path)
            unsuccessful_exit()
        else:
            logging.info('%s is a valid path.' % path)

    def fetch_repos(self):
        logging.info('Fetching list of all Gerrit repositories')
        repos_list = self.list_repos()
        for repo in repos_list:
            if repo.find('wikimedia/orgchart') > -1:
                pass
            try:
                repo, description = repo.split(' - ')
            except ValueError:
                description = 'Description is missing.'

            repo = repo.strip()
            description = description.strip()

            tests = [repo.startswith(ignore_repo)
                     is False for ignore_repo in self.ignore_repos]
            if all(tests):
                rp = Repo(repo, description, self)
                self.repos[rp.name] = rp

        for repo in self.parents:
            if repo['name'] not in self.repos:
                self.repos[repo['name']] = Repo(repo['name'],
                                                repo['description'], self, is_parent=True)

    def list_repos(self):
        query = 'gerrit ls-projects -d'
        repos = self.run_query(query)
        return repos

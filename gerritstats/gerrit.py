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
import sys
import logging

from query import Query
from repo import Repo

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


class Gerrit(object):
    '''
    This object contains the settings to interact with the gerrit server, nothing fancy these are just
    sensible defaults. Plus the properties that apply to all repositories, including the queries that will be
    run to generate the statistics, a list of repositories to ignore and a set of engineers that do not use
    a WMF email address and hence will be classified as volunteer.
    '''
    def __init__(self, args):
        self.dataset = args.datasets
        self.my_cnf = args.config
        self.csv_location, self.yaml_location = self.init_locations()
        self.host = 'gerrit.wikimedia.org'
        self.port = 29418
        self.format = 'JSON'
        self.recreate = args.recreate
        self.toolkit = args.toolkit
        self.ssh_username = args.ssh_username
        self.repos = {}
        self.ignore_repos = ['test', 'private']
        self.parents = [
            dict(name='mediawiki',description='Aggregate statistics for the entire mediawiki code base (core, extensions, tools and packages.'),
            dict(name='mediawiki/all_extensions',description='Aggregate statistics for all extensions.'),
            dict(name='mediawiki/wmf_extensions', description='Aggregate statistics for extensions run by WMF.'),
            dict(name='mediawiki/core_wmf_extensions', description='Aggregate statistics for extensions run by WMF and Mediawiki Core.'),
            dict(name='operations',description='Aggregate statistics for all operations repositories.'),
            dict(name='analytics',description='Aggregate statistics for all analytics repositories.'),
            dict(name='integration',description='Aggregate statistics for all integration repositories.'),
            dict(name='labs',description='Aggregate statistics for all labs repositories.'),
            dict(name='translatewiki',description='Aggregate statistics for all translatewiki repositories.'),
            dict(name='wikimedia',description='Aggregate statistics for all wikimedia repositories.'),
        ]
        self.is_valid_path(self.yaml_location)
        self.is_valid_path(self.csv_location)
        self.is_valid_path(self.my_cnf)
        self.remove_old_datasets()

    def __str__(self):
        return 'Gerrit-stats general settings object.'
    
    def init_locations(self):
        csv = os.path.join(self.dataset, 'datafiles')
        yaml = os.path.join(self.dataset, 'datasources')
        return csv, yaml

    def walk_directory(self, folder, pattern):
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.join(root, filename)

    def remove_old_datasets(self):
        if self.recreate:
            sources = ['data/datafiles', 'data/datasources']
            try:
                for source in sources:
                    for filename in self.walk_directory(source, '*.*'):
                        os.unlink(filename)
                    logging.info('Successfully removed %s' % source)
                #shutil.rmtree('data/datafiles')
                #shutil.rmtree('data/datasources')
            except OSError, e:
                logging.warning('Trying to remove %s but get error %s' % (source, e))
                logging.error('Leaving gerrit-stats unsuccesfully.')
                sys.exit(-1)

    def is_valid_path(self, path):
        if path.startswith('~'):
            path = os.path.expanduser(path)
        if os.path.isabs(path) == False:
            raise Exception("Please specify an absolute path.")
            sys.exit(-1)
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
            
            tests = [repo.startswith(ignore_repo) == False for ignore_repo in self.ignore_repos]
            if all(tests):
                rp = Repo(repo, description, self)
                self.repos[rp.name] = rp
        
        for repo in self.parents:
            if repo['name'] not in self.repos:
                self.repos[repo['name']] = Repo(repo['name'], repo['description'], self, is_parent=True)

    def list_repos(self):
        list_repo_query = {
                           'name':'list_repos', 
                           'query': 'gerrit ls-projects -d', 
                           'method': 'ssh', 
                           'support_json': False, 
                           }
        query = Query(gerrit=self, **list_repo_query)
        return query.launch()

            
    

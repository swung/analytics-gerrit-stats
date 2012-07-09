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
import shutil
import sys
import logging

from query import Query
from repo import Repo


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

#fh = logging.FileHandler('logs/gerrit-stats.txt')

class Gerrit(object):
    '''
    This object contains the settings to interact with the gerrit server, nothing fancy these are just
    sensible defaults. Plus the properties that apply to all repositories, including the queries that will be
    run to generate the statistics, a list of repositories to ignore and a set of engineers that do not use
    a WMF email address and hence will be classified as volunteer.
    '''
    def __init__(self, args):
        self.dataset = args.datasets
        #self.log_location = args.log
        self.csv_location, self.yaml_location = self.init_locations()
        self.host = 'gerrit.wikimedia.org'
        self.port = 29418
        self.format = 'JSON'
        self.recreate = args.recreate
        self.toolkit = args.toolkit
        self.repos = {}
        self.is_valid_path(self.yaml_location)
        self.is_valid_path(self.csv_location)
        #self.is_valid_path(self.log_location)

        self.ignore_repos = ['test', 'operations/private']
        self.parents = [
            'mediawiki/core',
            'mediawiki/extensions',
            'operations',
            'analytics',
        ]

        self.remove_old_datasets()
        self.fetch_repos()

    def __str__(self):
        return 'Gerrit-stats general settings object.'
    
    def init_locations(self):
        csv = os.path.join(self.dataset, 'datafiles')
        yaml = os.path.join(self.dataset, 'datasources')
        return csv, yaml


    def remove_old_datasets(self):
        if self.recreate:
            try:
                shutil.rmtree('data/datafiles')
                shutil.rmtree('data/datasources')
            except OSError:
                pass
            logging.info('Succesfully removed data/datafiles/ and data/datasources/.')

    def is_valid_path(self, path):
        if os.path.isabs(path) == False:
            raise Exception("Please specify an absolute path.")
            sys.exit(-1)
            

    def fetch_repos(self):
        logging.info('Fetching list of all Gerrit repositories')
        repos_list = self.list_repos()
        repos_list = repos_list.strip()
        repos_list = repos_list.split('\n')
        for repo in repos_list:
            if repo.find('wikimedia/orgchart') > -1:
                #print 'debug'
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


    def list_repos(self):
        list_repo_query = {
                           'name':'list_repos', 
                           'raw_query': 'ls-projects -d', 
                           'method': 'ssh', 
                           'support_json': False, 
                           'model': None, 
                           'handler': 'parse_json', 
                           'debug': True, 
                           'recreate':True,
                           'headings': None,
                           }
        query = Query(self, **list_repo_query)
        return query.launch()
    
#    def init_repo_queries(self):
#        if not self.recreate:
#            per_repo_queries =[
#                           {
#                            'name':'only+1', 
#                            'raw_query':'-- CodeReview+1 -CodeReview+2 -CodeReview-1 -CodeReview-2',
#                            'method':'ssh', 
#                            'support_json': True, 
#                            'model': None, 
#                            'handler': 'parse_json', 
#                            'debug': True, 
#                            'recreate': False,
#                            'headings': ['count','staff_count', 'wikipedian_count'],
#                            },
#                           
#                           {
#                            'name':'no_review',
#                            'raw_query': '-- -CodeReview+1 -CodeReview-1 -CodeReview+2 -CodeReview-2', 
#                            'method':'ssh', 
#                            'support_json': True, 
#                            'model': None, 
#                            'handler': 'parse_json', 
#                            'debug': True, 
#                            'recreate': False,  
#                            'headings': ['count','staff_count', 'wikipedian_count'],
#                            },
#                               
#                           {
#                            'name':'self_review',
#                            'raw_query': '', 
#                            'method': 'sql', 
#                            'support_json': True, 
#                            'model': None, 
#                            'handler': 'parse_json', 
#                            'debug': True, 
#                            'recreate': False, 
#                            'headings': ['count'],
#                            },
#                               
#                           {
#                            'name':'daily_commits',
#                            'raw_query':'select revision, patch_sets.created_on, dest_project_name from patch_sets INNER JOIN changes ON patch_sets.change_id = changes.change_id where patch_sets.created_on >= CURRENT_DATE();', 
#                            'method':'sql', 
#                            'support_json': False, 
#                            'model': None, 
#                            'handler': 'parse_json', 
#                            'debug': True, 
#                            'recreate': False,
#                            'headers': ['count','staff_count', 'wikipedian_count'],
#                            },
#                           ]
#            
#        if self.recreate:
#            per_repo_queries =[
#                           {'name':'only+1', 
#                            'raw_query':'''SELECT 
#                                                changes.change_id, 
#                                                changes.dest_project_name, 
#                                                changes.owner_account_id, 
#                                                changes.created_on, 
#                                                MIN(patch_set_approvals.granted) AS granted_on, 
#                                                patch_set_approvals.value, 
#                                                patch_set_approvals.account_id 
#                                            FROM 
#                                                changes
#                                            LEFT JOIN 
#                                                patch_set_approvals 
#                                            ON 
#                                                changes.change_id=patch_set_approvals.change_id 
#                                            WHERE 
#                                                patch_set_approvals.value=1 
#                                            GROUP BY
#                                                patch_set_approvals.change_id
#                                            ORDER BY 
#                                                created_on;''',
#                            'method':'sql',
#                            'support_json': False,
#                            'model': Changes,
#                            'handler': 'parse_results_only_1',
#                            'debug': True,
#                            'recreate': True,
#                            'headings': ['count','staff_count', 'wikipedian_count'],
#                            },
#                           
#                           {'name':'no_review',
#                            'raw_query': '''SELECT 
#                                                changes.change_id, 
#                                                changes.dest_project_name, 
#                                                changes.owner_account_id, 
#                                                changes.created_on, 
#                                                patch_set_approvals.granted, 
#                                                patch_set_approvals.value, 
#                                                patch_set_approvals.account_id, 
#                                                changes.status 
#                                            FROM 
#                                                changes 
#                                            LEFT JOIN 
#                                                patch_set_approvals 
#                                            ON 
#                                                changes.change_id=patch_set_approvals.change_id 
#                                            WHERE 
#                                                status !='A' -- EXCLUDE ABANDONDED CHANGE_SETS
#                                            AND
#                                                status !='M' -- EXCLUDED MERGED CHANGE_SETS
#                                            AND NOT EXISTS 
#                                                (SELECT * FROM changes WHERE change_id = patch_set_approvals.change_id) 
#                                            ORDER BY 
#                                                created_on;''', 
#                            'method':'sql',
#                            'support_json': False,
#                            'model': Changes,
#                            'handler': 'parse_results_no_review',
#                            'debug': True,
#                            'recreate': True,
#                            'headings': ['count','staff_count', 'wikipedian_count'],
#                            },
#                           #{'name':'self_review','raw_query': '', 'method': 'sql'},
#                           {
#                            'name':'daily_commits',
#                            'raw_query': '''SELECT 
#                                                changes.dest_project_name, 
#                                                changes.created_on, 
#                                                COUNT(changes.change_id) 
#                                            AS 
#                                                commits 
#                                            FROM 
#                                                changes 
#                                            WHERE 
#                                                DATE(changes.created_on) >= DATE('2009-09-07') 
#                                            AND 
#                                                DATE(changes.created_on) <= DATE('2014-12-31')
#                                            GROUP BY
#                                                DATE(changes.created_on),
#                                                changes.dest_project_name 
#                                            ORDER BY changes.created_on''', 
#                            'method': 'sql',
#                            'support_json': False,
#                            'model': Changes,
#                            'handler':'parse_results_daily_commits',
#                            'debug': True,
#                            'recreate': True,
#                            'headings': ['count'],
#                            },
#                            {
#                             'name':'only+2',
#                             'raw_query': '''SELECT 
#                                                changes.change_id, 
#                                                changes.dest_project_name, 
#                                                changes.owner_account_id, 
#                                                changes.created_on, 
#                                                patch_set_approvals.granted AS granted_on, 
#                                                patch_set_approvals.value, 
#                                                patch_set_approvals.account_id 
#                                            FROM 
#                                                changes 
#                                            INNER JOIN 
#                                                patch_set_approvals 
#                                            ON 
#                                                changes.change_id=patch_set_approvals.change_id 
#                                            WHERE 
#                                                value=2 
#                                            ORDER BY 
#                                                created_on;''',
#                            'method':'sql',
#                            'support_json': False,
#                            'model': Changes,
#                            'handler': 'parse_results_only_1',
#                            'debug': True,
#                            'recreate': True,
#                            'headings': ['count','staff_count', 'wikipedian_count'],
#                             },
#                           ] 
#        for query in per_repo_queries:
#            self.metrics[query.get('name')] = Query(self, **query)
            
    

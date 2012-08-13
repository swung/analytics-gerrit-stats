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
import sys
import argparse
import MySQLdb, MySQLdb.cursors, _mysql_exceptions
import cPickle
import logging

from datetime import datetime, date, timedelta
from copy import deepcopy

from gerrit import Gerrit
from commit import Review, Commit, Patchset
from sql_queries import GERRIT_CREATION_DATE, approvals_query, changes_query, patch_sets_query

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

try: 
    ch = logging.StreamHandler(strm=sys.stdout)
except TypeError:
    ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


def init_db(my_cnf):
    try:
        db = MySQLdb.connect(read_default_file=my_cnf)
        cur = db.cursor(MySQLdb.cursors.DictCursor)
        logging.info('Successfully obtained database cursor.')
    except _mysql_exceptions.OperationalError, error:
        logging.warning('Could *NOT* obtain database cursor. Error: %s' % error)
        unsuccessfull_exit()
    return cur 


def load_commit_data(cur, commits):
    try:
        cur.execute(changes_query)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    changes = cur.fetchall()
    logging.info('Successfully loaded commit data from database.')
    for change in changes:
        commit = Commit(**change)
        commits[commit.change_id] = commit
    
    return commits


def load_review_data(cur, commits):
    try:
        cur.execute(approvals_query)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    approvals = cur.fetchall()
    logging.info('Successfully loaded approval data from database.')
    for approval in approvals:
        review = Review(**approval)
        #drop bot reviewers and drop reviews with +0 (this is a hack to make it more compatible with gerrit search quagmire)
        if review.reviewer.human == True and review.value != 0:
            commit = commits.get(review.change_id)
            if commit:
                commit.patch_sets[review.patch_set_id].reviews['%s_%s' % (review.granted, review.value)] = review
            else:
                logging.info('Could not find a commit that belongs to change_id: %s written by %s (%s) on %s' % (review.change_id, review.reviewer.full_name, review.reviewer.account_id, review.granted))
    return commits
    

def load_patch_set_data(cur, commits):
    try:
        cur.execute(patch_sets_query)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    patch_sets = cur.fetchall()
    logging.info('Successfully loaded patch_sets data from database.')
    for patch_set in patch_sets:
        patch_set = Patchset(**patch_set)
        commit = commits.get(patch_set.change_id)
        if commit:
            commit.patch_sets[patch_set.patch_set_id] = patch_set
        else:
            logging.info('Could not find a commit that belongs to patch_set_id: %s written by %s on %s' % (patch_set.change_id, patch_set.uploader_account_id, patch_set.created_on))
    return commits


def create_aggregate_dataset(gerrit):
    logging.info('Creating datasets for parent repositories.')
    for name, repo in gerrit.repos.iteritems():
        if repo.is_parent == False:
            for parent in repo.parent_repos:
                parent_repo = gerrit.repos.get(parent)
                if parent_repo:
                    if parent_repo.name == repo.name:
                        logging.warning('Parent == child: %s: %s' % (parent_repo.name, repo.name))
                        unsuccessfull_exit()
                    gerrit.repos[parent_repo.name] = merge(parent_repo, repo)
                else:
                    logging.warn('Parent repo %s does not exist, while repo %s expects there to be a parent repo.' % (parent, name))
    return gerrit


def merge(parent_repo, repo):
    for date, obs in repo.observations.iteritems():
        if date.year == 2012 and date.month==8 and date.day == 12:
            print 'break'
        if date not in parent_repo.observations:
            parent_repo.observations[date] = deepcopy(obs)
        else:
            for key, value in obs.iteritems():
                parent_repo.observations[date] = parent_repo.observations[date].update(key, value)
    return parent_repo


def parse_commandline():
    parser = argparse.ArgumentParser(description='Welcome to gerrit-stats. The mysql credentials should be stored in the .my.cnf file. By default, this file is read from the user\'s home directory. You can specify an alternative location using the --config option.')
    parser.add_argument('--config', help='Specify the absolute path to tell gerrit-stats where it can find the MySQL my.cnf file.', action='store', required=False, default='~/.my.cnf')
    parser.add_argument('--datasets', help='Specify the absolute path to store the gerrit-stats datasets.', required=True)
    parser.add_argument('--toolkit', help='Specify the visualization library you want to use. Valid choices are: dygraphs and d3.', action='store', default='d3')
    parser.add_argument('--ssh-username', help='Specify your SSH username if your username on your local box dev is different then the one you use on the remote box.', action='store', required=False)
    parser.add_argument('--ssh-identity', help='Specify the location of your SSH private key.', action='store', required=False)
    return parser.parse_args()


def successful_exit():
    logging.info('Closing down gerrit-stats, no errors.')
    logging.info('Mission accomplished, beanz have been counted.')


def unsuccessfull_exit():
    logging.error('Gerrit-stats exited unsuccessfully, please look at the logs for hints on how to fix the problem.')
    logging.error('If the problem remains, contact Diederik van Liere <dvanliere@wikimedia.org>')
    sys.exit(-1)   


def main():
    logging.info('Launching gerrit-stats')
    
    args = parse_commandline()
    logging.info('Parsed commandline successfully.')
    
    gerrit = Gerrit(args)
    cur = init_db(gerrit.my_cnf)
    gerrit.fetch_repos()
    
    start_date = GERRIT_CREATION_DATE
    yesterday = date.today() - timedelta(days=1)
    commits = {}
    
    logging.info('Queries will span timeframe: %s - %s.' % (start_date, yesterday))
    logging.info('Queries will always run up to \'yesterday\', so that we always have counts for full days.')

    commits = load_commit_data(cur, commits)
    commits = load_patch_set_data(cur, commits)
    commits = load_review_data(cur, commits)
    
    for commit in commits.itervalues():
#        if commit.change_id == 10127 or commit.change_id == 10125 or commit.change_id == 9654 or commit.change_id == 9549 or commit.change_id == 9420 or commit.change_id == 9273 or commit.change_id == 9259 or commit.change_id == 9141 or commit.change_id ==  8937 or commit.change_id == 8928 or commit.change_id == 8728 or commit.change_id == 7608 or commit.change_id == 7149 or commit.change_id == 10129: # or commit.change_id == 4658:
        if commit.change_id ==7826:
            print commit
        commit.is_all_positive_reviews()
        commit.calculate_wait_first_review()
        commit.calculate_wait_plus2()
        commit.is_self_reviewed()
        
        repo = gerrit.repos.get(commit.dest_project_name)
        if repo:
            repo.increment(commit)
        else:
            logging.info('Repo %s does not exist, ignored repos are: %s' % (commit.dest_project_name, gerrit.ignore_repos))
    
    logging.info('Successfully parsed commit data.')
    # create datasets that are collections of repositories
    create_aggregate_dataset(gerrit)        
    
    for repo in gerrit.repos.itervalues():
        if repo.name == 'mediawiki':
            dates = repo.observations.keys()
            dates.sort()
            for dt in dates:
                print dt, repo.observations[dt].commit_ids
        repo.fill_in_missing_days()
        repo.create_headings()
        repo.prune_observations()
        repo.write_dataset(gerrit)    
    
    # save results for future use.
    successful_exit()

if __name__== '__main__':
    main()

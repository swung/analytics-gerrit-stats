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
from commit import Review, Commit
from settings import GERRIT_CREATION_DATE, approvals_query, changes_query

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)


def create_aggregate_dataset(gerrit):
    logging.info('Creating datasets for parent repositories.')
    for name, repo in gerrit.repos.iteritems():
        if repo.is_parent == False:
            for parent in repo.parent_repos:
                parent_repo = gerrit.repos.get(parent)
                if parent_repo:
                    if parent_repo.name == repo.name:
                        
                        print 'Parent == child: %s: %s' % (parent_repo.name, repo.name)
                        sys.exit(-1)
                    gerrit.repos[parent_repo.name] = merge(parent_repo, repo)
                else:
                    logging.warn('Parent repo %s does not exist, while repo %s expects there to be a parent repo.' % (parent, name))
    return gerrit


def create_path(location, filename):
    return os.path.join(location, filename)


def init_db(my_cnf):
    try:
        db = MySQLdb.connect(read_default_file=my_cnf)
        cur = db.cursor(MySQLdb.cursors.DictCursor)
        logging.info('Obtained database cursor.')
    except _mysql_exceptions.OperationalError, error:
        logging.warning('Could *NOT* obtain database cursor. Error: %s' % error)
        unsuccessfull_exit()
    return cur 


def load(location, filename):
    path = create_path(location, filename)
    if os.path.exists(path):
        fh = open(path, 'rb')
        obj = cPickle.load(fh)
        fh.close()
        logging.info('Successfully loaded %s.' % path)
    else:
        logging.warning('There is possibly a problem: gerrit-stats was able to detect that a previous was carried out but could not load commits.bin.')
        logging.warning('It is probably best to delete the file last_run.txt and start gerrit-stats again.')
        unsuccessfull_exit()
    return obj


def load_previous_results(location, start_date):
    commits = {}
    if start_date == GERRIT_CREATION_DATE:
        logging.info('Did *NOT* load commits.bin, this means we run against the entire gerrit history.')
        return commits
    else:
        filename = 'commits.bin'
        commits = load(location, filename)
    return commits


def merge(parent_repo, repo):
    for date, obs in repo.observations.iteritems():
        if date not in parent_repo.observations:
            parent_repo.observations[date] = deepcopy(obs)
        else:
            for key, value in obs.iteritems():
                parent_repo.observations[date].update(key, value)
    return parent_repo


def parse_commandline():
    parser = argparse.ArgumentParser(description='Welcome to gerrit-stats. The mysql credentials should be stored in the .my.cnf file. By default, this file is read from the user\'s home directory. You can specify an alternative location using the --config option.')
    parser.add_argument('--config', help='Specify the absolute path to tell gerrit-stats where it can find the MySQL my.cnf file.', action='store', required=False, default='~/.my.cnf')
    parser.add_argument('--datasets', help='Specify the absolute path to store the gerrit-stats datasets.', required=True)
    parser.add_argument('--recreate', help='Delete all existing datafiles and datasources and recreate them from scratch. This needs to be done whenever a new metric is added.', action='store_true', default=False)
    parser.add_argument('--toolkit', help='Specify the visualization library you want to use. Valid choices are: dygraphs and d3.', action='store', default='d3')
    parser.add_argument('--ssh-username', help='Specify your SSH username if your username on your local box dev is different then the one you use on the remote box.', action='store', required=False)
    return parser.parse_args()


def read_last_run(location):
    path = create_path(location, 'last_run.txt')
    try:
        fh = open(path, 'r')
        start_date = datetime.strptime(fh.readline(), '%Y-%m-%d')
        fh.close()
    except IOError:
        start_date = GERRIT_CREATION_DATE
    return start_date

            
def save(location, filename, obj):
    path = create_path(location, filename)
    fh = open(path, 'wb')
    cPickle.dump(obj, fh)
    fh.close()
    logging.info('Successfully saved %s.' % path)
    
    
def write_last_run(start_date, location):
    filename = 'last_run.txt'
    path = create_path(location, filename)
    fh = open(path,'w')
    fh.write('%s-%s-%s' % (start_date.year, start_date.month, start_date.day))
    fh.close()
    logging.info('Successfully wrote %s.' % path)

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
    
    yesterday = date.today() - timedelta(days=1)
    if args.recreate:
        commits = {}
        start_date = GERRIT_CREATION_DATE
    else:
        start_date = read_last_run(gerrit.dataset)
        commits = load_previous_results(gerrit.dataset, start_date)
    
    logging.info('Queries will span timeframe: %s - %s.' % (start_date, yesterday))
    logging.info('Queries will always run up to \'yesterday\', so that we always have counts for full days.')

    args = (start_date, yesterday)
    try:
        cur.execute(changes_query, args)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    changes = cur.fetchall()
    logging.info('Successfully loaded commit data from database.')
    for change in changes:
        commit = Commit(**change)
        commits[commit.change_id] = commit
    
    cur.execute(approvals_query, args)
    approvals = cur.fetchall()
    logging.info('Successfully loaded approval data from database.')
    for approval in approvals:
        review = Review(**approval)
        #drop bot reviewers
        if review.reviewer.human == True:
            commit = commits.get(review.change_id)
            if commit:
                commit.reviews['%s-%s' % (review.granted, review.value)] = review # review.granted by itself is not guaranteed to be unique.
            else:
                logging.info('Could not find a commit that belongs to change_id: %s written by %s (%s) on %s' % (review.change_id, review.reviewer.full_name, review.reviewer.account_id, review.granted))
                
    
    for commit in commits.itervalues():
        commit.is_all_positive_reviews()
        commit.calculate_wait()
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
        repo.fill_in_missing_days()
        repo.create_headings()
        repo.prune_observations()
        repo.write_dataset(gerrit)    
    
    # save results for future use.
    save(gerrit.dataset, 'commits.bin', commits)
    write_last_run(yesterday, gerrit.dataset)
    successful_exit()

if __name__== '__main__':
    main()

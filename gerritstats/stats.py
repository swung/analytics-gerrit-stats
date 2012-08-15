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

import sys
import argparse
import MySQLdb, MySQLdb.cursors, _mysql_exceptions
import logging

from datetime import datetime, date, timedelta
from copy import deepcopy

from gerrit import Gerrit
from changeset import Review, Changeset, Patchset
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


def load_commit_data(cur, changesets):
    try:
        cur.execute(changes_query)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    changesets_raw = cur.fetchall()
    logging.info('Successfully loaded changeset data from database.')
    for changeset in changesets_raw:
        changeset = Changeset(**changeset)
        changesets[changeset.change_id] = changeset
    
    return changesets


def load_review_data(cur, changesets):
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
            changeset = changesets.get(review.change_id)
            if changeset:
                changeset.patch_sets[review.patch_set_id].reviews['%s_%s' % (review.granted, review.value)] = review
            else:
                logging.info('Could not find a commit that belongs to change_id: %s written by %s (%s) on %s' % (review.change_id, review.reviewer.full_name, review.reviewer.account_id, review.granted))
    return changesets
    

def load_patch_set_data(cur, changesets):
    try:
        cur.execute(patch_sets_query)
    except _mysql_exceptions.ProgrammingError, e:
        logging.warning('Encountered problem while running db operation: %s' % e)
        unsuccessfull_exit()
    
    patch_sets = cur.fetchall()
    logging.info('Successfully loaded patch_sets data from database.')
    for patch_set in patch_sets:
        patch_set = Patchset(**patch_set)
        changeset = changesets.get(patch_set.change_id)
        if changeset:
            changeset.patch_sets[patch_set.patch_set_id] = patch_set
        else:
            logging.info('Could not find a commit that belongs to patch_set_id: %s written by %s on %s' % (patch_set.change_id, patch_set.uploader_account_id, patch_set.created_on))
    return changesets


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
    parser.add_argument('--ssh-password', help='Specify the password of the SSH private key (optional)', action='store', required=False)
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
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    changesets = {}
    
    logging.info('Queries will span timeframe: %s - %s.' % (start_date, yesterday))
    logging.info('Queries will always run up to \'yesterday\', so that we always have counts for full days.')

    changesets = load_commit_data(cur, changesets)
    changesets = load_patch_set_data(cur, changesets)
    changesets = load_review_data(cur, changesets)
    
    for changeset in changesets.itervalues():
        if changeset.change_id == 3291:
            print 'break'
        changeset.is_all_positive_reviews()
        changeset.calculate_wait_first_review()
        changeset.calculate_wait_plus2()
        changeset.is_self_reviewed()
        
        repo = gerrit.repos.get(changeset.dest_project_name)
        if repo:
            repo.increment(changeset)
        else:
            logging.info('Repo %s does not exist, ignored repos are: %s' % (changeset.dest_project_name, ','.join(gerrit.ignore_repos)))
    
    logging.info('Successfully parsed changesets data.')
    # create datasets that are collections of repositories
    create_aggregate_dataset(gerrit)        
    
    for repo in gerrit.repos.itervalues():
        if repo.name == 'mediawiki':
            dt = date(2012,8,12)
            change_ids = list(repo.observations[dt].changeset_ids)
            change_ids.sort()
            for change_id in change_ids:
                print change_id
                #print dt, repo.observations[dt].commit_ids
        repo.fill_in_missing_days()
        repo.create_headings()
        repo.prune_observations()
        repo.write_dataset(gerrit)    
    
    # save results for future use.
    successful_exit()

if __name__== '__main__':
    main()

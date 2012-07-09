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
import cPickle
import logging

import os.path as path
from datetime import datetime, date, timedelta

from gerrit import Gerrit
from commit import Review, Commit
from settings import settings, GERRIT_CREATION_DATE, approvals_query, changes_query

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('logs/gerrit-stats.txt')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)



def create_aggregate_dataset(repos):
    logging.info('Creating datasets for parent repositories.')
    for name, repo in repos.iteritems():
        if repo.parent:
            parent_repo = repos.get(repo.parent)
            if parent_repo:
                repos[parent_repo.name] = merge(parent_repo, repo) 
    return repos


def init_db():
    try:
        db = MySQLdb.connect(host=settings.get('host'), db=settings.get('database'), passwd=settings.get('passwd'), user=settings.get('user'))
        cur = db.cursor(MySQLdb.cursors.DictCursor)
        logging.info('Obtained database cursor.')
    except _mysql_exceptions.OperationalError, error:
        logging.warning('Could *NOT* obtain database cursor. Error: %s' % error)
 	sys.exit(-1)   
    return cur 


def load(obj):
    filename = '%s.bin' % obj
    fh = open(filename, 'rb')
    obj = cPickle.load(fh)
    fh.close()
    logging.info('Successfully loaded %s.' % filename)
    return obj


def load_previous_results(start_date):
    commits = {}
    if start_date == GERRIT_CREATION_DATE:
        logging.info('Did *NOT* load commits.bin, this means we run against the entire gerrit history.')
        return commits
    else:
        filename = 'commits.bin'
        if path.exists(filename):
            commits = load(filename)
        logging.info('Succesfully loaded commits.bin')
    return commits

def merge(parent_repo, repo):
    for date, obs in repo.observations.iteritems():
        if date not in parent_repo.observations:
            parent_repo.observations[date] = obs
        else:
            for key, value in obs.iteritems():
                parent_repo.observations[date].update(key, value)
    return parent_repo


def parse_commandline():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--datasets', help='Specify the absolute path to store the gerrit-stats datasets.', required=True)
    parser.add_argument('--log', help='Specify the absolute path to store the log files.', required=True)
    parser.add_argument('--recreate', help='Delete all existing datafiles and datasources and recreate them from scratch. This needs to be done whenever a new metric is added.', action='store_true', default=False)
    parser.add_argument('--toolkit', help='Specify the visualization library you want to use. Valid choices are: dygraphs and d3.', action='store', default='d3')
    return parser.parse_args()


def read_last_run():
    try:
        fh = open('last_run.txt','r')
        start_date = datetime.strptime(fh.readline(), '%Y-%m-%d')
        fh.close()
    except IOError:
        start_date = GERRIT_CREATION_DATE
    return start_date

            
def save(filename, obj):
    filename = '%s.bin' %  filename
    fh = open(filename, 'wb')
    cPickle.dump(obj, fh)
    fh.close()
    logging.info('Successfully saved %s.' % filename)
    
    
def write_last_run(start_date):
    filename = 'last_run.txt'
    fh = open(filename,'w')
    fh.write('%s-%s-%s' % (start_date.year, start_date.month, start_date.day))
    fh.close()
    logging.info('Successfully wrote %s.' % filename)
 

def main():
    logging.info('Launching gerrit-stats')
    
    args = parse_commandline()
    logging.info('Parsed commandline successfully.')
    
    gerrit = Gerrit(args)
    cur = init_db()
    
    yesterday = date.today() - timedelta(days=1)
    if not args.recreate:
        start_date = read_last_run()
        commits = load_previous_results(start_date)
    else:
        commits = {}
        start_date = GERRIT_CREATION_DATE
    

    args = (start_date, yesterday)
    cur.execute(changes_query, args)
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
        commit = commits.get(review.change_id)
        if commit:
            commit.reviews['%s-%s' % (review.granted, review.value)] = review # review.granted by itself is not guaranteed to be unique.
        else:
            logging.info('Could not find a commit that belongs to change_id: %s written by %s (%s) on %s' % (review.change_id, review.reviewer.full_name, review.reviewer.account_id, review.granted))
                
    
    for commit in commits.itervalues():
        commit.is_all_positive_reviews()
        commit.is_self_reviewed()
        commit.calculate_wait()
        
#        if commit.status != 'n':
#            if commit.time_first_review.date() == date.today() or commit.time_plus2 == date.today():
#                for review in commit.reviews.itervalues():
#                    print review.granted, review.value
        
        repo = gerrit.repos.get(commit.dest_project_name)
        if repo:
            repo.increment(commit)
        else:
            logging.info('Repo %s does not exist, ignored repos are: %s' % (commit.dest_project_name, gerrit.ignore_repos))
    
    logging.info('Successfully parsed commit data.')
    # create datasets that are collections of repositories
    create_aggregate_dataset(gerrit.repos)        
    
    for repo in gerrit.repos.itervalues():
        repo.fill_in_missing_days()
        repo.create_headings()
        repo.prune_observations()
        repo.write_dataset(gerrit)    
    
    # save results for future use.
    save('commits', commits)
    write_last_run(start_date)
    logging.info('Closing down gerrit-stats, no errors.')
    logging.info('Mission accomplished, beanz have been counted.')

if __name__== '__main__':
    main()

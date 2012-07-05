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

import json
import argparse
import MySQLdb, MySQLdb.cursors


from gerrit import Gerrit
from commit import Review, Commit
from repo import Observation

from datetime import date
def merge(d1, d2, helper=lambda x,y:x+y):
    """
    Inspired from: http://stackoverflow.com/a/44512/55281
    Merges two dictionaries, non-destructively, combining 
    values on duplicate keys as defined by the optional merge
    function.  The default behavior replaces the values in d1
    with corresponding values in d2.  (There is no other generally
    applicable merge strategy, but often you'll have homogeneous 
    types in your dicts, so specifying a merge technique can be 
    valuable.)

    Examples:

    >>> d1
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1)
    {'a': 1, 'c': 3, 'b': 2}
    >>> merge(d1, d1, lambda x,y: x+y)
    {'a': 2, 'c': 6, 'b': 4}

    """
    result = dict(d1)
    for k,v in d2.iteritems():
        if type(v) == dict:
            if k in result:
                result[k] = merge(v, result[k])
            else:
                result[k] = v
        else:
            if k in result:
                result[k] = helper(result[k], v)
            else:
                result[k] = v
    return result


def parse_json(output):
    output = output.split('\n')
    data = []
    for obs in output:
        try:
            data.append(json.loads(obs))
        except ValueError, e:
            print e
    return data
            
#def get_repo(data):
#    if isinstance(data, dict) and 'rowCount' not in data:
#        try:
#            return data['project']
#        except KeyError, e:
#            print e, data
#            return None
#
#def parse_results_no_review(repos, output, query):
#    return repos
#
#def parse_results_only_1(repos, output, query):
#    for obj in output:
#        repo = repos.get(obj.dest_project_name)
#        if repo:
#            if query.debug:
#                pass
#                #print '%s\t%s\t%s' % (repo.name, obj.created_on, obj.value)
#                #if len(repo.dataset_headings.keys()) ==1:
#                #print repo.name, len(repo.dataset_headings.keys()), repo.dataset_headings
#            
#            created = repo.construct_day_key(obj.created_on)
#            if query.recreate and created not in repo.dataset:
#                continue
#            #elif not query.recreate:
#            #    repo.dataset.setdefault(created, {})
#            email = repo.gerrit.developers.get(obj.account_id)
#            for day in repo.daterange(obj.created_on, obj.granted_on):
#                day = repo.construct_day_key(day)
#                repo.dataset[day]['touched'] = True
#                repo.dataset[day].setdefault(query.name, {})
#                repo.dataset[day][query.name].setdefault('total', 0)
#                repo.dataset[day][query.name].setdefault('wiki_count', 0)
#                repo.dataset[day][query.name].setdefault('staff_count', 0)
#                if repo.is_wikimedian(email):
#                    repo.dataset[day][query.name]['wiki_count']+=1
#                else:
#                    repo.dataset[day][query.name]['staff_count']+=1
#                repo.dataset[day][query.name]['total']+=1
#            repos[obj.dest_project_name] = repo
#    print 'Done'
#    return repos

#def parse_results_daily_commits(repos, output, query):
#    for obj in output:
#        repo = repos.get(obj.dest_project_name)
#        if repo:
#            if query.debug:
#                print '%s\t%s' % (obj.created_on, obj.commits)
#                
#            day = repo.construct_day_key(obj.created_on)
#            if day not in repo.dataset:
#                continue
#            #elif query.recreate:
#            #    repo.dataset.setdefault(day, {})
#            
#            repo.dataset[day]['touched'] = True
#            repo.dataset[day][query.name] = {}
#            repo.dataset[day][query.name]['count'] = obj.commits
#            repos[obj.dest_project_name] = repo
#    print 'Done'
#    return repos

def create_aggregate_dataset(repos):
    for repo in repos.itervalues():
        if repo.parent:
            parent_repo = repos.get(repo.parent)
            if parent_repo:
                parent_repo.dataset = merge(parent_repo.observations, repo.observations)
                repos[parent_repo.name] = parent_repo
    return repos


def main():
    args = parse_commandline()
    gerrit = Gerrit(args)
    db = MySQLdb.connect(host='localhost', db='reviewdb', passwd='mulder', user='root')
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    changes_query = '''
                    SELECT 
                        *
                    FROM
                        changes
                    INNER JOIN
                        accounts
                    ON
                        changes.owner_account_id=accounts.account_id
                    ORDER BY
                        changes.created_on;
                    '''
    
    approvals_query = '''
                    SELECT
                        *
                    FROM 
                        patch_set_approvals
                    INNER JOIN
                        accounts
                    ON 
                        patch_set_approvals.account_id=accounts.account_id
                    ORDER BY
                        patch_set_approvals.granted;
                    '''

    cur.execute(changes_query)
    changes = cur.fetchall()
    commits = {} 
    for change in changes:
        commit = Commit(**change)
        commits[commit.change_id] = commit
    
    cur.execute(approvals_query)
    approvals = cur.fetchall()
    for approval in approvals:
        review = Review(**approval)
        commit = commits.get(review.change_id)
        if commit:
            commit.reviews['%s-%s' % (review.granted, review.value)] = review # review.granted by itself is not guaranteed to be unique.
        else:
            print 'shit: %s' % review
    
    for commit in commits.itervalues():
        commit.is_all_positive_reviews()
        commit.calculate_wait()
        commit.is_self_reviewed()
#        if commit.time_first_review.date() == date.today() or commit.time_plus2 == date.today():
#            for review in commit.reviews.itervalues():
#                print review.granted, review.value
        
        repo = gerrit.repos.get(commit.dest_project_name)
        if repo:
            if repo.name == 'mediawiki/core':
                print 'debug'
            repo.increment(commit)

        
        else:
            print 'shit, repo doesnt exist: %s' % commit.dest_project_name

    #create_aggregate_dataset(gerrit.repos)        

    for repo in gerrit.repos.itervalues():
        if repo.name == 'mediawiki/core':
            print 'debug'
        repo.fill_in_missing_days()
        repo.create_headings()
        repo.prune_observations()
        repo.write_dataset(gerrit)    
        

def parse_commandline():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--datasets', help='Specify the absolute path to store the gerrit-stats datasets.', required=True)
    parser.add_argument('--recreate', help='Delete all existing datafiles and datasources and recreate them from scratch. This needs to be done whenever a new metric is added.', action='store_true', default=False)
    parser.add_argument('--verbose', help='Output intermediate results to see what\'s happening.', action='store_true', default=False)
    parser.add_argument('--toolkit', help='Specify the visualization library you want to use. Valid choices are: dygraphs and d3.', action='store', default='d3')
    return parser.parse_args()
    



if __name__== '__main__':
    main()

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
import subprocess
import json
import sys
import os
from datetime import datetime

from classes import Gerrit, Settings, Metric, Repo

def create_repo_set(gerrit, settings):
    repos = {}
    output = run_gerrit_query('ssh -p 29418 gerrit.wikimedia.org gerrit ls-projects')
    output = output.split('\n')
    for repo in output:
        repo = repo.strip()
        if len(repo) > 1:
            tests = [repo.find(ignore) == -1 for ignore in settings.ignore_repos]
            if all(tests):
                rp = Repo(repo, settings, gerrit)
                repos[rp.name] = rp
    return repos


def is_wikimedian(email, whitelist):
    if email in whitelist:
        return True
    if email.endswith('wikimedia.org'):
        return True
    else:
        return False


def set_delimiter(fields, counter):
    num_fields = len(fields)
    if num_fields-counter != 1:
        return ','
    else:
        return ''

def output_results(fh, *args):
    args = [str(arg) for arg in args]
    output = ''.join(args)
    fh.write(output)
    sys.stdout.write(output)

def write_heading(fh, repo):
    output_results(fh, 'data',',','repository',',')
    #fh.write('%s,%s,' % ('date', 'repository'))
    #sys.stdout.write('%s,%s,' % ('date', 'repository'))
    for metric_counter, (name, metric) in enumerate(repo.dataset.iteritems()):
        headings = metric.keys()
        for counter, heading in enumerate(headings):
            if metric_counter +1 == repo.num_metrics:
                delim = set_delimiter(headings, counter)
            else:
                delim = ','
            #fh.write('%s_%s%s' % (name, heading, delim))
            #sys.stdout.write('%s_%s%s' % (name, heading, delim))
            output_results(fh, name,'_', heading, delim)
    fh.write('\n')
    sys.stdout.write('\n')


def construct_timestamp(epoch):
    return datetime.fromtimestamp(epoch)


def run_gerrit_query(query):
    query = query.split(' ')
    output = subprocess.Popen(query, shell=False, stdout=subprocess.PIPE).communicate()[0]
    return output


def create_dataset(repos, gerrit):
    for key, repo in repos.iteritems():
        fh = open('%s/%s' % (gerrit.data_location, repo.filename), repo.filemode)
        if repo.filemode == 'w':
            write_heading(fh, repo)
        #sys.stdout.write('%s-%s-%s,%s,' % (repo.today.month,repo.today.day,repo.today.year, repo.name))
        #fh.write('%s-%s-%s,%s,' % (repo.today.month,repo.today.day,repo.today.year, repo.name))
        output_results(fh, repo.today.month,'-',repo.today.day,'-',repo.today.year,',',repo.name,',')
        print_dict(repo, fh)
        sys.stdout.write('\n*****************\n')
        sys.stdout.write('\n')
        fh.write('\n')
        fh.close()


def print_dict(repo, fh, ident = '', braces=1):
    """ Recursively prints nested dictionaries."""
    dataset = repo.dataset
    for metric_counter, metric in enumerate(dataset):
        fields = dataset[metric].keys()
        for counter, field in enumerate(fields):
            if metric_counter +1 == repo.num_metrics:
                delim = set_delimiter(fields, counter)
            else:
                delim = ','
            #print delim
            sys.stdout.write('%s%s' % (dataset[metric][field], delim))
            fh.write('%s%s' % (dataset[metric][field], delim))


def cleanup_volunteers(repos, whitelist):
    for name, repo in repos.iteritems():
        for ws in whitelist:
            if ws in repo.email['volunteer']:
                repo.email['wikimedian'].add(ws)
                repo.email['email']['volunteer'].remove(ws)
    return repos


def construct_dataset(settings, repos, metric, output, gerrit):
    output = output.split('\n')
    for obs in output:
        try:
            obs= json.loads(obs)
        except ValueError, e:
            print e
        
        if isinstance(obs, dict) and 'rowCount' not in obs:
            try:
                project = obs['project']
            except KeyError, e:
                print e, obs
            email = obs['owner']['email']
            repo = repos.get(project, {})
            if repo == {}:
                continue
            dt = construct_timestamp(obs['createdOn'])
            
            # print "REPO: %s" % repo
            # print "PROJECT: %s" % project
            # print "METRIC: %s" % metric
            # print "DATASET: %s" % repo.dataset
            
            if repo.dataset[metric]['oldest'] > dt:
                repo.dataset[metric]['oldest'] = dt
            repo.dataset[metric]['total'] +=1
            if is_wikimedian(email, settings.whitelist) == True:
                repo.dataset[metric]['wikimedian'] +=1
                repo.email['wikimedian'].add(email)
            else:
                repo.dataset[metric]['volunteer'] +=1
                repo.email['volunteer'].add(email)
            repo.touched = True


def main():
    gerrit = Gerrit()
    settings = Settings(gerrit)
    print 'Fetching list of all gerrit repositories...\n'
    repos = create_repo_set(gerrit, settings)
    
    for metric in settings.metrics.itervalues():
        #query = 'ssh -p %s %s gerrit query --format=%s %s' % (gerrit.port, gerrit.host, gerrit.format, question)
        output = run_gerrit_query(metric.query)
        print 'Running %s' % metric.query
        construct_dataset(settings, repos, metric.name, output, gerrit)
    
    print 'Fixing miscategorization of volunteer engineers...'
    repos = cleanup_volunteers(repos, settings.whitelist)
    print 'Creating datasets...'
    create_dataset(repos, gerrit)


if __name__== '__main__':
    main()

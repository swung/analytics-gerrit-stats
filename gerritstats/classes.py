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
from datetime import datetime
from cStringIO import StringIO

class Metric(object):
    '''
    The Metric class
    '''
    def __init__(self, name, raw_query, settings):
        self.raw_query = raw_query
        self.name = name
        self.query = 'ssh -p %s %s gerrit query --format=%s %s' % (settings.port, settings.host, settings.format, self.raw_query)


class Settings(object):
    '''
    This object contains properties that apply to all repositories, including the queries that will be
    run to generate the statistics, a list of repositories to ignore and a set of engineers that do not use
    a WMF email address and hence will be classified as volunteer.
    '''
    def __init__(self, settings):
        self.queries = {
            'only+1'    : '-- CodeReview+1 -CodeReview+2 -CodeReview-1 -CodeReview-2',
            'no_review' : '-- -CodeReview+1 -CodeReview-1 -CodeReview+2 -CodeReview-2',
        }
        self.whitelist = set([
            'niklas.laxstrom@gmail.com',
            'roan.kattouw@gmail.com',
            'maxsem.wiki@gmail.com',
            's.mazeland@xs4all.nl',
            'jeroendedauw@gmail.com',
            'mediawiki@danielfriesen.name',
            'jdlrobson@gmail.com',
            'hashar@free.fr'
        ])
        self.ignore_repos = ['test']
        self.metrics =  {}
        self.parents = [
            'mediawiki/core',
            'mediawiki/extensions',
            'operations',
            'analytics',
        ]
        
        for name, query in self.queries.iteritems():
            self.metrics[name] = Metric(name, query, settings)
    
    def __str__(self):
        return 'Metrics container object'
    
    def get_measures(self):
        return self.queries.keys()


class Gerrit(object):
    '''
    This object contains the setings to interact with the gerrit server, nothing fancy these are just
    sensible defaults.
    '''
    def __init__(self, args):
        self.data_location = args.output
        self.host = 'gerrit.wikimedia.org'
        self.port = 29418
        self.format = 'JSON'
    
    def __str__(self):
        return 'Codereview settings object.'


class Repo(object):
    
    def __init__(self, name, settings, gerrit):
        self.touched = False
        self.gerrit = gerrit
        self.name = name
        self.dataset = {}
        self.filename = ('%s.csv' % (self.determine_filename()))
        self.directory = self.determine_directory()
        self.full_path = os.path.join(self.directory, self.filename)
        self.filemode = self.determine_filemode()
        self.create_path()
        
        self.today = datetime.today()
        self.email = {}
        self.email['wikimedian'] = set()
        self.email['volunteer'] = set()
        self.num_metrics = 0
        
        for metric in settings.metrics:
            self.dataset[metric] = {}
            self.dataset[metric]['oldest'] = datetime(2030,1,1)
            self.dataset[metric]['wikimedian'] = 0
            self.dataset[metric]['volunteer'] = 0
            self.dataset[metric]['total'] = 0
            self.num_metrics +=1
        
        self.labels = self.set_labels(settings)
    
    def __str__(self):
        return self.name
    
    def set_labels(self, settings):
        labels = []
        for metric in settings.metrics:
            headings = self.dataset[metric]
            headings = ['%s_%s' % (metric, heading) for heading in headings]
            labels.extend(headings)
        return labels
            

    def determine_directory(self):
        return os.path.join(self.gerrit.data_location, self.name)

    def create_path(self):
        if self.directory != '':
            try:
                os.makedirs(self.directory)
                print 'Creating %s...' % self.directory
            except OSError:
                pass
    
    def determine_filename(self):
        return os.path.basename(self.name)
    
    def determine_filemode(self):
        if os.path.isfile(self.full_path) == False:
            return 'w'
        else:
            return 'a'


class YamlConfig(object):
    def __init__(self, settings, repo):
        self.format = 'csv'
        self.repo = repo
        self.dataset_id = repo.name
        self.name = self.set_description(settings, repo)
        self.shortname = 'Codereview stats for %s' % repo.name
        self.url = self.set_url()
        self.buffer = StringIO()
    
    def set_url(self):
        return '/data/datasources/gerrit-stats/%s.%s' % (self.dataset_id, self.format)
    
    def set_description(self, settings, repo):
        measures = ','.join(settings.get_measures())
        return '%s metrics for %s repo' % (measures, repo.name)
    
    def set_metadata(self):
        self.buffer.write('id: %s\n' % self.dataset_id)
        self.buffer.write('name: %s\n' % self.name)
        self.buffer.write('shortName: %s\n' % self.shortname)
        self.buffer.write('format: %s\n' % self.format)
        self.buffer.write('url: %s\n' % self.url)
        self.buffer.write('\n')
    
    def set_timespan(self):
        today = datetime.today()
        self.buffer.write('timespan:\n')
        self.buffer.write('    end: %s/%s/%s\n' % (today.year, today.month, today.day))
        self.buffer.write('    start: 2012/6/12\n')
        self.buffer.write('    step: 1d\n')
        self.buffer.write('\n')
        
    def set_columns(self, labels):
        num_labels = len(labels)
        self.buffer.write('columns:\n')
        self.buffer.write('    labels:\n')
        self.buffer.write('    - Date\n')
        for label in labels:
            self.buffer.write('    - %s\n' % label)
        self.buffer.write('    types:\n')
        self.buffer.write('    - date\n')
        for x in xrange(num_labels):
            self.buffer.write('    - int\n')
        self.buffer.write('\n')
    
    def set_charttype(self):
        self.buffer.write('chart:\n')
        self.buffer.write('    chartType: dygraphs\n')
    
    def write_file(self):
        self.set_metadata()
        self.set_timespan()
        self.set_columns(self.repo.labels)
        self.set_charttype()
        
        filename = '%s.yaml' % (self.repo.determine_filename())
        full_path = os.path.join(self.repo.directory, filename)
        fh = open(full_path, 'w')
        fh.write(self.buffer.getvalue())
        fh.close()
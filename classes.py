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


class Gerrit(object):
    '''
    This object contains the setings to interact with the gerrit server, nothing fancy these are just
    sensible defaults.
    '''
    def __init__(self):
        self.data_location = 'data'
        self.host = 'gerrit.wikimedia.org'
        self.port = 29418
        self.format = 'JSON'
    
    def __str__(self):
        return 'Codereview settings object.'


class Repo(object):
    
    def __init__(self, name, settings, gerrit):
        self.touched = False
        self.name = name
        self.dataset = {}
        self.create_path(self.name, gerrit)
        self.filename = ('%s.csv' % (self.determine_filename(self.name)))
        self.filemode = self.determine_filemode(self.filename, gerrit)
        
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
    
    def __str__(self):
        return self.name
    
    def create_path(self, filename, gerrit):
        print filename
        dir= os.path.dirname(filename)
        if dir != '':
            dir = os.path.join(gerrit.data_location, dir)
            try:
                os.makedirs(dir)
                print 'Creating %s...' % dir
            except OSError:
                pass
    
    def determine_filename(self, filename):
        return os.path.basename(filename)
    
    def determine_filemode(self, filename, settings):
        if os.path.isfile('%s/%s' % (settings.data_location, filename)) == False:
            return 'w'
        else:
            return 'a'


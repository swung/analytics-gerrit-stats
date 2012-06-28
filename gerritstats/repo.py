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
from datetime import datetime, timedelta
from cStringIO import StringIO

from yaml import YamlConfig

class Repo(object):
    def __init__(self, name, description, gerrit):
        self.touched = False
        self.gerrit = gerrit
        self.description = description
        self.name = name
        self.dataset = {}
        self.dataset_headings = {1: {'headings': 'date'}}
        self.email = {}
        self.email['wikimedian'] = set()
        self.email['volunteer'] = set()
        self.labels = None
        self.file_contents = StringIO()
        self.first_commit = datetime(2030, 12, 31)
        
        self.filename = ('%s.csv' % (self.determine_filename()))
        self.csv_directory = self.determine_directory(gerrit.csv_location)
        self.yaml_directory = self.determine_directory(gerrit.yaml_location)
        self.full_csv_path = os.path.join(self.csv_directory, self.filename)
        self.full_yaml_path = os.path.join(self.yaml_directory, self.filename)
        self.filemode = self.determine_filemode()
        self.create_path()
        self.today = datetime.today()
        self.first_commit = datetime(2011,9,7)
        self.init_dataset()
        self.parent = self.determine_parent()
    
    def __str__(self):
        return self.name
    
    def determine_parent(self):
        for parent in self.gerrit.parents:
            if self.name.startswith(parent):
                return parent
        return None
        
    def init_dataset(self):
        self.construct_time_keys()
        self.register_headings()
    
    def register_headings(self):
        for query in self.gerrit.metrics:
            query = self.gerrit.metrics.get(query)
            counter = max(self.dataset_headings.keys()) + 1
            self.dataset_headings[counter] = {}
            self.dataset_headings[counter]['query'] = query.name
            self.dataset_headings[counter]['headings'] = query.headings

    def create_headings(self):
        headings = StringIO()
        max_key = len(self.dataset_headings.keys()) -1
        for x, query in enumerate(self.dataset_headings.values()):
            if query['headings'] == 'date':
                headings.write('%s,' % query['headings']) 
            else:
                query_name = query.get('query')  
                values = query.get('headings')
                values = ','.join(['%s_%s' % (query_name, value) for value in values])
                headings.write(values)
                if x < max_key:
                    headings.write(',')
        headings.write('\n')
        self.labels = headings.getvalue()
            

    def determine_directory(self, location):
        return os.path.join(location, self.name)

    def create_path(self):
        folders = [self.yaml_directory,self.csv_directory]
        for folder in folders:
            if folder != '':
                try:
                    os.makedirs(folder)
                    print 'Creating %s...' % folder
                except OSError:
                    pass
    
    def determine_filename(self):
        return os.path.basename(self.name)
    
    def determine_filemode(self):
        if os.path.isfile(self.full_csv_path) == False:
            return 'w'
        else:
            return 'a'
    
    def construct_timestamp(self, epoch):
        return datetime.fromtimestamp(epoch)
    
    def daterange(self, start_date, end_date):
        for n in range((end_date - start_date).days):
            yield start_date + timedelta(n)

    def construct_day_key(self, date):
        day = '%s%s' % (0, date.day) if date.day < 10 else date.day
        month = '%s%s' % (0, date.month) if date.month < 10 else date.month
        return '%s-%s-%s' % (date.year, month, day)
    
    def construct_time_keys(self):
        today  =  datetime.today()
        for day in self.daterange(self.first_commit, today):
            day = self.construct_day_key(day)
            self.dataset[day] = {}
            self.dataset[day]['touched'] = False
            
    def is_wikimedian(self, email):
        if email in self.gerrit.whitelist:
            return True
        if email.endswith('wikimedia.org'):
            return True
        else:
            return False
        
    def determine_first_commit_date(self):
        dates = self.dataset.keys()
        dates.sort()
        dates.reverse()
        for date in dates:
            touched = self.dataset[date]['touched']
            if touched:
                date = datetime.strptime(date, '%Y-%m-%d')
                if date < self.first_commit:
                    self.first_commit = date
    
    
    def prune_observations(self):
        self.determine_first_commit_date()
        for date_str in self.dataset.keys():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if date < self.first_commit:
                del self.dataset[date_str]
    
    def fill_missing_observations(self):
        for date in self.dataset.keys():
            for name, query in self.gerrit.metrics.iteritems():
                if name not in self.dataset[date]:
                    self.dataset[date].setdefault(name, {})
                    for heading in query.headings:
                        self.dataset[date][name].setdefault(heading, 0) 
            

    def create_dataset(self):
        self.create_headings()
        self.prune_observations()
        self.fill_missing_observations()
        
        if self.filemode == 'w':
            self.file_contents.write(self.labels)
            
        dates = self.dataset.keys()
        dates.sort()
        for date in dates:
            observation = self.dataset.get(date)
            self.file_contents.write('%s' % date)              
            max_key = len(observation.keys())
            for x, counts in enumerate(observation.itervalues()):
                if type(counts) == dict:
                    obs = ','.join(['%s' % count for count in counts.values()])
                    if x < max_key:
                        self.file_contents.write(',')
                    self.file_contents.write(obs)
            self.file_contents.write('\n')
            
    def write_dataset(self):
        self.create_dataset()
        #if dataset is empty then there is no need to write it 
        if not self.dataset == {}:
            yaml = YamlConfig(self.gerrit, self)
            yaml.write_file()
            
            fh = open(self.full_csv_path, self.filemode)
            fh.write(self.file_contents.getvalue())
            fh.close()
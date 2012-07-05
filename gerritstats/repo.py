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
import logging

from datetime import date, datetime, timedelta
from cStringIO import StringIO
from itertools import product

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

from yaml import YamlConfig
from settings import GERRIT_CREATION_DATE

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('logs/gerrit-stats.txt')

class Repo(object):
    def __init__(self, name, description, gerrit):
        self.description = description
        self.name = name
        self.observations = OrderedDict()
        self.headings = OrderedDict(date='date')
        self.file_contents = StringIO()
        self.first_commit = GERRIT_CREATION_DATE
        self.future_date = date(2030,12,31)
        self.metrics = ['time_first_review', 'time_plus2']
        self.suffixes = ['total', 'staff', 'volunteer']
        
        self.filename = ('%s.csv' % (self.determine_filename()))
        self.csv_directory = self.determine_directory(gerrit.csv_location)
        self.yaml_directory = self.determine_directory(gerrit.yaml_location)
        self.full_csv_path = os.path.join(self.csv_directory, self.filename)
        self.full_yaml_path = os.path.join(self.yaml_directory, self.filename)
        
        self.filemode = self.determine_filemode()
        self.create_path()
        self.today = date.today()
        
        self.parent = self.determine_parent(gerrit)
    
    def __str__(self):
        return self.name
    
    def determine_parent(self, gerrit):
        for parent in gerrit.parents:
            if self.name.startswith(parent):
                return parent
        return None
    
    def create_headings(self):
        self.metrics.sort()
        self.suffixes.sort()
        iterator =  product(self.metrics, self.suffixes)
        for it in iterator:
            yield self.merge_keys(it[0], it[1])
    
    def merge_keys(self, key1, key2):
        return '%s_%s' %  (key1, key2)
   
    def increment(self, commit):
        obs = self.observations.get(commit.created_on.date(), Observation(commit.created_on, self))
        obs.commits+=1
        self.observations[obs.date] = obs
        if commit.status == 'A':
            return
        
        if commit.self_review == True:
            obs.self_review +=1
        self.observations[obs.date] = obs
        
        for metric in self.metrics:
            start_date = getattr(commit, 'created_on') if metric == 'time_first_review' else getattr(commit, 'time_first_review')
            end_date = getattr(commit, metric)
            for date in self.daterange(start_date, end_date):
                obs = self.observations.get(date.date(), Observation(date.date(), self))
                for heading in product([metric], self.suffixes):
                    heading = self.merge_keys(heading[0], heading[1])
                    #print heading
                    attr = getattr(obs, heading)
                    if heading.endswith('staff') and commit.author.staff == True:
                        attr+=1
                    elif heading.endswith('volunteer') and commit.author.staff == False:
                        attr+=1
                    elif heading.endswith('total'):
                        attr+=1
                    setattr(obs, heading, attr)
                self.observations[obs.date] = obs
       
    def determine_directory(self, location):
        return os.path.join(location, self.name)

    def create_path(self):
        folders = [self.yaml_directory,self.csv_directory]
        for folder in folders:
            if folder != '':
                try:
                    os.makedirs(folder)
                    logging.info('Created %s'% folder )
                except OSError:
                    pass
    
    def determine_filename(self):
        return os.path.basename(self.name)
    
    def determine_filemode(self):
        if os.path.isfile(self.full_csv_path) == False:
            return 'w'
        else:
            return 'a'
    
    def daterange(self, start_date, end_date):
        for n in range((end_date - start_date).days):
            yield start_date + timedelta(n)

#    def construct_day_key(self, date):
#        day = '%s%s' % (0, date.day) if date.day < 10 else date.day
#        month = '%s%s' % (0, date.month) if date.month < 10 else date.month
#        return '%s-%s-%s' % (date.year, month, day)
    
    def fill_in_missing_days(self):
        for date in self.daterange(self.first_commit, self.today):
            obs = self.observations.get(date, Observation(date, self, False))
            self.observations[date] = obs
            
        
    def determine_first_commit_date(self):
        dates = self.observations.keys()
        dates.sort()
        for date in dates:
            touched = self.observations[date].touched
            if not touched:
                if date < self.future_date:
                    self.first_commit = date + timedelta(days=1)
            else:
                break

    def prune_observations(self):
        self.determine_first_commit_date()
        for date in self.observations.keys():
            if date < self.first_commit:
                del self.observations[date]
    
    def generate_headings(self):
        headings = ['date', 'commits', 'self_review']
        for heading in self.create_headings():
            headings.append(heading)
        return ','.join(headings)
            
    def create_dataset(self):
        if self.filemode == 'w':
            headings = self.generate_headings()
            self.file_contents.write(headings)
            self.file_contents.write('\n')
            
        dates = self.observations.keys()
        dates.sort()
        for date in dates:
            observation = self.observations.get(date)
            values = observation.get_values()
            values.insert(0, date)          
            values = ','.join(['%s' % value for value in values])
            self.file_contents.write(values)
            self.file_contents.write('\n')
            
    def write_dataset(self, gerrit):
        #if dataset is empty then there is no need to write it 
        if not self.observations == {}:
            self.create_dataset()
            yaml = YamlConfig(gerrit, self)
            yaml.write_file()
            
            fh = open(self.full_csv_path, self.filemode)
            fh.write(self.file_contents.getvalue())
            fh.close()

class Observation(object):
    def __init__(self, date, repo, touched=True):
        self.touched = touched
        self.date = self.convert_to_date(date)
        self.commits = 0
        self.self_review = 0
        self.ignore = ['touched', 'date', 'ignore']
        for heading in repo.create_headings():
            setattr(self, heading, 0)
    
    def __str__(self):
        return '%s:%s' % (self.date, self.commits)

    def __iter__(self):
        props = self.__dict__
        props = props.keys()
        props.sort()
        for prop in props:
            if not prop.startswith('__') and prop not in self.ignore:
                yield prop
    
    def update(self, key, value):
        prop = getattr(self, key)
        prop += value
        
    
    def iteritems(self):
        for prop in self:
            value = getattr(self, prop)
            yield prop, value
    
    def get_values(self):
        values = []
        for prop in self:
            values.append(getattr(self, prop))
        return values

    def convert_to_date(self, date):
        if type(date) == datetime:
            return date.date()
        else:
            return date
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
from extensions import extensions
from sql_queries import GERRIT_CREATION_DATE

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


class Repo(object):
    def __init__(self, name, description, gerrit, is_parent=False):
        self.description = description
        self.name = name
        self.gerrit = gerrit
        self.observations = OrderedDict()
        self.headings = OrderedDict(date='date')
        self.file_contents = StringIO()
        self.first_commit = GERRIT_CREATION_DATE
        self.future_date = date(2030,12,31)
        self.is_parent = is_parent
        
        self.metrics = ['waiting_first_review', 'waiting_plus2']
        self.suffixes = ['total', 'staff', 'volunteer']
        
        self.filename = ('%s.csv' % (self.determine_filename()))
        self.csv_directory = self.determine_directory(gerrit.csv_location)
        self.yaml_directory = self.determine_directory(gerrit.yaml_location)
        self.full_csv_path = os.path.join(self.csv_directory, self.filename)
        self.full_yaml_path = os.path.join(self.yaml_directory, self.filename)
        
        self.create_path()
        self.yesterday = datetime(date.today().year, date.today().month, date.today().day-1, 23,59,59)
        
        self.wmf_extension = self.is_wikimedia_extension()
        self.extension = self.is_extension()
        self.parent_repos = self.determine_parent(gerrit)
            
    def __str__(self):
        return self.name
    
    def create_dataset(self):
        headings = self.generate_headings()
        self.file_contents.write(headings)
        self.file_contents.write('\n')
            
        dates = self.observations.keys()
        dates.sort()
        today = datetime.today()
        last_date = dates[-1]
        if last_date.year == today.year and last_date.month == today.month and last_date.day == today.day: 
            dates.pop(dates.index(last_date))
            #print 'today removed form dataset: %s ' % self.name
        
        for date in dates:
            observation = self.observations.get(date)
            values = observation.get_values()
            values.insert(0, date.strftime('%Y/%m/%d'))          
            values = ','.join(['%s' % value for value in values])
            self.file_contents.write(values)
            self.file_contents.write('\n')
            
    def create_headings(self):
        self.metrics.sort()
        self.suffixes.sort()
        iterator =  product(self.metrics, self.suffixes)
        for it in iterator:
            yield self.merge_keys(it[0], it[1])
            
    def create_path(self):
        folders = [self.yaml_directory,self.csv_directory]
        for folder in folders:
            if folder != '':
                try:
                    os.makedirs(folder)
                    logging.info('Created %s'% folder )
                except OSError:
                    pass
    
    def daterange(self, start_date, end_date):
        dt = ((end_date - start_date).days)
        #this happens for the waiting_plus2 measure if there are no positive 
        #reviews, then the review date is set to the commit creation date but 
        #that will mean that the end date is before the start date. Hence a 
        #negative value here should be reset to 0.
        if dt < 0:
            dt = 0
        elif dt >= 0:
            # add +1 because we want to have the iterator include the end date.
            dt = dt + 1  
        for n in range(dt):
            yield start_date + timedelta(n)
    
    def determine_directory(self, location):
        return os.path.join(location, self.name)

    def determine_filename(self):
        return os.path.basename(self.name)
    
    def determine_parent(self, gerrit):
        parents = []
        if self.extension == True:
            parents.append('mediawiki/all_extensions')
        if self.wmf_extension == True:
            parents.append('mediawiki/wmf_extensions')
            parents.append('mediawiki/core_wmf_extensions')
        if self.name == 'mediawiki/core':
            parents.append('mediawiki/core_wmf_extensions')
        
        if self.is_parent == False:
            for repo in self.gerrit.parents:
                if self.name != repo['name']:
                    if self.name.startswith(repo['name']):
                        parents.append(repo['name'])
                else:
                    self.is_parent = True
        return parents   

    def determine_first_commit_date(self):
        dates = self.observations.keys()
        dates.sort()
        for dt in dates:
            touched = self.observations[dt].touched
            if not touched:
                if dt < self.future_date:
                    self.first_commit = dt
            else:
                break

    def fill_in_missing_days(self):
        for date in self.daterange(self.first_commit, self.yesterday.date()):
            obs = self.observations.get(date, Observation(date, self, False))
            self.observations[date] = obs
    
    def generate_headings(self):
        headings = ['date', 'commits', 'self_review']
        for heading in self.create_headings():
            headings.append(heading)
        return ','.join(headings)
     
    def get_review_start_date(self, commit, metric):
        start_date = getattr(commit, 'created_on') if metric == 'waiting_first_review' else getattr(commit, 'waiting_first_review')
        try:
            return getattr(start_date, 'granted') 
        except AttributeError:
            return start_date
        
    def get_review_end_date(self, commit, metric):
        try:
            return getattr(commit, metric).granted
        except AttributeError:
            return getattr(commit, metric)  
        
    def increment_number_of_changesets(self, commit):
        obs = self.observations.get(commit.created_on.date(), Observation(commit.created_on, self))
        obs.commits+=1
        if commit.self_review == True:
            obs.self_review +=1
        self.observations[obs.date] = obs
    
    def increment(self, changeset):
        self.increment_number_of_changesets(changeset)
        if changeset.status == 'A':
            return
        for metric in self.metrics:
            start_date = self.get_review_start_date(changeset, metric)
            end_date = self.get_review_end_date(changeset, metric)
            
            for date in self.daterange(start_date, end_date):
                obs = self.observations.get(date.date(), Observation(date.date(), self))
                if metric == 'waiting_first_review':
                    obs.changeset_ids.add(changeset.change_id)
                for heading in product([metric], self.suffixes):
                    heading = self.merge_keys(heading[0], heading[1])
                    value = getattr(obs, heading)
                    if heading.endswith('staff') and changeset.author.staff == True:
                        value+=1
                    elif heading.endswith('volunteer') and changeset.author.staff == False:
                        value+=1
                    elif heading.endswith('total'):
                        value+=1
                    setattr(obs, heading, value)
                self.observations[obs.date] = obs
 
    def is_wikimedia_extension(self):
        shortname = self.name.split('/')[-1]
        if shortname in extensions:
            return True
        else:
            return False

    def is_extension(self):
        if self.name.find('/extensions') > -1:
            return True
        else:
            return False
        
    def merge_keys(self, key1, key2):
        return '%s_%s' %  (key1, key2)
           
    def prune_observations(self):
        self.determine_first_commit_date()
        for date in self.observations.keys():
            if date < self.first_commit:
                del self.observations[date] 
    
    def write_dataset(self, gerrit):
        #if dataset is empty then there is no need to write it 
        if not self.observations == {}:
            self.create_dataset()
            yaml = YamlConfig(gerrit, self)
            yaml.write_file()
            
            fh = open(self.full_csv_path, 'w')
            fh.write(self.file_contents.getvalue())
            fh.close()

class Observation(object):
    def __init__(self, date, repo, touched=True):
        self.touched = touched
        self.date = self.convert_to_date(date)
        self.commits = 0
        self.self_review = 0
        self.changeset_ids = set()
        self.ignore = ['touched', 'date', 'ignore'] #changeset_ids
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
    
    def convert_to_date(self, date):
        if type(date) == datetime:
            return date.date()
        else:
            return date
    
    def iteritems(self):
        for prop in self:
            value = getattr(self, prop)
            yield prop, value
    
    def get_values(self):
        values = []
        for prop in self:
            values.append(getattr(self, prop))
        return values

    def update(self, key, value):
        prop = getattr(self, key)
        if type(prop) == type(set()):
            for val in value:
                prop.add(val)
        else:
            prop += value
        setattr(self, key, prop)
        return self

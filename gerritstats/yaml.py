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
from cStringIO import StringIO
from datetime import datetime

class YamlConfig(object):
    def __init__(self, gerrit, repo):
        self.format = 'csv'
        self.gerrit = gerrit
        self.repo = repo
        self.dataset_id = repo.name
        self.name = self.set_description(repo)
        self.shortname = 'Codereview stats for %s' % repo.name
        self.url = self.set_url()
        self.buffer = StringIO()
    
    def set_url(self):
        pos = self.dataset_id.rfind('/') +1
        repo_name = self.dataset_id[pos:]
        return '/data/datasources/gerrit-stats/datafiles/%s/%s.%s' % (self.dataset_id, repo_name, self.format)
    
    def set_description(self, repo):
        return '%s' % (repo.name)
    
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
        self.buffer.write('    start: %s/%s/%s\n' % (self.repo.first_commit.year, self.repo.first_commit.month, self.repo.first_commit.day))
        self.buffer.write('    step: 1d\n')
        self.buffer.write('\n')
        
    def set_columns(self, repo):
        headings = repo.generate_headings()
        headings = headings.split(',')
        num_headings = len(headings)
        self.buffer.write('columns:\n')
        self.buffer.write('    labels:\n')
        self.buffer.write('    - Date\n')
        for heading in headings:
            self.buffer.write('    - %s\n' % heading)
        self.buffer.write('    types:\n')
        self.buffer.write('    - date\n')
        for x in xrange(num_headings-1):
            self.buffer.write('    - int\n')
        self.buffer.write('\n')
    
    def set_charttype(self):
        self.buffer.write('chart:\n')
        self.buffer.write('    chartType: %s\n' % self.gerrit.toolkit)
    
    def write_file(self):
        self.set_metadata()
        self.set_timespan()
        self.set_columns(self.repo)
        self.set_charttype()
        
        filename = '%s.yaml' % (self.repo.determine_filename())
        full_path = os.path.join(self.repo.yaml_directory, filename)
        fh = open(full_path, 'w')
        fh.write(self.buffer.getvalue())
        fh.close()
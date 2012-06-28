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
import subprocess
from datetime import datetime

from peewee import RawQuery


class Query(object):
    '''
    The Query class
    '''
    def __init__(self, gerrit, name, raw_query, method, support_json, model, handler, debug, recreate, headings):
        self.raw = raw_query
        self.name = name
        self.method = method
        self.model = model
        self.support_json = support_json
        self.handler = handler
        self.debug = debug
        self.recreate = recreate
        self.headings = headings
        if self.method == 'ssh':
            if self.support_json:
                self.full = 'ssh -p %s %s gerrit --format=%s %s' % (gerrit.port, gerrit.host, gerrit.format, self.raw)
            else:
                self.full = 'ssh -p %s %s gerrit  %s' % (gerrit.port, gerrit.host,  self.raw)
        elif self.method == 'sql':
            self.full = self.raw
            
    def __str__(self):
        print self.name

    def launch(self):
        if self.method == 'ssh':
            results = self.run_gerrit()
        elif self.method == 'sql':
            results = self.run_sql()
        else:
            raise Exception('Format %s is not supported.\n' % (self.format))
        
        if type(results) == dict:
            if results.get('type', None) == 'error':
                raise Exception('There is an error in your query: %s.' % self.full)
                sys.exit(-1) 
            else:
                return results
        else:
            return results

    def run_gerrit(self):
        query = self.full.split(' ')
        output = subprocess.Popen(query, shell=False, stdout=subprocess.PIPE).communicate()[0]
        return output
    
    def run_sql(self):
        return RawQuery(self.model, self.raw)




class Observation(object):
    def __init__(self, date, wikimedian, volunteer, total):
        self.date = date
        self.oldest = datetime(2030,1,1)
        self.wikimedia = wikimedian
        self.volunteer = volunteer
        self.total = total

class Observations(object):
    def __init__(self):
        self.obs = {}
        


        


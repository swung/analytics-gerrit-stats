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
import logging
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('logs/gerrit-stats.txt')

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
        
    def parse_json(self, output):
        output = output.split('\n')
        data = []
        for obs in output:
            try:
                data.append(json.loads(obs))
            except ValueError, e:
                print e
        return data

    def run_gerrit(self):
        query = self.full.split(' ')
        output, error = subprocess.Popen(query, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()  #[0]
        if error:
            logging.warning('Could not retrieve list with Gerrit repositories. Error %s' % error.strip())
            logging.warning('Closing down gerrit-stats.')
            sys.exit(-1)
        return output
    

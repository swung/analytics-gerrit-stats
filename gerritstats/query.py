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
import logging

import paramiko

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


class Query(object):
    '''
    The Query class
    '''
    def __init__(self, query, name, method, support_json, gerrit):
        self.query = query
        self.name = name
        self.method = method
        self.support_json = support_json
        self.gerrit = gerrit
            
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
        
    def run_gerrit(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.gerrit.host, port=self.gerrit.port, username=self.gerrit.ssh_username, key_filename=self.gerrit.ssh_identity)
        stdin, stdout, stderr = ssh.exec_command(self.query)
        data = stdout.readlines()
        try:
            error = stderr.readlines()
        except IOError:
            pass
        
        if error:
            logging.warning('Could not retrieve list with Gerrit repositories. Error %s' % error.strip())
            logging.warning('Closing down gerrit-stats.')
            sys.exit(-1)
        return data

    

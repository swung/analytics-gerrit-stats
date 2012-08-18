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

whitelist = set([
            'niklas.laxstrom@gmail.com',
            'roan.kattouw@gmail.com',
            'maxsem.wiki@gmail.com',
            's.mazeland@xs4all.nl',
            'jeroendedauw@gmail.com',
            'mediawiki@danielfriesen.name',
            'jdlrobson@gmail.com',
            'hashar@free.fr'
        ])

class Developer(object):
    def __init__(self, **kwargs):
        self.full_name = kwargs.get('full_name')
        self.preferred_email = kwargs.get('preferred_email', '')
        self.registered_on = kwargs.get('registered_on')
        self.account_id = kwargs.get('account_id')
        
        self.fix_email()
        
        self.staff = self.is_staff()
        self.human = self.is_human()
        
    def __str__(self):
        return self.full_name
    
    def is_staff(self):
        if self.preferred_email in whitelist:
            return True
        elif self.preferred_email.endswith('wikimedia.org'):
            return True
        else:
            return False
    
    def is_human(self):
        non_human_reviewers = ['jenkins-bot','L10n-bot', 'gerrit2']
        if self.full_name in non_human_reviewers:
            return False
        else:
            return True

    def fix_email(self):
        if self.preferred_email == None:
            self.preferred_email = 'No email address'    
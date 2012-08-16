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

import json
from datetime import datetime, date
import pytz 

def main():
    fh = open('benchmark.json', 'r')
    data = []
    for line in fh:
        data.append(line)
    fh.close()
    
    data = ','.join(data)
    data = '%s%s%s' % ('[', data, ']')
    changesets = json.loads(data)
    
    change_ids=[]
    
    local = pytz.timezone ("America/Los_Angeles")
    for changeset in changesets:
        try:
            created_on = datetime.fromtimestamp(changeset['createdOn'])
            local_dt = local.localize(created_on, is_dst=None)
            utc_dt = local_dt.astimezone (pytz.utc)
            
            if int(changeset['number']) == 14052:
                print 'break'
            
            if utc_dt.date() != date.today():
                if changeset['project'].startswith('mediawiki') == True:
                    change_ids.append(int(changeset['number']))
        except KeyError:
            pass
    
    change_ids.sort()
    fh = open('backlog_gerrit.txt', 'w')
    for change_id in change_ids:
        print change_id
        fh.write('%s\n' % change_id)
    
    fh.close()
if __name__ == '__main__':
    main()
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

def main():
    data = {}
    path = 'data/datafiles/mediawiki/extensions/'
    folders = os.listdir(path)
    for folder in folders:
        try:
            files = os.listdir(os.path.join(path, folder))
            for filename in files:
                print os.path.join(path, folder, filename)
                fh = open(os.path.join(path, folder, filename), 'r')
                for x, line in enumerate(fh):
                    line = line.strip()
                    line = line.split(',')
                    if x == 0:
                        headers = line
                    else:
                        for y,header in enumerate(headers):
                            if y==0:
                                date = line[y]
#                                if date == '2012-03-21':
#                                    print line[1]
                                data.setdefault(date, {})
                            else:
                                data[date].setdefault(header, 0)
                                data[date][header] += int(line[y])
                fh.close()
        except OSError:
            pass
    
    dates = data.keys()
    dates.sort()
    for date in dates:
        print '%s:%s' %  (date, data[date]['commits'])

if __name__ == '__main__':
    main()
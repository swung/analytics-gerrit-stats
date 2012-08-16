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


def read_file(filename):
    fh = open(filename,'r')
    data = set()
    for line in fh:
        line =  int(line.strip())
        data.add(line)
    
    fh.close()
    return data


def main():
    backlog_gerrit = read_file('backlog_gerrit.txt')
    backlog_gerrit_stats = read_file('backlog_gerrit-stats.txt')
    
    fh = open('backlog_diff.txt', 'w')
    
    diffs = backlog_gerrit.difference(backlog_gerrit_stats)
    diffs = list(diffs)
    diffs.sort()
    
    msg = 'Change ids present in gerrit search ui but not gerrit-stats:'
    print msg
    fh.write('%s\n' % msg)
    for diff in diffs:
        print diff
        fh.write('%s\n' % diff)
    
    diffs = backlog_gerrit_stats.difference(backlog_gerrit)
    diffs = list(diffs)
    diffs.sort()
    
    msg = 'Change ids present in gerrit-stats but not in gerrit search ui:'
    print msg
    fh.write('%s\n' % msg)
    for diff in diffs:
        print diff
        fh.write('%s\n' % diff)

    fh.close()
if __name__ == '__main__':
    main()
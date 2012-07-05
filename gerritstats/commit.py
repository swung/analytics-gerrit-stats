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

from datetime import datetime

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

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
        self.preferred_email = kwargs.get('preferred_email')
        self.registered_on = kwargs.get('registered_on')
        self.account_id = kwargs.get('account_id')
        self.staff = self.is_staff()
        
    def __str__(self):
        return self.full_name
    
    def is_staff(self):
        if self.preferred_email in whitelist:
            return True
        elif self.preferred_email.endswith('wikimedia.org'):
            return True
        else:
            return False
        

class Commit(object):
    def __init__(self, **kwargs):
        self.created_on = kwargs.get('created_on')
        self.owner_account_id = kwargs.get('owner_account_id')
        self.dest_project_name = kwargs.get('dest_project_name')
        self.dest_branch_name = kwargs.get('dest_branch_name')
        self.change_id = kwargs.get('change_id')
        self.last_updated_on = kwargs.get('last_updated_on')
        self.change_key = kwargs.get('change_key')
        self.subject = kwargs.get('subject')
        self.open = True if kwargs.get('open') == 'Y' else False
        self.nbr_patch_sets = kwargs.get('nbr_patch_sets')
        self.status = kwargs.get('status')
        self.merged = True if kwargs.get('status') == 'M' else False
        self.reviews = OrderedDict()
        self.self_review = False
        self.repo_has_review = True
        self.time_first_review = datetime.today()  #wait time between creation and first plus 1
        self.time_plus2 = datetime.today()  #wait time between first plus 1 and plus 2
        self.merge_review = None #this will become an instance of Review
        self.all_positive_reviews = None
        self.author = Developer(**kwargs)  #this will become an instance of Developer
    
    def __str__(self):
        return '%s:%s' %  (self.change_id, self.subject)
    
    def is_self_reviewed(self):
        if self.merged:
#            if not self.merge_review:
#                print self, self.reviews
            try:
                if self.owner_account_id == self.merge_review.account_id:
                    return True
            except AttributeError:
                pass
        return False
    
    def is_all_positive_reviews(self):
        values = [True if review.value > 0 else False for review in self.reviews.itervalues()]
        if all(values) and len(values) > 0:
            self.all_positive_reviews = True
        else:
            self.all_positive_reviews = False
        
    
    def calculate_wait(self):
        if self.reviews == {}:
            if self.status == 'A':
                # edge case 1
                # the commit has been abandoned and there are no reviews
                # then just reset the review times to when the commit was abandoned
                self.time_first_review = self.last_updated_on
                self.time_plus2 = self.last_updated_on
            elif self.status == 'M':
                # edge case 2
                # commit has been merged without any reviews.
                self.time_first_review = self.last_updated_on
                self.time_plus2 = self.last_updated_on
            elif self.status == 'd':
                # edge case 3
                # ignore draft commits for now
                self.time_first_review = self.last_updated_on
                self.time_plus2 = self.last_updated_on
        else:
            values = []
            for review in self.reviews.itervalues():
                values.append(review.value)
                if review.value != 2:
                    if review.granted < self.time_first_review:
                        self.time_first_review = review.granted
                else:
                    if self.all_positive_reviews == True:
                        self.time_plus2 = review.granted
                        self.merge_review = review
                    else:
                        self.time_plus2 = self.created_on
            if values != [] and min(values) == 2:
                # edge case 4
                # this handles the edge case where there is only a +2
                # review, in that case the time to first review variable
                # is set to time_plus2. 
                self.time_first_review = self.time_plus2
                        
        
    
class Review(object):
    def __init__(self, **kwargs):
        self.change_id = kwargs.get('change_id')
        self.granted = kwargs.get('granted')
        self.value = kwargs.get('value')
        self.account_id = kwargs.get('account_id')
        self.patch_set_id = kwargs.get('patch_set_id')
        self.reviewer = Developer(**kwargs)

    def __str__(self):
        return '%s:%s' % (self.change_id, self.value)


def main():
    pass
    
if __name__ == '__main__':
    main()
                         

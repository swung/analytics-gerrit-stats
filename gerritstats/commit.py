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

from datetime import datetime, timedelta

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
        self.waiting_first_review = datetime.today() - timedelta(days=1) #wait time between creation and first review
        self.waiting_plus2 = datetime.today() - timedelta(days=1)  #wait time between first plus 1 and plus 2
        self.merge_review = None #this will become an instance of Review
        self.all_positive_reviews = None
        self.author = Developer(**kwargs)  #this will become an instance of Developer
    
    def __str__(self):
        return '%s:%s' %  (self.change_id, self.subject)
    
    def is_self_reviewed(self):
        if self.merged:
            try:
                if self.owner_account_id == self.merge_review.account_id:
                    self.self_review = True
            except AttributeError:
                pass
    
    def is_all_positive_reviews(self):
        values = [True if review.value > 0 else False for review in self.reviews.itervalues()]
        if all(values) and len(values) > 0:
            self.all_positive_reviews = True
        else:
            self.all_positive_reviews = False
    
    def get_first_review_by_review_value(self, value):
        #self.reviews is an ordereddict that is sorted by timestamp, so the first hit is the oldest. 
        for review in self.reviews.itervalues():
            if review.value == value and review.reviewer.human == True:
                return review
        #this commit does not have a review with value 'value', return None
        return None
        
    
    def get_first_review(self):
        dates = self.reviews.keys()
        try:
            first_date = min(dates)
            return self.reviews.get(first_date)
        except ValueError:
            return None
    
    
    def calculate_wait_plus2(self):
        if self.merged and self.reviews != {}:
            #commit was merged with reviews
            try:
                review = self.get_first_review_by_review_value(2)
                if not review:
                    #commit was merged but there was no +2 made by a human developer. 
                    review = Review(granted=self.last_updated_on)
            except (AttributeError, ValueError):
                #although there are reviews, there is no +2 review
                #second guess the merge date by using last_updated_on field
                review = Review(granted=self.last_updated_on)
        elif self.merged and self.reviews == {}:
            #commit was merged but there were no reviews
            #second guess the merge date by using last_updated_on field
            review = Review(granted=self.last_updated_on)
        else:
            #commit is not merged, but all the reviews are positive
            if self.all_positive_reviews == True:
                # always deduct 1 day as we only run the counts for complete days
                review = Review(granted=datetime.today() - timedelta(days=1))
            else:
                #commit is not yet ready to be merged, ignore for stats
                review = Review(granted=self.last_updated_on)
        self.waiting_plus2 = review
    
    def calculate_wait_first_review(self):
        if self.reviews == {}:
            if self.merged:
                review = Review(granted=self.last_updated_on)
            else:
                #there are no reviews and the commit is not merged
                # always deduct 1 day as we only run the counts for complete days
                review = Review(granted=datetime.today() - timedelta(days=1))
        else:
            review = self.get_first_review()
        
        self.waiting_first_review = review
        
    
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
                         

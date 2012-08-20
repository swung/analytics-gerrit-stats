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

from copy import deepcopy

from utils import determine_yesterday
from developer import Developer

try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict


class Changeset(object):
    '''
    A changeset can contain one or more patchsets and each patchset can contain
    0 or more reviews.
    
    @param created_on: timestamp when this changeset was created
    @type: datetime
    
    @param owner_account_id: id of developer, this can be used to retrieve 
    instance of @Developer
    @type: integer
    
    @param dest_project_name: name of the project in Gerrit
    @type: string
    
    @param dest_branch_name: name of the remote branch in which the changeset
    was committed
    @type: string
    
    @param change_id: unique id of the changeset
    @type: integer
    
    @param last_updated_on: timestamp of the last action on this changeset
    @type: datetime
    
    @param change_key: internal Gerrit change key
    @type: string
    
    @param subject: subject of the changeset
    @type: string 
    
    @param nbr_patch_sets: total number of patchsets that belong to this
    changeset
    @type: integer
    
    @param status: status of the changeset. Capital letters are final statuses,
    like 'M' for merged and 'A' for abandoned. Lower case status can change like
    'd' for draft. 
    @type: string
    
    '''
    def __init__(self, **kwargs):
        self.created_on = kwargs.get('created_on')
        self.owner_account_id = kwargs.get('owner_account_id')
        self.dest_project_name = kwargs.get('dest_project_name')
        self.dest_branch_name = kwargs.get('dest_branch_name')
        self.change_id = kwargs.get('change_id')
        self.last_updated_on = kwargs.get('last_updated_on')
        self.change_key = kwargs.get('change_key')
        self.subject = kwargs.get('subject')
        self.nbr_patch_sets = kwargs.get('nbr_patch_sets')
        self.status = kwargs.get('status')

        self.patch_sets = OrderedDict()
        self.open = True if kwargs.get('open') == 'Y' else False
        self.merged = True if kwargs.get('status') == 'M' else False
        self.self_review = False
        self.repo_has_review = True

        self.yesterday = determine_yesterday()
        self.waiting_first_review = self.yesterday  # wait time between creation and first review
        self.waiting_plus2 = self.yesterday  # wait time between first plus 1 and plus 2
        self.merge_review = None  # this will become an instance of Review
        self.all_positive_reviews = None
        self.author = Developer(**kwargs)  # this will become an instance of Developer

    def __str__(self):
        return '%s:%s' % (self.change_id, self.subject)

    def is_self_reviewed(self):
        '''
        Determine whether this changeset was reviewed by the developer who
        submitted this changeset.
        '''
        self.get_merge_review()
        if self.merged:
            try:
                if self.owner_account_id == self.merge_review.account_id:
                    self.self_review = True
            except AttributeError:
                pass

    def is_all_positive_reviews(self):
        '''
        only consider the most recent patch_set to determine whether all reviews were positive.
        '''
        values = [True if review.value > 0 else False for review in self.patch_sets[self.nbr_patch_sets].reviews.itervalues()]
        if all(values) and len(values) > 0:
            self.all_positive_reviews = True
        else:
            self.all_positive_reviews = False

    def get_first_review_by_review_value(self, value):
        '''
        self.reviews is an ordereddict that is sorted by timestamp, so the first hit is the oldest.
        '''
        for review in self.patch_sets[self.nbr_patch_sets].reviews.itervalues():
            if review.value == value and review.reviewer.human is True and review.category_id == 'CRVW':
                return deepcopy(review)
        #this commit does not have a review with value 'value', return None
        return None

    def get_merge_review(self):
        if self.merged is True:
            merge_review = self.get_first_review_by_review_value(2)
            if merge_review:
                self.merge_review = merge_review
            else:
                #commit was merged but there was no review
                self.merge_review = None

    def get_review(self, review_age):
        '''
        Valid values for review_age are min and max.
        '''
        dates = self.patch_sets[self.nbr_patch_sets].reviews.keys()
        try:
            first_date = review_age(dates)
            return self.patch_sets[self.nbr_patch_sets].reviews.get(first_date)
        except ValueError:
            return None

    def calculate_wait_plus2(self):
        if self.merged and self.patch_sets[self.nbr_patch_sets].reviews != {}:
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
        elif self.merged and self.patch_sets[self.nbr_patch_sets].reviews == {}:
            #commit was merged but there were no reviews
            #second guess the merge date by using last_updated_on field
            #this means that rerunning gerrit-stats over time can change the
            #count as this number is not set in stone. 
            review = Review(granted=self.last_updated_on)
        else:
            #commit is not merged, but all the reviews are positive
            if self.all_positive_reviews is True:
                # always deduct 1 day as we only run the counts for complete days
                review = Review(granted=self.yesterday)
            else:
                #commit is not yet ready to be merged, ignore for stats
                review = Review(granted=self.last_updated_on)
        self.waiting_plus2 = review

    def calculate_wait_first_review(self):
        values = [-2, -1, 1]
        reviews = {}
        for value in values:
            review = self.get_first_review_by_review_value(value)
            if review:
                reviews[review.granted] = review
        if reviews != {}:
            review = reviews[min(reviews.keys())]
            review.granted = determine_yesterday(review.granted)
        else:
            if self.merged is True:
                review = Review(granted=self.last_updated_on)
                review.granted = determine_yesterday(self.last_updated_on)
            else:
                review = Review(granted=self.yesterday)
        self.waiting_first_review = review


class Patchset(object):
    '''
    A Patchset belongs to a Changeset and can be thought of as a commit in Git.

    @param revison: the git reference to a commit
    @type revison: string

    @param uploader_account_id: the id of the developer who uploaded the 
    patchset
    @type: integer

    @param created_on: an instance of datetime.datetime when the @patchset was
    uploaded
    @type created_on: datetime.datetime

    @param change_id: the id of the @Changeset
    @type change_id: integer

    @param patch_set_id: the id of the @Patchset
    @type: integer

    @param draft: Flag to indicate whether patchset is a draft or not.
    @type draft: string

    @param change_open: Flag to indicate whether the patchset is still open or 
    not.
    @type change_open: string

    @param change_sort_key: a key that assists Gerrit in sorting
    @type change_sort_key: string

    @param reviews: instance of OrderedDict that keeps track of all the @Review
    objects that belong to this @Patchset.
    @type reviews: OrderedDict
    '''
    def __init__(self, **kwargs):
        self.revision = kwargs.get('revision')
        self.uploader_account_id = kwargs.get('uploader_acoount_id')
        self.created_on = kwargs.get('created_on')
        self.change_id = kwargs.get('change_id')
        self.patch_set_id = kwargs.get('patch_set_id')
        self.draft = kwargs.get('draft')
        self.change_open = kwargs.get('change_open')
        self.change_sort_key = kwargs.get('change_sort_key')
        self.reviews = OrderedDict()


class Review(object):
    '''
    A Review instance keeps track of all the information related to review
    as made by a developer of patchset. A patchset belongs to a changeid.

    @param change_id: the id of the changeset
    @param type: int

    @param granted: an instance of datetime.datetime of when the review was 
    made.
    @type granted: datetime.datetime

    @param value: how the review was scored, potential values are: -2, -1, 0, 1,
    2.
    @type value: integer

    @param account_id: the id of the developer who reviewed this patchset.
    @type account_id: integer

    @param patch_set_id: the id of the patchset.
    @type patch_set_id: integer

    @param category_id: whether this review was a CodeReview of a Review
    @type category_id: str
    '''
    def __init__(self, **kwargs):
        self.change_id = kwargs.get('change_id')
        self.granted = kwargs.get('granted')
        self.value = kwargs.get('value')
        self.account_id = kwargs.get('account_id')
        self.patch_set_id = kwargs.get('patch_set_id')
        self.category_id = kwargs.get('category_id')
        self.reviewer = Developer(**kwargs)

    def __str__(self):
        return '%s:%s:%s:%s' % (self.change_id, self.patch_set_id,
                                self.category_id, self.value)

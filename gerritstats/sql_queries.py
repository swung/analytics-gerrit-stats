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

from datetime import date

GERRIT_CREATION_DATE = date(2011,9,7)

changes_query = '''
                SELECT 
                    *
                FROM
                    changes
                INNER JOIN 
                    accounts
                ON
                    changes.owner_account_id=accounts.account_id
                ORDER BY
                    changes.created_on;
                '''
    
approvals_query = '''
                SELECT
                    *
                FROM 
                    patch_set_approvals
                INNER JOIN
                    accounts
                ON 
                    patch_set_approvals.account_id=accounts.account_id
                ORDER BY
                    patch_set_approvals.granted;
                '''

patch_sets_query = '''
                SELECT
                    *
                FROM 
                    patch_sets
                LEFT JOIN
                    patch_set_approvals
                ON 
                    patch_sets.change_id=patch_set_approvals.change_id 
                AND 
                    patch_sets.patch_set_id=patch_set_approvals.patch_set_id;
                '''
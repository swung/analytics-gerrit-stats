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
from socket import gethostname
if gethostname() == 'drdee':
    from local import settings
else:
    settings = {
                'database':'reviewdb',
                'passwd':'',
                'host':'localhost',
                'user':'',
                }

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
                WHERE
                    changes.created_on >= %s
                AND
                    changes.created_on <= %s
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
                WHERE
                    patch_set_approvals.granted >= %s
                AND
                    patch_set_approvals.granted <= %s
                ORDER BY
                    patch_set_approvals.granted;
                '''
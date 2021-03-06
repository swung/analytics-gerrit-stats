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
from datetime import datetime, date, timedelta

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')


def determine_yesterday(relative_to=None):
    if relative_to:
        yesterday = relative_to - timedelta(days=1)
    else:
        yesterday = date.today() - timedelta(days=1)
    yesterday = datetime(
        yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    return yesterday


def successful_exit():
    logging.info('Closing down gerrit-stats, no errors.')
    logging.info('Mission accomplished, beanz have been counted.')


def unsuccessful_exit():
    logging.error('Gerrit-stats exited unsuccessfully, please look at the logs for hints on how to fix the problem.')
    logging.error('If the problem remains, contact Diederik van Liere <dvanliere@wikimedia.org>')
    sys.exit(-1)

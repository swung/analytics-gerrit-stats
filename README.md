# Gerrit Code-Review Stats

`gerrit-stats` generates code-review stats based from Gerrit commits.


## Installation

This package is not in PyPi, as it is WMF-specific. Install it by cloning the repo, and then using `pip` or `easy_install`:

```sh
git clone git@less.ly:gerrit-stats.git
pip install gerrit-stats
```

## TODO
1. Add mediawiki extensions parent repo
2. Determine if repo has review enabled
3. Check gerrit 2.4 compatability
4. Add checks to detect schema change
5. This script needs to be puppetized and launched from a cronjob every day at 11:59PM UTC.
    Andrew, maybe you can have a look at this next week?
6. Add developer-centric measures
7. Add active developers metric 
8. Contemplate use of server side db cursor

## Workflow

This initial version generates two metrics on a day-by-day basis:

1. Number of commits that have been completely untouched (no `-1`, `-2`, `+1`, `+2` rating)
2. Number of commits with only `+1`

Unfortunately, it proves (AFAIK) impossible to determine the number of commits per day. Gerrit's
search is so broken that it is not even funny. The NOT operator does not work and you cannot use any
logic when querying for `is:<state>`.

This means that it is hard to put these numbers in context.

1. The scripts will query all gerrit repos, except for the repos that are mentioned in the
    settings.ignore_repos variable. Currently repos containing the word 'test' are ignored.
2. Queries are run using the SSH interface, each repo has it's own dataset. If the file does not
    exist a new file is created with a header line, if the file already exists then the new
    observation is appended.


## Roadmap

### Todo



### Known Issues

- Adding a new metric to existing datasets might not work because of the mismatch between number
    of headings and number of fields. 
- To run gerrit-stats you need an active gerrit ssh account.


## Feedback

Bugs? Feature requests? Feedback? Contact [Diederik van Liere](mailto:dvanliere@wikimedia.org).


## License

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


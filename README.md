# Gerrit Code-Review Stats
This initial version generates two metrics on a day-by-day basis:
1) Number of commits that have been completely untouched, no -1, -2, +1, +2
2) Number of commits with only +1

Unfortunately, it proves (AFAIK) impossible to determine the number of commits per day. Gerrit's search is so broken that it is not even funny. The NOT operator does not work and you cannot use any logic when querying for is:<state> 

This means that it is hard to put these numbers in context. 

Workflow:
1) The scripts will query all gerrit repos, except for the repos that are mentioned in the settings.ignore_repos variable. Currently repos containing the word 'test' are ignored
2) Queries are run using the SSH interface, each repo has it's own dataset. If the file does not exist a new file is created with a header line, if the file already exists then the new observation is appended.

Todolist:
1) This script needs to be puppetized and launched from a cronjob every day at 11:59PM UTC. Andrew, maybe you can have a look at this next week?
2) We need to figure out a way to get total commits per day
3) RIght now each repository has it's own dataset but we need to add functionality in Limn to make logical groups of datasets where the values are summed.

Known Issues
1) Adding a new metric to existing datasets might not work because of the mismatch between number of headings and number of fields. 
2) To run gerrit-stats you need an active gerrit ssh account.



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

# from: https://gerrit.wikimedia.org/r/gitweb?p=mediawiki/tools/release.git;a=blob;f=make-wmf-branch/default.conf;h=a14651276d7a7ff3950e7a614411b6b6eb9d9637;hb=HEAD
# probably needs update once in a while.

extensions = set([
'AbuseFilter',
'ActiveAbstract', #Used as part of dumpBackup
'AntiBot',
'AntiSpoof',
'ApiSandbox',
'ArticleFeedback',
'ArticleFeedbackv5',
'AssertEdit',
'Babel',
'CategoryTree',
'CentralAuth',
'CentralNotice',
'CharInsert',
'CheckUser',
'Cite',
'cldr',
'ClickTracking',
'ClientSide',
'CodeReview',
'Collection',
'CommunityApplications',
'CommunityHiring',
'CommunityVoice',
'ConditionalShowSection',
'ConfirmEdit',
'ContactPage',
'ContactPageFundraiser',
'Contest',
'ContributionReporting',
'ContributionTracking',
'CustomUserSignup',
'DisableAccount',
'DismissableSiteNotice',
'DonationInterface',
'DoubleWiki',
'EditPageTracking',
'EducationProgram',
'EmailCapture',
'ExpandTemplates',
'ExtensionDistributor',
'FeaturedFeeds',
'FormPreloadPostCache', #Foundation wiki
'FundraiserLandingPage',
'Gadgets',
'GlobalBlocking',
'GlobalUsage',
'GoogleNewsSitemap',
'ImageMap',
'InputBox',
'intersection',
'Interwiki',
'LabeledSectionTransclusion',
'LandingCheck',
'LastModified',
'LiquidThreads',
'LocalisationUpdate',
'MWSearch',
'MarkAsHelpful',
'Math',
'MobileFrontend',
'MoodBar',
'Narayam',
'NewUserMessage',
'normal',
'Nuke',
'OAI',
'OggHandler',
'OpenSearchXml',
'Oversight',
'PagedTiffHandler',
'PageTriage',
'ParserFunctions',
'PdfHandler',
'Poem',
'PoolCounter',
'PrefSwitch', #Still used by SimpleSurvey... (nfi why)...
'ProofreadPage',
'Quiz',
'RandomRootPage',
'ReaderFeedback',
'Renameuser',
'RSS',
'ScanSet',
'SecurePoll',
'ShortUrl',
'SimpleAntiSpam',
'SimpleSurvey',
'SiteMatrix',
'SkinPerPage', #Foundation wiki
'skins', #Foundation wiki
'SpamBlacklist',
'StrategyWiki',
'StringFunctionsEscaped',
'SubPageList3',
'SwiftCloudFiles',
'SyntaxHighlight_GeSHi',
'timeline',
'TitleBlacklist',
'TitleKey',
'TorBlock',
'Translate',
'TranslationNotifications',
'TrustedXFF',
'UnicodeConverter',
'UploadBlacklist',
'UploadWizard',
'UserDailyContribs',
'UserThrottle',
'Vector',
'VipsScaler',
'VisualEditor',
'WebFonts',
'wikidiff2',
'wikihiero',
'WikiEditor',
'WikiLove',
'WikimediaIncubator',
'WikimediaMaintenance',
'WikimediaMessages',
'WikimediaShopLink',
'ZeroRatedMobileAccess',
 ])
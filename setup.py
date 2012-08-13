#!python
# -*- coding: utf-8 -*-
import re
from os.path import dirname, abspath, join
from setuptools import setup, find_packages

HERE = abspath(dirname(__file__))
readme = open(join(HERE, 'README.md'), 'rU').read()

package_file = open(join(HERE, 'gerritstats/__init__.py'), 'rU')
__version__ = re.sub(
    r".*\b__version__\s+=\s+'([^']+)'.*",
    r'\1',
    [ line.strip() for line in package_file if '__version__' in line ].pop(0)
)


setup(
    name             = 'gerrit-stats',
    version          = __version__,
    description      = 'Generate codereview stats based from Gerrit commits',
    long_description = readme,
	url              = 'https://gerrit.wikimedia.org/gitweb/analytics/gerrit-stats.git',
    
    author           = 'Diederik van Liere',
    author_email     = 'dvanliere@wikimedia.org',
    
    packages         = find_packages(),
    entry_points     = { 'console_scripts':['gerrit-stats = gerritstats:main'] },
	install_requires = [
		'MySQL-python','paramiko','pycrypto','argparse','yaml',
	],

    # install_requires = [
    #     "bunch  >= 1.0",
    #     "PyYAML >= 3.10",
    # ],
    
    keywords         = ['gerrit', 'stats'],
    classifiers      = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Utilities"
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GPLv2 License",
    ],
    zip_safe = False,
    license  = "GPLv2",
)

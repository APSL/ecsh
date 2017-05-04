# -*- coding: utf-8 -*-

from sys import version_info

from setuptools import setup

if version_info.major != 3:
    raise OSError("Python 3 is required")

INSTALL_REQUIRES = [
    'click',
    'boto3',
    'sh',
]

setup(
    name='ecsh',
    version='0.2.1',
    packages=['ecsh'],
    url=u"https://github.com/apsl/ecsh",
    license='GPLv3',
    install_requires=INSTALL_REQUIRES,
    entry_points="""
        [console_scripts]
        ecsh=ecsh.ecsh:ecsh
    """,
    author=u"Bartomeu Miro Mateu",
    author_email=u"bmiro@apsl.net",
    description=u"Cli tool to access Amazon ECS containers with a shell"
)

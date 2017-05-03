# -*- coding: utf-8 -*-

from setuptools import setup


INSTALL_REQUIRES = [
    'click',
    'boto3',
    'sh',
]

setup(
    name='ecsh',
    version='0.0.1',
    packages=['ecsh'],
    url=u"https://github.com/apsl/ecsh",
    license='GPLv3',
    install_requires=INSTALL_REQUIRES,
    entry_points="""
        [console_scripts]
        ecsh=ecsh.ecsh:ecsh
    """,
    author=u"Bartomeu Miro Mateu",
    author_email=u"bartomeumiro at apsl dot net",
    description=u"Cli tool to access Amazon ECS containers with a shell"
)



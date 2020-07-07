# Copyright 2019 WHG (International) Limited. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
import json

from setuptools import find_packages
from setuptools import setup

NAME = 'defectdojo-reporting'
VERSION = '1.0.0'

install_requires = []
tests_require = []

with open('Pipfile.lock') as fd:
    lock_data = json.load(fd)
    install_requires = [
        package_name + package_data['version']
        for package_name, package_data in lock_data['default'].items() \
            if package_data.get('version')
    ]
    install_requires += [
        package_name + '@git+' + package_data['git'] + '#egg=' + package_data['ref']
        for package_name, package_data in lock_data['default'].items() \
            if package_data.get('git')
    ]
    tests_require = [
        package_name + package_data['version']
        for package_name, package_data in lock_data['develop'].items() \
            if package_data.get('version')
    ]

setup(
    name=NAME,
    version=VERSION,
    description='CCVS API Client',
    author='Ederson Brilhante',
    author_email='ederson.brilhante@grandparade.co.uk',
    url='https://github.com/William-Hill-Online/defectdojo-reporting',
    keywords=['CCVS API'],
    install_requires=install_requires,
    tests_require=tests_require,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'defectdojo-reporting=defectdojo_reporting.cli:main',
        ],
    },
    long_description="""\
        Client for sending reports to DefectDojo
    """
)

#  Copyright: Copyright (c) 2020., <AUTHOR>
#  Author: <AUTHOR> <EMAIL>
#  License: See LICENSE.txt

import pathlib
from setuptools import setup
from distutils.util import convert_path

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# Get values from the about file
plg_ns = {}
about_path = convert_path('beetsplug/similarity/about.py')
with open(about_path) as about_file:
    exec(about_file.read(), plg_ns)

setup(
    name=plg_ns['__PACKAGE_NAME__'],
    version=plg_ns['__version__'],
    description=plg_ns['__PACKAGE_DESCRIPTION__'],
    author=plg_ns['__author__'],
    author_email=plg_ns['__email__'],
    url=plg_ns['__PACKAGE_URL__'],
    license='MIT',
    long_description=README,
    long_description_content_type='text/markdown',
    platforms='ALL',

    include_package_data=True,
    packages=['beetsplug.similarity'],

    python_requires='>=3.6',

    install_requires=[
        'beets>=1.6.0', 'confuse'
    ],
    classifiers=[
        'Topic :: Multimedia :: Sound/Audio',
        'License :: OSI Approved :: MIT License',
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
)

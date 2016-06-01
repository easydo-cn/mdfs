# coding: utf-8
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md'), encoding='utf-8').read()
except TypeError:
    README = open(os.path.join(here, 'README.md')).read()

setup(
    name='mdfs',
    version='0.1',
    author = "panjy",
    author_email = "panjunyong@gmail.com",
    description = "Multiple Device File Storage",
    long_description=README,
    license = "GPL",
    classifiers = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        ],
    url = 'https://github.com/easydo-cn/mdfs',
    packages = find_packages(),
    include_package_data = True,
    install_requires = [
         'setuptools',
         'oss2',
        ],
    zip_safe = False,
    entry_points = """
    """
)

################################
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup (
    name='mdfs',
    version='0.1',
    author = "panjy",
    author_email = "panjunyong@gmail.com",
    description = "Site file storage",
    long_description=README,
    license = "GPL",
    classifiers = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        ],
    url = 'http://github.com/easydo-cn/sfs',
    packages = find_packages(),
    include_package_data = True,
    install_requires = [
         'setuptools',
         # tests only
        ],
    zip_safe = False,
    entry_points = """
    """
)

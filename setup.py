from setuptools import setup
import os

THIS_DIR = os.path.dirname(__file__)

try:
    import pypandoc
    _long_description = pypandoc.convert(
        source='README.md',
        format='markdown_github',
        to='rst',
        outputfile='README.rst')
except(IOError, ImportError):
    _long_description = open('README.md').read()

_author = 'Alex Goodman'
_email = 'alexander.goodman@jpl.nasa.gov'

setup(
    name =            	'binconvert',
    version =         	'0.1.0',
    description =     	'Converts byte ordering in binary files from one '
                        'platform to another',
    long_description = 	_long_description,
    author =          	_author,
    author_email =    	_email,
    maintainer =        _author,
    maintainer_email =  _email,
    url =             	'https://github.com/agoodm/binconvert',
    platforms =         ['any'],
    install_requires =  ['pyyaml'],
    license =           'MIT',
    test_suite =        'tests',
    include_package_data = True,
    package_data =      {
        '': ['README.md', 'LICENSE']
    },
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    zip_safe = False,
    py_modules=['convert'],
    entry_points={
        'console_scripts': ['bconv = convert:main',],
    })

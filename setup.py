"""

XXX


"""


try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(name='nimsdata',
    packages=['nimsdata', 'nimsdata.pfile'],
    package_data={'nimsdata':['nimsdata/*.py'],
                  'nimsdata.pfile':[ 'nimsdata/pfile/*.py']})

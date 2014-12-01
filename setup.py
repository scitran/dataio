"""

XXX


Dependencies:
-dcmstack
-pymongo
-bson
"""

from distutils.core import setup

setup(name='nimsdata',
      packages = ['nimsdata', 'nimsdata.pfile', 'nimsdata.medimg'],
      package_dir = {'nimsdata':'.', 'nimsdata.pfile': './pfile'},
      package_data={'nimsdata': ['./*.py', './*.json'],
                    'nimsdata.pfile':[ './pfile/*.py'],
                    'nimsdata.medimg': ['./medimg/*.py']})

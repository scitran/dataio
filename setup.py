"""

XXX


Dependencies:
-dcmstack
-pymongo
-bson
"""

from distutils.core import setup

setup(name='nimsdata',
      packages = ['nimsdata', 'nimsdata.pfile', 'nimsdata.medimg',
                  'nimsdata.medimg.dcm','nimsdata.medimg.dcm.mr'],
      package_dir = {'nimsdata':'.', 'nimsdata.pfile': './pfile'},
      package_data={'nimsdata': ['./*.py', './*.json'],
                    'nimsdata.pfile':[ './pfile/*.py'],
                    'nimsdata.medimg': ['./medimg/*.py'],
                    'nimsdata.medimg.dcm':['./medimg/dcm/*.py'],
                    'nimsdata.medimg.dcm.mr':['./medimg/dcm/mr/*.py']
          })

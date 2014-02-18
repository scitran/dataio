"""

XXX


"""

from distutils.core import setup

setup(name='nimsdata',
      packages = ['nimsdata', 'nimsdata.pfile'],
      package_dir = {'nimsdata':'.', 'nimsdata.pfile': './pfile'},
      package_data={'nimsdata': ['./*.py'],
                    'nimsdata.pfile':[ './pfile/*.py']})

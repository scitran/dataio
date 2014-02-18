"""

XXX


"""

from distutils.core import setup

setup(name='nimsdata',
      py_modules=['mkpfile',
                  'nimsbehavior',
                  'nimsdata',
                  'nimsdicom',
                  'nimsmontage',
                  'nimsmrdata',
                  'nimsnifti',
                  'nimsphysio',
                  'nimspng',
                  'tempdir',
                  'nimsraw'],
    packages=['pfile'],
    package_data={'pfile':[ 'nimsdata/pfile/*.py']})

# @author:  Gunnar Schaefer

import os
import glob


for mod in [os.path.basename(f)[:-3] for f in glob.glob(os.path.dirname(__file__) + '/nims*.py')]:
    __import__(mod, globals())
del f, mod

def __all_subclasses(cls):
    subclasses = []
    for sc in cls.__subclasses__():
        subclasses += [sc] + __all_subclasses(sc)
    return subclasses

nimsdata.subclasses = sorted(
        filter(lambda cls: not bool(getattr(cls, '__abstractmethods__')), __all_subclasses(nimsdata.NIMSData)),
        key=lambda sc: sc.parse_priority,
        reverse=True
        )

parse = nimsdata.NIMSData.parse
NIMSData = nimsdata.NIMSData
NIMSDataError = nimsdata.NIMSDataError

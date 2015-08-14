"""
scitran.data.meeg
=================

Data format for M/EEG data using mne-python.

"""

import logging
import bson
import abc

from .. import data

log = logging.getLogger(__name__)  # root logger already configured

# see data.py for expected project properties
project_properties = data.project_properties

_session_properties = {  # add additional session properties
    'subject': {
        'type': 'object',
        'properties': {
            'firstname': {
                'field': 'subj_firstname',
                'title': 'First Name',
                'type': 'string',
            },
            'lastname': {
                'field': 'subj_lastname',
                'title': 'Last Name',
                'type': 'string',
            },
            'dob': {
                'field': 'subj_dob',
                'title': 'Date of Birth',
                'type': 'string',
                'format': 'date',
            },
        },
    },
}
session_properties = data.dict_merge(data.session_properties,
                                     _session_properties)

_acquisition_properties = {  # add custom acquisition properties
}
acquisition_properties = data.dict_merge(data.acquisition_properties,
                                         _acquisition_properties)


class MEEGError(data.DataError):
    pass


class MEEGReader(data.Reader):

    """
    Parameters
    ----------
    path : str
        path to input file
    load_data : boolean
        indicate if a reader should attempt to immediately load all data.
        Default False.
    """
    project_properties = project_properties
    session_properties = session_properties
    acquisition_properties = acquisition_properties

    domain = u'meeg'
    filetype = u'FIF'   # filetype within meeg domain
    state = ['orig']             # usually an 'orig' raw file gets 'reaped'

    @abc.abstractmethod
    def __init__(self, path, load_data=False):
        super(MEEGReader, self).__init__(path, load_data)

    @abc.abstractmethod
    def load_data(self):
        super(MEEGReader, self).load_data()

    @property
    def nims_metadata_status(self):
        return self.metadata_status

    @property
    def nims_group_id(self):
        return self.group_name

    @property
    def nims_project(self):
        return self.project_name

    @property
    def nims_session_id(self):
        return self.exam_uid

    @property
    def nims_session_label(self):
        return (self.study_datetime and
                self.study_datetime.strftime('%Y-%m-%d %H:%M'))

    @property
    def nims_session_subject(self):
        return self.subj_code

    @property
    def nims_acquisition_id(self):
        return 'not implemented'

    @property
    def nims_acquisition_label(self):
        if self.acq_no is not None:
            return '%d.%d' % (self.series_no, self.acq_no)
        else:
            return str(self.series_no)

    @property
    def nims_acquisition_description(self):
        return self.series_desc

    @property
    def nims_file_name(self):
        if self.acquisition_id:  # as in pfile json header
            return self.acquisition_id + '_' + self.filetype
        extra = '_' + str(self.acq_no) if self.acq_no is not None else ''
        return self.series_uid + extra + '_' + self.filetype

    @property
    def nims_file_ext(self):
        return '.tgz'

    @property
    def nims_file_domain(self):
        return self.domain

    @property
    def nims_file_type(self):
        return self.filetype

    @property
    def nims_file_kinds(self):
        # this really SHOULDn't be scan_type, because not all medical images
        # will set a scan type
        # pick a more general name. that is suitable for non-scan type
        # or define this property in EVERY class...
        return [self.scan_type]

    @property
    def nims_file_state(self):
        return self.state

    @property
    def nims_timestamp(self):
        return self.timestamp.replace(tzinfo=bson.tz_util.FixedOffset(-7 * 60, 'pacific')) if self.timestamp else None # FIXME: use pytz

    @property
    def nims_timezone(self):
        pass  # FIXME


class MEEGWriter(data.Writer):

    """
    Base MR data writer class.

    Cannot be instantiated.

    """

    def write(cls, metadata, imagedata, outbase):
        super(MEEGWriter, cls).write(metadata, imagedata, outbase)

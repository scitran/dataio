"""
scitran.data.eegmeg
===================

duh-docs duh-docs duh-docs duh-docs-docs-docs. plz. kthnxbai.

"""

import logging
import abc
from bson.tz_util import FixedOffset

import mne

from .. import data

log = logging.getLogger(__name__)  # root logger already configured

# see data.py for expected project properties
project_properties = data.project_properties

_session_properties = {  # add additional session properties
    'exam_uid': {
        'field': 'exam_uid',
        'title': 'DICOM UID',
        'type': 'string',
    },
    'exam': {
        'field': 'exam_no',
        'title': 'Exam Number',
        'type': 'integer',
    },
    'patient_id': {
        'field': 'patient_id',
        'title': 'Patient ID',
        'type': 'string',
    },
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
            'sex': {
                'field': 'subj_sex',
                'title': 'Sex',
                'type': 'string',
                'enum': ['male', 'female'],
            },
        },
    },
    'instrument': {
        # FIXME: should be surrounded by an array of multiple instruments
        'title': 'Instrument',
        'type': 'object',
        'properties': {
            'manufacturer': {
                'field': 'manufacturer',
                'title': 'Manufacturer',
                'type': 'string',
            },
            'model': {
                'field': 'manufacturer_model',
                'title': 'Model',
                'type': 'string',
            },
            'uid': {
                'field': 'scanner_name',
                'title': 'ID',
                'type': 'string',
            },
        },
    },
}
session_properties = data.dict_merge(data.session_properties,
                                     _session_properties)

_acquisition_properties = {  # add custom acquisition properties
    'series_uid': {
        'field': 'series_uid',
        'title': 'DICOM UID',
        'type': 'string',
    },
    'series': {
        'field': 'series_no',
        'title': 'Series',
        'type': 'integer',
    },
    'acquisition': {
        'field': 'acq_no',
        'title': 'Acquisition',
        'type': 'integer',
    },
    'psd': {
        'field': 'psd_name',
        'title': 'PSD',
        'type': 'string',
        'maxLength': 64,
    },
    'tr': {
        'field': 'tr',
        'title': 'Tr',
        'type': 'number',
    },
    'te': {
        'field': 'te',
        'title': 'Te',
        'type': 'number',
    },
    'ti': {
        'field': 'ti',
        'title': 'Ti',
        'type': 'number',
    },
    'flip_angle': {
        'field': 'flip_angle',
        'title': 'Flip Angle',
        'type': 'integer',
    },
    'pixel_bandwidth': {
        'field': 'pixel_bandwidth',
        'title': 'Pixel Bandwidth',
        'type': 'number',
    },
    'num_averages': {
        'field': 'num_averages',
        'title': 'Averages',
        'type': 'integer',
    },
    'num_bands': {
        'field': 'num_bands',
        'title': 'Bands',
        'type': 'integer',
    },
    'num_echos': {
        'field': 'num_echos',
        'title': 'Echos',
        'type': 'integer',
    },
    'num_slices': {
        'field': 'num_slices',
        'title': 'Slices',
        'type': 'integer',
    },
    'num_timepoints': {
        'field': 'num_timepoints',
        'title': 'Time Points',
        'type': 'integer',
    },
    'rx_coil': {
        'field': 'receive_coil_name',
        'title': 'Coil',
        'type': 'string',
        'maxLength': 64,
    },
    'num_receivers': {
        'field': 'num_receivers',
        'title': 'Receivers',
        'type': 'integer',
    },
    'protocol': {
        'field': 'protocol_name',
        'title': 'Protocol',
        'type': 'string',
        'maxLength': 64,
    },
    'size': {
        'title': 'Size',
        'type': 'object',
        'properties': {
            'x': {
                'field': 'size_x',
                'title': 'X',
                'type': 'integer',
            },
            'y': {
                'field': 'size_y',
                'title': 'Y',
                'type': 'integer',
            },
        },
    },
    'fov': {
        'title': 'Field of View',
        'type': 'object',
        'properties': {
            'x': {
                'field': 'fov_x',
                'title': 'X',
                'type': 'integer',
            },
            'y': {
                'field': 'fov_y',
                'title': 'Y',
                'type': 'integer',
            },
        },
    },
    'mm_per_voxel': {
        'title': 'mm per Voxel',
        'type': 'object',
        'properties': {
            'x': {
                'field': 'mm_per_vox_x',
                'title': 'X',
                'type': 'number',
            },
            'y': {
                'field': 'mm_per_vox_y',
                'title': 'Y',
                'type': 'number',
            },
            'z': {
                'field': 'mm_per_vox_z',
                'title': 'Z',
                'type': 'number',
            },
        },
    },
    'effective_echo_spacing': {
        'field': 'effective_echo_spacing',
        'title': 'Effective Echo Spacing',
        'type': 'number',
    },
    'phase_encode_direction': {
        'field': 'phase_encode_direction',
        'title': 'Phase-encode Direction',
        'type': 'integer',
    },
    'duration': {
        'field': 'duration',
        'title': 'Duration',
        'type': 'number',
    },
    'prescribed_duration': {
        'field': 'prescribed_duration',
        'title': 'Prescribed Duration',
        'type': 'number',
    },
    'slice_encode_undersample': {
        'field': 'slice_encode_undersample',
        'title': 'Slice Encode Undersample',
        'type': 'integer',
    },
    'phase_encode_undersample': {
        'field': 'phase_encode_undersample',
        'title': 'Phase Encode Undersample',
        'type': 'integer',
    },
    'device': {
        'field': 'scanner_name',
        'title': 'Device',
        'type': 'string',
        'maxLength': 64,
    },
    'acquisition_matrix': {
        'title': 'Acquisition Matrix',
        'type': 'object',
        'properties': {
            'x': {
                'field': 'acquisition_matrix_x',
                'title': 'X',
                'type': 'number',
            },
            'y': {
                'field': 'acquisition_matrix_y',
                'title': 'Y',
                'type': 'number',
            },
        },
    },
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
        Default: False.
    """
    project_properties = project_properties
    session_properties = session_properties
    acquisition_properties = acquisition_properties

    domain = u'meeg'
    filetype = u'FIF'   # filetype within meeg domain
    state = ['orig']             # usually an 'orig' raw file gets 'reaped'

    def __init__(self, path, load_data=False):
        super(MEEGReader, self).__init__(path, load_data)

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
        return ('%d.%d' % (self.series_no, self.acq_no)
                if self.acq_no is not None else str(self.series_no))

    @property
    def nims_acquisition_description(self):
        return self.series_desc

    @property
    def nims_file_name(self):
        if self.acquisition_id:  # as in pfile json header
            return self.acquisition_id + '_' + self.filetype
        return (self.series_uid + ('_' + str(self.acq_no)
                if self.acq_no is not None else '') + '_' + self.filetype)

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
        # this really SHOULDn't be scan_type, because not all medical
        # images will set a scan type
        # pick a more general name. that is suitable for non-scan type
        # or define this property in EVERY class...
        return [self.scan_type]

    @property
    def nims_file_state(self):
        return self.state

    @property
    def nims_timestamp(self):
        return (self.timestamp.replace(tzinfo=FixedOffset(-7 * 60, 'pacific'))
                if self.timestamp else None)  # FIXME: use pytz

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

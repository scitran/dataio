"""
scitran.data.meeg
=================

Data format for M/EEG data using mne-python.

"""

import logging
import tempfile
import zipfile
import json
import warnings
import os
from os import path as op
import shutil

from mne.io import read_raw_fif

from .. import data, util

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
        Path to input file.
    load_data : boolean
        Indicate if a reader should attempt to immediately load all data.
        Default False.
    """
    project_properties = project_properties
    session_properties = session_properties
    acquisition_properties = acquisition_properties

    domain = u'meeg'
    filetype = u'meeg'
    state = ['orig']

    def __init__(self, path, load_data=False, timezone=None):
        super(MEEGReader, self).__init__(path, load_data, timezone)
        self._temp_dir = tempfile.mkdtemp()
        os.mkdir(op.join(self._temp_dir, 'reap'))
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zip_file:
                hdr = json.loads(zip_file.comment,
                                 object_hook=util.datetime_decoder)['header']
                self.project_name = hdr['project']
                zip_fnames = [op.join('reap', op.basename(fname))
                              for fname in zip_file.namelist()]
                fnames = []
                for fname in zip_fnames:
                    if fname.endswith('.fif'):
                        fnames.append(zip_file.extract(fname, self._temp_dir))
                # load raw files
                with warnings.catch_warnings(record=True):
                    self._raws = [read_raw_fif(fname, allow_maxshield=True,
                                               preload=load_data)
                                  for fname in fnames]
        except Exception as e:
            raise MEEGError(e)

    def __del__(self):
        shutil.rmtree(self._temp_dir)

    def load_data(self):
        super(MEEGReader, self).load_data()
        for raw in self._raws:
            raw.preload_data()

    @property
    def nims_project(self):
        return self.project_name

    @property
    def nims_group_id(self):
        # XXX
        return 'group_id'

    @property
    def nims_session_id(self):
        # XXX
        return 'session_id'

    @property
    def nims_session_label(self):
        # XXX
        return 'session_label'

    @property
    def nims_session_subject(self):
        # XXX
        return 'subj_code'

    @property
    def nims_acquisition_label(self):
        # XXX
        return 'series_no'

    @property
    def nims_acquisition_description(self):
        # XXX get from info
        return 'foobar'

    @property
    def nims_file_name(self):
        # XXX what are the constraints on this?
        return 'foo'

    @property
    def nims_file_kinds(self):
        # XXX
        return ['FIF']

    @property
    def nims_acquisition_id(self):
        # XXX
        return 'nims_acquisition_id'

    # XXX why are these not implemented at the data.Reader level?

    @property
    def nims_timestamp(self):
        return super(MEEGReader, self).nims_timestamp

    @property
    def nims_timezone(self):
        return super(MEEGReader, self).nims_timezone

    @property
    def nims_metadata_status(self):
        return self.metadata_status

    @property
    def nims_file_ext(self):
        return '.zip'

    @property
    def nims_file_domain(self):
        return self.domain

    @property
    def nims_file_type(self):
        return self.filetype

    @property
    def nims_file_state(self):
        return self.state

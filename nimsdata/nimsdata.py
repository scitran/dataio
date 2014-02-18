# @author:  Gunnar Schaefer
#           Bob Dougherty

import abc

subclasses = []


class NIMSDataError(Exception):
    pass


class NIMSData(object):

    __metaclass__ = abc.ABCMeta

    parse_priority = 0

    _session_properties = {
            'name': {
                'attribute': 'nims_session_name',
                'title': 'Name',
                'type': 'string',
                'maxLength': 32,
            },
            'subject': {
                'attribute': 'nims_session_subject',
                'title': 'Subject',
                'type': 'string',
                'maxLength': 16,
            },
            'datatype': {
                'attribute': 'nims_session_type',
                'title': 'Type',
                'type': 'array',
            },
            'timestamp': {
                'title': 'Timestamp',
                'type': 'string',
                'format': 'date-time',
            },
            'timezone': {
                'title': 'Timezone',
                'type': 'string',
            },
    }
    session_properties = _session_properties

    _epoch_properties = {
            'name': {
                'attribute': 'nims_epoch_name',
                'title': 'Name',
                'type': 'string',
                'maxLength': 32,
            },
            'description': {
                'attribute': 'nims_epoch_description',
                'title': 'Description',
                'type': 'string',
                'maxLength': 64,
            },
            'datatype': {
                'attribute': 'nims_epoch_type',
                'title': 'Type',
                'type': 'string',
                'maxLength': 32,
            },
            'timestamp': {
                'attribute': 'nims_timestamp',
                'title': 'Timestamp',
                'type': 'string',
                'format': 'date-time',
            },
            'timezone': {
                'attribute': 'nims_timezone',
                'title': 'Timezone',
                'type': 'string',
            },
    }
    epoch_properties = _epoch_properties

    @staticmethod
    def parse(filepath):
        for sc in subclasses:
            try:
                dataset = sc(filepath)
            except NIMSDataError:
                dataset = None
            else:
                break
        else:
            raise NIMSDataError('%s could not be parsed' % filepath)
        return dataset

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractproperty
    def nims_group(self):
        pass

    @abc.abstractproperty
    def nims_experiment(self):
        pass

    @abc.abstractproperty
    def nims_session(self):
        pass

    @abc.abstractproperty
    def nims_epoch(self):
        pass

    @abc.abstractproperty
    def nims_type(self):
        pass

    @abc.abstractproperty
    def nims_filename(self):
        pass

    @abc.abstractproperty
    def nims_timestamp(self):
        pass

    @abc.abstractproperty
    def nims_timezone(self):
        pass

    @property
    def nims_session_name(self):
        pass

    @property
    def nims_session_subject(self):
        pass

    @property
    def nims_session_type(self):
        pass

    @property
    def nims_epoch_name(self):
        pass

    @property
    def nims_epoch_description(self):
        pass

    @property
    def nims_epoch_type(self):
        pass


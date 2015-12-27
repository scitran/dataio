#!/usr/bin/env python
# @author:  Gunnar Schaefer
#           Bob Dougherty
#           Kevin S. Hahn

"""
scitran.data.data
=================

provides base classes for scitran data related exceptions and an abstract implementation of a reader
object. scitran.data.data module provides base classes for Exceptions, Readers and Writers.
Also provides the scitran data command line interface. The Reader object is meant to be subclassed
to create abstract classes for data domains (e.g. MRData) and concrete classes for domain specific
data type (e.g. Dicom).

In some cases, such as with MR data, there are functions and definitions that are used by multiple
data types, such as MR Dicoms, MR Nifti, and MR PFiles, all may want to manipulate metadata in the
same way.  In these cases, it may be more prudent to add an abstract base class for your data
domain, and several seperate data type specific classes.

see :doc:`extending_data` for more information on creating a new reader
subclass.

SciTran data are organized in a group, project, session, acquisition hierarchy.
A group is approximately equivalent to a university research lab.
The group "owns" the project. If the provided group does not exist,
data will end up in the "unknown" group.
By default, live.sh provisions a "scitran" group.
"""

import os
import abc
import copy
import json
import pytz
import logging
import zipfile
import warnings
import datetime
import traceback

import util


log = logging.getLogger(__name__)
warnings.simplefilter('ignore', FutureWarning)

READERS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'readers.json')))
WRITERS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'writers.json')))
MODULES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules.json')))


project_properties = {
        'gid': {
            'field': 'nims_group_id',
            'type': 'string',
        },
        'group': {
            'title': 'Group',
            'type': 'string',
            # FIXME: dynamically add enum of all possible groups
        },
        'name': {
            'field': 'nims_project',
            'title': 'Name',
            'type': 'string',
            'maxLength': 32,
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

session_properties = {
        'uid': {
            'field': 'nims_session_id',
            'type': 'string',
        },
        'label': {
            'field': 'nims_session_label',
            'title': 'Label',
            'type': 'string',
            'maxLength': 32,
        },
        'subject': {
            'title': 'Subject',
            'type': 'object',
            'properties': {
                'code': {
                    'field': 'nims_session_subject',
                    'title': 'Code',
                    'type': 'string',
                    'maxLength': 16,
                },
            },
        },
        'type': {
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

acquisition_properties = {
        'uid': {
            'field': 'nims_acquisition_id',
            'type': 'string',
        },
        'label': {
            'field': 'nims_acquisition_label',
            'title': 'Label',
            'type': 'string',
            'maxLength': 32,
        },
        'description': {
            'field': 'nims_acquisition_description',
            'title': 'Description',
            'type': 'string',
            'maxLength': 64,
        },
        'datatype': {
            'title': 'Datatype',
            'type': 'array',
        },
        'timestamp': {
            'field': 'nims_timestamp',
            'title': 'Timestamp',
            'type': 'string',
            'format': 'date-time',
        },
        'timezone': {
            'field': 'nims_timezone',
            'title': 'Timezone',
            'type': 'string',
        },
        'filetype': {
            'field': 'nims_file_type',
            'title': 'Filetype',
            'type': 'string',
        },
        'state': {
            'field': 'nims_file_state',
            'title': 'State',
            'type': 'string',
        },
}


def module_by_type(domain_kind):
    """
    Retrieve a module based on tuple(domain, kind).

    Parameters
    ----------
    domain_kind : 2-item tuple
        Tuple of data domain and kind. kind can be None.

    Returns
    -------
    mod : module
        module that defines the properties for (domain, kind).

    Raises
    ------
    DataError
        Unable to import the module specified by (domain, kind) in modules.json.

    """
    domain, kind = domain_kind[0], domain_kind[1]
    mod_name = MODULES.get('%s.%s' % (domain, kind)) if (domain and kind) else MODULES.get(domain)
    try:
        mod = __import__(mod_name, globals())
    except (ImportError, TypeError):
        raise DataError('no module matches that domain/datatype %s' % mod_name, log_level=logging.ERROR)
    return mod


def dict_merge(a, b=None, in_place=False):
    """
    Recursively merge dictionaries.

    If a and b are both dictionaries, merge them. If a is a list of dicionaries, b must be None,
    then merge all the dictionaries.

    Parameters
    ----------
    a : dict or list
        dictionary, or list of dicionaries to merge.
    b : dict or None
        dictionary or None.  if a is a list, b must be None.
    in_place : bool [default False]
        False creates a deep copy of dict a. dict a is not modified.
        True merges dict a with dict b, altering dict a. dict a is modified.

    Returns
    -------
    merged : dict
        dictionary of dict b merged into dict a.

    Raises
    ------
    DataError
        inputs were of unexpected types.  Inputs must be two dictionaries, or one list.

    """
    if isinstance(a, dict) and isinstance(b, dict):
        result = copy.deepcopy(a) if not in_place else a
        for k, v in b.iteritems():
            if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v, in_place=True)
            else:
                result[k] = copy.deepcopy(v)
        return result
    elif isinstance(a, list) and b is None:
        result = copy.deepcopy(a[0]) if not in_place else a[0]
        for b in a[1:]:
            result = dict_merge(result, b, in_place=True)
    else:
        raise DataError('inputs must be two dictionaries, or a list of dicionaries',
                            log_level=logging.ERROR)
    return result


def acquisition_properties_by_type_list(type_list):
    """
    Assemble acquisition properties from list of types.

    Parameters
    ----------
    type_list : list
        list of two-item (domain, kind) tuples.

    Returns
    -------
    merged_dict : dict
        merged acquisition properties for items in type_list.

    """
    return dict_merge([module_by_type(t).acquisition_properties for t in type_list])


def session_properties_by_type_list(type_list):
    """
    Assemble session properties from list of types.

    Parameters
    ----------
    type_list : list
        list of two item (domain, kind) tuples.

    Returns
    -------
    merged_dict : dict
        merged session properties for items in type_list.

    """
    return dict_merge([module_by_type(t).session_properties for t in type_list])


def project_properties_by_type_list(type_list):
    """
    Assemble project properties from list of types.

    Parameters
    ----------
    type_list : list
        list of two-item (domain, kind) tuples.

    Returns
    -------
    merged_dict : dict
        merged project properties for items in type_list.

    """
    return dict_merge([module_by_type(t).project_properties for t in type_list])


def get_handler(filetype, handlerdict):
    """
    Retrieve the class object of reader or writer from its string label.

    Parameters
    ----------
    name : str
        reader or writer name
    handlerdict : dict
        name of which handler dict to search from, READERS or WRITERS.

    Returns
    -------
    handler : Reader or Writer subclass
        Reader or Writer object.

    Raises
    ------
    DataError
        The specified handler does not exist, or cannot be imported

    """
    try:
        mod, klass = map(str, handlerdict.get(filetype).rsplit('.', 1))
        handler = getattr(__import__(mod, globals(), fromlist=[klass]), klass)
    except (ImportError, AttributeError):
        raise DataError('no handler for filetype %s' % filetype, log_level=logging.ERROR)
    return handler


def get_reader(filetype):
    return get_handler(filetype, READERS)


def get_writer(filetype):
    return get_handler(filetype, WRITERS)


def parse(path, filetype=None, load_data=False, ignore_json=False, debug=False, **kwargs):
    """
    Parse the file at path with a filetype-specific parser.

    The parse function expects a zip file with a comment containing json metadata.
    The json should declare the filetype, and any metadata that should be overwritten.

    This function will pass the input file to the appropriate handler,
    if available.

    =========== ======== ===================================================
    ignore_json filetype behavior
    =========== ======== ===================================================
    False       None     **DEFAULT** try to read json, use parser from json.
    False       'dicom'  try to read json, use 'dicom' parser.
    True        None     **INVALID**
    True        'dicom'  don't try to read json, use 'dicom' parser.
    =========== ======== ===================================================

    Parameters
    ----------
    path : str
        path to input file.
    filetype : str
        string name of parser to use.  no special search or inferences will be made if this option
        is specified.
    load_data : bool  [default False]
        attempt to load all metadata and data at parse.  like running parse, then load_data
    ignore_json : bool [default False]
        True, don't look for json file. therefore the parser cannot be read from the json, and a
        parser MUST be specfied if ignore_json is true. False, do look for json file.
    debug : bool [default False]
        developer option, False masks all exceptions as DataError.  debug=True does not
        mask exceptions.
    kwargs : dict
        keyword arguments passed to reader.

    Returns
    -------
    parser_class : obj
        Reader populated with data and metadata attributes. this Reader object can be
        passed to any compatible writer to complete the conversion process.

    Raises
    ------
    DataError
        input file is of unacceptable type, or problem with combination of input parameters.

    Examples
    --------
    convert dicom.tgz to dicoms.nii.gz

    .. code-block:: python

        import scitran.data as scidata
        ds = scidata.parse('dicoms.tgz', load_data=False, filetype='dicom')
        ds.load_data()
        scidata.write(ds, ds.data, outbase, filetype='nifti')

    TODO: convert all in-line code EXAMPLES to using doc-string code.

    """
    log.debug('parse start: %s' % str(datetime.datetime.now()))
    if not os.path.exists(path):
        raise DataError('input path %s not found' % path, log_level=logging.ERROR)
    if os.path.isdir(path):
        raise DataError('directory input not implemented', log_level=logging.ERROR)
    if os.path.isfile(path) and not zipfile.is_zipfile(path):
        if path.endswith('.7.gz') or path.endswith('.7'):   # single P12345.7 or P12345.7.gz
            filetype = 'pfile'
        else:
            raise DataError('non zip-files not implemented', log_level=logging.ERROR)

    if ignore_json and not filetype:   # if ignore_json=True, filetype MUST be set
        raise DataError('filetype must be specified if ignore_json=True')

    timezone = None
    if not ignore_json:  # if ignore_json=False, read json
        log.debug('inspecting %s for json' % path)
        with zipfile.ZipFile(path) as archive:
            try:
                json_data = json.loads(archive.comment, object_hook=util.datetime_decoder)
            except (TypeError, ValueError):
                raise DataError('expected filetype to be indicated in json file')
        filetype = json_data.get('filetype')
        timezone = json_data.get('timezone')
        if filetype is None:
            raise DataError('expected filetype to be indicated in json file')


    parser = get_reader(filetype)  # at this point filetype is set, or an exception was raised
    ds = parser(path, load_data, timezone, **kwargs)  # parser should try to always return a dataset
    if ds.failure_reason:
        if not debug:
            log.warning('parse error: %s' % str(ds.failure_reason))
        else:
            raise ds.failure_reason

    if not ignore_json:
        for key, value in json_data.get('overwrite', {}).iteritems():  # FIXME: handle NESTED information
            setattr(ds, key, value)

    return ds


def write(metadata, data, outbase, filetype, debug=False, **kwargs):
    """
    Write the metadata, imagedata into ouput file named outbase.

    kwargs can be passed to the writer specified by filetype.

    Parameters
    ----------
    metadata : dataset object
        dataset from scidata.parse.
    imagedata : dict
        dictionary of data with string labels as keys.
    outbase : string
        base of name to use, without any file extension.
    filetype : string
        string name of writer to use.
    kwargs : dict
        keyword arguments to be passed to writer.

    Returns
    -------
    output_list : list
        list of created output filepaths.

    Raises
    ------
    DataError
        filetype parameters was not specified.

    Examples
    --------
    convert dicom.tgz to dicoms.nii.gz

    .. code-block:: python

        import scitran.data as scidata
        ds = scidata.parse('dicoms.tgz', load_data=False, filetype='dicom')
        ds.load_data()
        scidata.write(ds, ds.data, outbase, filetype='nifti')

    """
    log.debug('write start: %s' % str(datetime.datetime.now()))
    if not filetype:
        raise DataError('filetype cannot be None')  # XXX FAIL! unexpected to get no filetype

    output_list = []
    if metadata is None:
        log.error('no metadata, cannot write')
    elif data is None:
        log.error('no data, cannot write')
    else:
        try:
            writer = get_writer(filetype)  # raises exception if no handler
            output_list = writer.write(metadata, data, outbase, **kwargs)  # writer checks if data is present
        except Exception as e:
            if not debug:
                log.warning('WRITE ERR: %s could not be written to %s. %s' % (metadata.filepath, filetype, str(e)))
            else:
                raise e
    log.debug('generated: %s' % str(output_list))
    log.debug('write end: %s' % str(datetime.datetime.now()))
    return output_list


class DataError(Exception):

    """
    Base class for Scitran Data exceptions.

    Parameters
    ----------
    message : str
        Message to report along with the exception.
    log_level : logging level [default None]
        What logging level to report the error with, must be a valid logging level class, such as
        `logging.DEBUG` or `logging.ERROR`.

    """

    def __init__(self, message, log_level=None):
        """instantiate dataerror exception class."""
        super(DataError, self).__init__(message)
        if log_level is not None:
            message = '%s\n%s' % (message, traceback.format_exc())
            log.log(log_level, message)


class Reader(object):

    """
    Abstract base class that provides interfaces, and functions for readers.

    Cannot be instantiated.  See :doc:`extending_data` for more information on
    subclassing Reader to create a new data reader.

    Parameters
    ----------
    path : str
        filepath as string
    load_data : boolean [default False]
        Indicate if parse should return with all data loaded.
    timezone : str
        The time zone to use.
    """

    __metaclass__ = abc.ABCMeta

    project_properties = project_properties
    session_properties = session_properties
    acquisition_properties = acquisition_properties

    def _schema_init(self, schema):
        for k, v in schema.iteritems():
            if isinstance(v, dict):
                    self._schema_init(v)
            elif k == 'field' and not v.startswith('nims_'):
                setattr(self, v, None)

    @abc.abstractmethod
    def __init__(self, path, load_data=False, timezone=None):
        self._schema_init(self.project_properties)
        self._schema_init(self.session_properties)
        self._schema_init(self.acquisition_properties)
        self.filepath = os.path.abspath(path)
        self.timezone = timezone
        self.timestamp = None
        self.data = None
        self.metadata_status = 'empty'
        self.failure_reason = None

    @abc.abstractmethod
    def load_data(self):
        pass

    @abc.abstractproperty
    def nims_group_id(self):
        """Group ID

        This is roughly equivalent to a university research lab.
        """
        pass

    @abc.abstractproperty
    def nims_project(self):
        """Project ID"""
        pass

    @abc.abstractproperty
    def nims_session_id(self):
        """Session ID (unique ID)

        For DICOM this is the study instance UID.
        """
        pass

    @abc.abstractproperty
    def nims_session_label(self):
        """Session label (human-readable)"""
        pass

    @abc.abstractproperty
    def nims_session_subject(self):
        """Identifier for the subject

        For DICOM this is the patient ID.
        """
        pass

    @abc.abstractproperty
    def nims_acquisition_id(self):
        """Acquisition ID (unique ID)

        An acquisition is roughly equivalent to a DICOM series.
        For DICOM we use the series instance UID.
        """
        pass

    @abc.abstractproperty
    def nims_acquisition_label(self):
        """Acquisition label (human readable)"""
        pass

    @abc.abstractproperty
    def nims_acquisition_description(self):
        """Description of the acquisition

        Should come from the data.
        """
        pass

    @abc.abstractproperty
    def nims_file_name(self):
        """Filename to use on disk

        Globally unique names are nice, but not required.
        We store all files for an acquisition in the same directory,
        so some uniqueness is needed.
        """
        pass

    # these have sensible global defaults, so we could make them properties,
    # but then the class wouldn't be abstact

    @abc.abstractproperty
    def nims_metadata_status(self):
        """This says whether or not metadata (e.g., session) is available"""
        # NOTE: If you get "(unknown)" for e.g. session even though it has
        # been populated, you need to set self.metadata_status = 'complete'
        return self.metadata_status

    @abc.abstractproperty
    def nims_file_ext(self):
        """The file extension to use"""
        return '.zip'

    @abc.abstractproperty
    def nims_file_domain(self):
        """The file domain"""
        return self.domain

    @abc.abstractproperty
    def nims_file_type(self):
        """The file type"""
        return self.filetype

    @abc.abstractproperty
    def nims_file_state(self):
        """The state of the file"""
        return self.state
        
    @abc.abstractproperty
    def nims_timestamp(self):
        if self.timestamp and self.timezone:
            tz = pytz.timezone(self.timezone).localize(self.timestamp)
            return tz.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)
        return self.timestamp

    @abc.abstractproperty
    def nims_timezone(self):
        return self.timezone

    def __str__(self):  # TODO: tighten this up. or just get rid of it completely
        properties = []
        for prop, value in vars(self).iteritems():          
            if prop in set(['data','imagedata','_']):
                continue
            if value is None:
                value = ''        
            properties.append((prop, value)).sort()
 
        for prop in dir(self):
            if prop in ['data', 'imagedata'] or not prop.startswith('nims'):
                continue
            value = getattr(self, prop) if (value is not None) else ''    
            properties.append((prop, str(value)))
 
        return '\n'.join(['%-30s: %s' % (p, v) for p, v in properties])
     
 

class abstractclassmethod(classmethod):

    """
    Decorator for abstract classmethods.

    .. code-block:: python

        class C(object):
            __metaclass__ = abc.ABCMeta
            @abstractclassmethod
            def my_abstract_classmethod(cls, ...):
                ...

    """

    __isabstractmethod__ = True

    def __init__(self, callable_):
        callable_.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable_)


class Writer(object):

    """
    Abstract base class that provides interfaces and functions for writers.

    Cannot be instantiated.  See :doc:`extending_data` for more information on subclassing
    Reader to create a new data writer.

    """

    __metaclass__ = abc.ABCMeta

    @abstractclassmethod
    def write(cls, metadata, data, outbase, **kwargs):
        """
        Write metadata and imagedata to output file outbase.

        Abstract implementaiton doesn't REALLY need to know about filepath.  Subclasses may want to
        build upon write, such as performing voxel reordering of MR data.

        Parameters
        ----------
        metadata : object
            fully loaded instance of a Reader.
        imagedata : dict
            dictionary of np.darrays. label suffix as keys, with np.darrays as values.
        outbase : str
            output name prefix.
        **kwargs :
            all remaining keyword arguments will be passed to the underlying file writer.

        Returns
        -------
        None : NoneType

        Raises
        ------
        DataError
            metadata or data is None.

        """

        if metadata is None:
            log.error('no metadata, cannot write')
            metadata.failure_reason = DataError('write error, no metadata')
        if data is None:
            log.error('no data, cannot write')
            metadata.failure_reason = DataError('write error, no data')


if __name__ == '__main__':
    import sys
    import argparse

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import data

    log = logging.getLogger('data')

    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='file to convert')
    parser.add_argument('outbase', nargs='?', help='basename for output files (default: input)')
    parser.add_argument('-p', '--parser', help='parser to use', choices=data.data.READERS.keys())
    parser.add_argument('-i', '--ignore_json', help='do not use json metadata in output metadata', action='store_true', default=False)
    parser.add_argument('-w', '--writer', help='write to use', choices=data.data.WRITERS.keys())
    parser.add_argument('-v', '--verbose', help='enable verbose logging', dest='verbose', action='store_true', default=False)
    parser.add_argument(      '--parser_kwarg', action='append', help='keyword arguments to pass directly to the parser')
    parser.add_argument(      '--writer_kwarg', action='append', help='keyword arguments to pass directly to the writer')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not os.path.exists(args.input):
        raise DataError('could not find input file %s' % args.input)

    outbase = args.outbase or os.path.basename(os.path.splitext(args.input.rstrip('/'))[0])

    def cast_if_number(s):
        try:
            return float(s) if '.' in s else int(s)
        except ValueError:
            return s

    p_kwargs = {}
    if args.parser_kwarg:
        for item in args.parser_kwarg:
            kw, val = item.split('=')
            p_kwargs[kw] = cast_if_number(val)
    log.debug(p_kwargs)

    w_kwargs = {}
    if args.writer_kwarg:
        for item in args.writer_kwarg:
            kw, val = item.split('=')
            w_kwargs[kw] = cast_if_number(val)
    log.debug(w_kwargs)

    ds = data.parse(args.input, load_data=True, ignore_json=args.ignore_json, filetype=args.parser, **p_kwargs)

    if not ds:
        raise DataError('%s could not be parsed' % args.input)
    if ds.data is None:
        raise DataError('%s has no data' % args.input)

    data.write(ds, ds.data, outbase, filetype=args.writer, **w_kwargs)

# -*- coding: utf-8 -*-

import os
import glob
from collections import OrderedDict
import operator

try:
   import cPickle as pickle
except:
   import pickle

# Wrappers
from os.path import exists, dirname, basename
from os import makedirs as mkdir


def extension(filename):
    """Get extension from filename.

    Extension is everything from the last dot to the end, ignoring leading
    dots. Extension may be empty.
    """

    return os.path.splitext(filename)[1]


def split(filename, extension=False):
    dirname, basename = os.path.split(filename)

    if extension:
        basename, filetype = os.path.splitext(basename)
        return dirname, basename, filetype
    else:
        return dirname, basename


def index(filename, digits=3, start=0, stop=None, inc=1, seperator='_'):
    value = start
    dirname, basename = split(filename)

    while ((stop is None) or (value < stop)):
        indexed_basename = '{0:0{1}d}{2}{3}'.format(value, digits, seperator, basename)
        indexed_filename = '{}/{}'.format(dirname, indexed_basename)
        yield indexed_filename
        value += inc


def mkfile(filename, override=False):
    """Create directories and open file if not existing or override is True.

    """

    # Create directory if it does not exit
    directory = dirname(filename)
    if directory:
        if not exists(directory):
            mkdir(directory)

    #  Check for existing file if overide is False
    if not override:
        if exists(filename):
            raise OSError('file exists.')

    # Return file object
    return open(filename, 'w')


def flist(file_pattern, *sorted_args, **sorted_kwargs):
    """List of sorted filenames in path, based on pattern.

    """
    files = glob.glob(file_pattern)
    return sorted(files, *sorted_args, **sorted_kwargs)


def ftuple(filenames, index=0, split='_'):
    """Create ordered dictonary from filenames in based on pattern.

    """

    files = list()

    if isinstance(index, (slice, int)):
        ig = operator.itemgetter(index)
    else:
        ig = operator.itemgetter(*index)

    for filename in filenames:
        basename_str = basename(filename)
        keys = ig(basename_str.split(split))
        if isinstance(keys, str):
            key = keys
        else:
            key = split.join(keys)
        files.append((key, filename))

    return files


def fdict(filenames, index=0, split='_'):
    return dict(ftuple(filenames, index, split))


def fodict(filenames, index=0, split='_'):
    return OrderedDict(ftuple(filenames, index, split))


def pdump(obj, file, override=False, protocol=0):
    if isinstance(file, str):
        with mkfile(file, override) as fobj:
            pickle.dump(obj, fobj, protocol)
    else:
        pickle.dump(obj, file, protocol)


def pload(file):
    if isinstance(file, str):
        with open(file) as fobj:
            obj = pickle.load(fobj)
    else:
        obj = pickle.load(file)

    return obj

def read(filename, nr=None, strip=True):
    """Read file into string.

    """

    with open(filename) as fobj:
        if nr:
            lines = []
            for x in xrange(nr):
                try:
                    lines.append(next(fobj))
                except StopIteration:
                    break
            file_str = ''.join(lines)
        else:
            file_str = fobj.read()

    if strip:
        file_str = file_str.strip()

    return file_str


class iopen(object):

    def __init__(self, container, method=None, *open_args, **open_kwargs):

        # Handle dictonaries
        if isinstance(container, (OrderedDict, dict)):
            self._files = container.__class__()
            for key, filename in container.items():
                self._files[key] = open(filename, *open_args, **open_kwargs)
        else:
            # Handle tuple types ((key0, filename0), (key1, filename1), ...)
            try:
                self._files = ((key, open(filename, *open_args, **open_kwargs)) \
                               for key, filename in container)
                self._files = container.__class__(self._files)
            # Handle everything else
            except (ValueError, TypeError):
                self._files = (open(filename, *open_args, **open_kwargs) \
                               for filename in container)
                self._files = container.__class__(self._files)

    def __getitem__(self, key):
        return self._files[key]

    def __getattr__(self, attr):
        return getattr(self._files, attr)

    def __dir__(self):
        return dir(self._files)

    def __repr__(self):
        return repr(self._files)

    def __str__(self):
        return str(self._files)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def close(self):
        if isinstance(self._files, (OrderedDict, dict)):
            for fobj in self._files.values():
                fobj.close()
        else:
            try:
                for key, fobj in self._files:
                    fobj.close()
            except (ValueError, AttributeError):
                for fobj in self._files:
                    fobj.close()

"""
ds9.py connects python and ds9 via the xpa messaging system:

- The ds9 class constructor connects to a single instance of a running ds9.
- The ds9 object supports 'set' and 'get' methods to communicate with ds9.
- Send/retrieve numpy arrays and pyfits (or astropy) hdulists to/from ds9.
- The ds9_targets() function lists ds9 programs running on your system.
- The ds9_openlist() function connects to a list of running ds9 instances.

"""
from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

import contextlib
from distutils.spawn import find_executable
import sys
import subprocess
import shlex
import os
import time
import array
import platform
import textwrap as tw
import warnings

from . import xpa

from astropy.extern import six
from astropy.extern.six import BytesIO


# pyds9 version
__version__ = '1.8.1'

__all__ = ['DS9', 'ds9', 'ds9_openlist', 'ds9_targets', 'ds9_xpans']

# try to be a little bit neat with global parameters
ds9Globals = {}

# platform-specific parameters
ds9Globals["ulist"] = platform.uname()


def get_xpans_ds9():
    """Look for xpans and ds9 executable or app

    Returns
    -------
    xpans : string
        full path to the xpans executable
    ds9 : list of strings
        path to the ds9 executable or, on OSX, ``["open", "-a"
        to call the Aqua version.
    """
    # create the path there to look for xpans executable
    xpans_path = os.environ['PATH']
    pyds9_dir = os.path.dirname(__file__)
    # it could be the development version, then the executable is in the
    # ``xpa`` directory containing the c code
    xpa_dir = os.path.join(os.path.dirname(__file__), 'xpa')
    xpans_path = os.pathsep.join([pyds9_dir, xpa_dir, xpans_path])

    # find the executables
    xpans = find_executable('xpans', path=xpans_path)
    ds9 = [find_executable('ds9')]

    # warning message in case ds9 and/or xpans is not found
    ds9_warning = ("Can't locate DS9 executable. Please add the DS9 directory"
                   " to your PATH and try again.")
    xpans_warning = ("Can't locate xpans executable.")

    if ds9Globals["ulist"][0] == 'Darwin' and not ds9[0]:
        # on mac OSX the Aqua version can be installed. If this is the case,
        # look for a "SAOImage DS9.app" directory in ``/Applications``,
        # ``$HOME`` and ``$HOME/Applications``. If it's found use the mac
        # ``open`` command
        ds9_app = "SAOImage DS9.app"
        user_dir = os.path.expanduser('~')
        for p in ['/Applications', user_dir,
                  os.path.join(user_dir, 'Applications'),
                  os.path.join(user_dir, 'Desktop')]:
            ds9_app_dir = os.path.join(p, ds9_app)
            if os.path.exists(ds9_app_dir):
                ds9 = ['open', '-a', ds9_app_dir, '--args']
                break

        ds9_warning = ("Can't locate the X11 DS9 executable in your PATH or"
                       " the Aqua SAOImage DS9 app in /Applications, $HOME"
                       " or $HOME/Applications. Please configure your PATH or"
                       " make SAOImage DS9 available in a known location.")

    # warn the user if xpans or ds9 is not found
    if not xpans:
        warnings.warn(xpans_warning)
    if not ds9[0]:
        warnings.warn(ds9_warning)

    return xpans, ds9

ds9Globals["progs"] = get_xpans_ds9()

# default list of commands that returns binary data that should not be decoded
ds9Globals['bin_cmd'] = ["array",
                         "fits", "fits image", "fits table", "fits slice",
                         "gif", "jpeg",
                         "mecube",
                         "mosaic", "mosaicimage",
                         "nrrd",
                         "png",
                         "rgbarray", "rgbcube", "rgbimage",
                         "tiff"]

# load pyfits, if available
try:
    from astropy.io import fits as pyfits
    ds9Globals["pyfits"] = 1
except:
    try:
        import pyfits
        if pyfits.__version__ >= '2.2':
            ds9Globals["pyfits"] = 2
        else:
            ds9Globals["pyfits"] = 0
    except:
        ds9Globals["pyfits"] = 0

# load numpy, if available
try:
    import numpy
    ds9Globals["numpy"] = 1
except:
    ds9Globals["numpy"] = 0

# numpy-dependent routines
if ds9Globals["numpy"]:
    def _bp2np(bitpix):
        """
        Convert FITS bitpix to numpy datatype
        """
        if bitpix == 8:
            return numpy.uint8
        elif bitpix == 16:
            return numpy.int16
        elif bitpix == 32:
            return numpy.int32
        elif bitpix == 64:
            return numpy.int64
        elif bitpix == -32:
            return numpy.float32
        elif bitpix == -64:
            return numpy.float64
        elif bitpix == -16:
            return numpy.uint16
        else:
            raise ValueError('unsupported bitpix: %d' % bitpix)

    def _np2bp(dtype):
        """
        Convert numpy datatype to FITS bitpix
        """
        if dtype.kind == 'u':
            # unsigned ints
            if dtype.itemsize == 1:
                return 8
            if dtype.itemsize == 2:
                # this is not in the FITS standard?
                return -16
        elif dtype.kind == 'i':
            # integers
            if dtype.itemsize == 2:
                return 16
            elif dtype.itemsize == 4:
                return 32
            elif dtype.itemsize == 8:
                return 64
        elif dtype.kind == 'f':
            # floating point
            if dtype.itemsize == 4:
                return -32
            elif dtype.itemsize == 8:
                return -64

        raise ValueError('unsupported dtype: %s' % dtype)


def string_to_bytes(string):
    """Converts the input (list of) string(s) into (a list of) bytes

    :param string: string or list of strings to encode

    :rtypes: (list of) byte string(s)
    """
    if six.PY3:
        if isinstance(string, str):
            return string.encode()
        elif isinstance(string, bytes):
            return string
        else:
            try:
                out = []
                for s in string:
                    if isinstance(s, str):
                        out.append(s.decode())
                    else:
                        out.append(s)
                return out
            except TypeError:
                # non iterable
                return string
    else:
        return string


def bytes_to_string(byte):
    """Converts the input (list of) byte string(s) into (a list of) string(s)

    :param byte: (list of) byte string(s) to decode

    :rtypes: string or list of strings
    """
    if six.PY3:
        if isinstance(byte, bytes):
            return byte.decode()
        elif isinstance(byte, str):
            return byte
        else:
            try:
                out = []
                for b in byte:
                    if isinstance(b, bytes):
                        out.append(b.decode())
                    else:
                        out.append(b)
                return out
            except TypeError:
                # non iterable
                return byte
    else:
        return byte


# if xpans is not running, start it up

def ds9_xpans():
    """
    :rtype: 0 => xpans already running, 1 => xpans started by this routine

    ds9_xpans() starts the xpans name server, if its not already running.
    If xpans was not running (and so was started by this routine) while ds9
    was already running, an explanation on how to connect to that instance
    of ds9 is displayed.
    """
    if xpa.xpaaccess(b"xpans", None, 1) is None:
        _fname = ds9Globals["progs"][0]
        if _fname:
            # start up xpans
            subprocess.Popen([_fname, "-e"])
            # if ds9 is already running, issue a warning
            p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE,
                                 universal_newlines=True)
            pslist = p.communicate()[0]   # get the std out
            if 'ds9' in pslist:
                print(tw.dedent("""
                    An instance of ds9 was found to be running before we could
                    start the 'xpans' name server. You will need to perform a
                    bit of manual intervention in order to connect this
                    existing ds9 to Python.

                    For ds9 version 5.7 and beyond, simply register the
                    existing ds9 with the xpans name server by selecting the
                    ds9 File->XPA->Connect menu option. Your ds9 will now be
                    fully accessible to pyds9 (e.g., it appear in the list
                    returned by the ds9_targets() routine).

                    For ds9 versions prior to 5.7, you cannot (easily) register
                    with xpans, but you can view ds9's File->XPA Information
                    menu option and pass the value associated with XPA_METHOD
                    directly to the Python DS9() constructor, e.g.:

                        d = DS9('a000101:12345')

                    The good news is that new instances of ds9 will be
                    registered with xpans, and will be known to ds9_targets()
                    and the DS9() constructor.
                    """))
            return 1
        else:
            raise ValueError("xpans is not running and cannot be located. You"
                             " will not be able to communicate with ds9")
    else:
        return 0


def ds9_targets(target='DS9:*'):
    """
    :param target: ds9 target template (default: all ds9 instances)

    :rtype: list of available targets matching template (name and id)

    To see all actively running ds9 instances for a given target, use the
    ds9_targets() routine::

      >>> ds9_targets()
      ['DS9:foo1 838e29d4:42873', 'DS9:foo2 838e29d4:35739']

    You then can pass one of the ids (or names) to the DS9() constructor.
    """
    targets = xpa.xpaaccess(string_to_bytes(target), None, 1024)
    return bytes_to_string(targets)


def ds9_openlist(target='DS9:*', n=1024):
    """
    :param target: the ds9 target template (default: all ds9 instances)
    :param n: maximum number of targets to connect to (default: 1024)

    :rtype: list of connected ds9 objects

    To open multiple instances of ds9, use the ds9_openlist() routine. Specify
    the target template and an (optional) max target count, and the routine
    returns a list of ds9 objects. For example, assuming 3 instances of ds9
    are running with names foo1, foo2, foo3::

        >>> ds9list = ds9_openlist("foo*")
        >>> for d in ds9list:
        ...     print d.target, d.id
        ...
        DS9:foo1 a000104:56249
        DS9:foo2 a000104:56254
        DS9:foo3 a000104:56256
        >>> ds9list[1].set("file test.fits")

    """
    tlist = xpa.xpaaccess(string_to_bytes(target), None, n)
    if not tlist:
        raise ValueError('no active ds9 found for target: %s' % target)
    else:
        ds9list = []
        for item in bytes_to_string(tlist):
            ds9list.append(DS9(item.split()[0]))
        return ds9list


class DS9(object):
    """
    The DS9 class supports communication with a running ds9 program via the xpa
    messaging system. All of ds9's xpa access points are available via the
    DS9.get() and DS9.set() methods:

    - str = get(paramlist): get data or info from ds9
    - n = set(paramlist, [buf, [blen]]): send data or commands to ds9

    The get method returns the data as a string, while the set method returns
    the number of targets successfully processed (i.e., 1 means success, while
    0 probably means the ds9 is no longer running).

    DS9's xpa access points are documented in the reference manual:

    - http://hea-www.harvard.edu/saord/ds9/ref/xpa.html

    In addition, a number of special methods are implemented to facilitate data
    access to/from python objects:

    - get_arr2np: retrieve a FITS image or an array into a numpy array
    - set_np2arr: send a numpy array to ds9 for display
    - get_pyfits: retrieve a FITS image into a pyfits (or astropy) hdu list
    - set_pyfits: send a pyfits (or astropy) hdu list to ds9 for display

    """

    # access points that do not get trailing cr stripped from them
    _nostrip = ['array', 'fits', 'regions']

    # private attributes that cannot be changed
    _privates = ['target', 'id', 'method']

    # ds9 constructor args:
    # target => XPA template (only one target per object is allowed)
    # verify => use xpaaccess to check target before each method call
    def __init__(self, target='DS9:*', start=True, wait=10, verify=True):
        """
        :param target: the ds9 target name or id (default is all ds9 instances)
        :param start:  start ds9 if its not already running (optional: instead
         of True, you can specify a string or a list of ds9 command line args)
        :param wait: seconds to wait for ds9 to start
        :param verify: perform xpaaccess check before each set or get?

        :rtype: DS9 object connected to a single instance of ds9

        The DS9() contructor takes a ds9 target as its main argument. If start
        is True (default), the ds9 program will be started automatically if its
        not already running.

        The default target matches all ds9 instances. (Note that ds9 instances
        are given unique names using the -title switch on the command line). In
        general, this is the correct way to find ds9 if only one instance of
        the program is running. However, this default target will throw an
        error if more than one ds9 instance is running. In this case, you will
        be shown a list of the actively running programs and will be asked to
        use one of them to specify which ds9 is wanted::

          >>> DS9()
          More than one ds9 is running for target DS9:*:
          DS9:foo1 838e29d4:42873
          DS9:foo2 838e29d4:35739
          Use a specific name or id to construct a ds9 object, e.g.:
          d = ds9('foo1')
          d = ds9('DS9:foo1')
          d = ds9('838e29d4:42873')
          The 'ip:port' id (3rd example) will always be unique.
          ...
          ValueError: too many ds9 instances running for target: DS9:*

        You then can choose one of these to pass to the contructor::

           d = DS9('838e29d4:35739')

        Of course, you can always specify a name for this instance of ds9. A
        unique target name is especially appropriate if you want to start up
        ds9 with a specified command line. This is because pyds9 will start up
        ds9 only if a ds9 with the target name is not already running.

        If the verify flag is turned on, each ds9 method call will check
        whether ds9 is still running, and will throw an exception if this is
        not the case. Otherwise, the method return value can be used to detect
        failure.  Using verification allows ds9 methods to used in try/except
        constructs, at the expense of a slight decrease in performance.
        """
        tlist = xpa.xpaaccess(string_to_bytes(target), None, 1024)
        # no need to convert, as tlist content is not used
        if not tlist and start:
            if '?' in target or '*' in target:
                target = "ds9"
            try:
                args = shlex.split(start)
            except AttributeError:      # Not a parsable string-like object
                try:
                    args = list(start)
                except TypeError:       # Not an iterable object
                    args = []
            self.pid = subprocess.Popen(ds9Globals["progs"][1] +
                                        ['-title', target] + args)

            for i in range(wait):
                tlist = xpa.xpaaccess(string_to_bytes(target), None, 1024)
                if tlist:
                    break
                time.sleep(1)
        tlist = bytes_to_string(tlist)
        if not tlist:
            raise ValueError('no active ds9 running for target: %s' % target)
        elif len(tlist) > 1:
            if 'XPA_METHOD' in os.environ.keys():
                method = os.environ['XPA_METHOD']
            else:
                method = 'inet'
            if method == 'local' or method == 'unix':
                s = 'local file'
            else:
                s = 'ip:port'
            print('More than one ds9 is running for target %s:' % target)
            for l in tlist:
                print("  %s" % l)

            a = tlist[0].split()
            print('Use a specific name or id to construct a DS9 object, e.g.:')
            print("  d = DS9('%s')" % a[0].split()[0].split(':')[1])
            print("  d = DS9('%s')" % a[0])
            print("  d = DS9('%s')" % a[1])
            print("The '%s' id (3rd example) will always be unique.\n" % s)
            raise ValueError('too many ds9 instances for target: %s' % target)
        else:
            a = tlist[0].split()
            self.__dict__['target'] = target
            self.__dict__['id'] = a[1]
            self.verify = verify

    def __setattr__(self, attrname, value):
        """
        An internal routine to guard read-only attributes.
        """
        if attrname in self._privates:
            raise AttributeError('attribute modification is not permitted: %s'
                                 % attrname)
        else:
            propobj = getattr(self.__class__, attrname, None)
            if isinstance(propobj, property):
                if propobj.fset is None:
                    raise AttributeError("can't set attribute")
                propobj.fset(self, value)
            else:
                self.__dict__[attrname] = value

    def _selftest(self):
        """
        An internal test to make sure that ds9 is still running."
        """
        if self.verify and not xpa.xpaaccess(string_to_bytes(self.id), None,
                                             1):
            raise ValueError('ds9 is no longer running (%s)' % self.id)

    def get(self, paramlist=None, decode=None):
        """
        :param paramlist: command parameters (documented in the ds9 ref manual)
        :param decode: decode the output; if ``None`` decodes the output if
            ``paramlist`` is not present in the list ``ds9Globals['bin_cmd']``

        :rtype: returned data or info (as a string or byte string)

        Once a DS9 object has been initialized, use 'get' to retrieve data from
        ds9 by specifying the standard xpa paramlist::

          >>> d.get("file")
          '/home/eric/python/ds9/test.fits'
          >>> d.get("fits height")
          '15'
          >>> d.get("fits width")
          '15'
          >>> d.get("fits bitpix")
          '32'

        Note that all access points return data as python strings.
        """
        self._selftest()
        # convert to byte string in python3
        x = xpa.xpaget(string_to_bytes(self.id), string_to_bytes(paramlist), 1)
        if decode is None:
            decode = paramlist not in ds9Globals['bin_cmd']
        if decode:
            x = bytes_to_string(x)
        if len(x) > 0:
            if paramlist not in self._nostrip:
                x[0] = x[0].strip()
            return x[0]
        else:
            return x

    def set(self, paramlist, buf=None, blen=-1):
        """
        :param paramlist: command parameters (documented in the ds9 ref manual)

        :rtype: 1 for success, 0 for failure

        Once a DS9 object has been initialized, use 'set' to send data and
        commands to ds9::

          >>> d.set("file /home/eric/data/casa.fits")
          1

        A return value of 1 indicates that ds9 was contacted successfully,
        while a return value of 0 indicates a failure.

        To send data (as well as the paramlist) to ds9, specify the data buffer
        in the argument list. The data buffer must either be a string, a
        numpy.ndarray,  or an array.array::

          >>> d.set("array [xdim=1024 ydim=1024 bitpix=-32]", arr)

        Sending both a paramlist and data is the canonical way to send a region
        to ds9::

          >>> d.set('regions', 'fk5; circle(345.29,58.87,212.58")');
          1

        This is equivalent to the Unix xpaset command:

          echo 'fk5; circle(345.29,58.87,212.58")' | xpaset ds9 regions

        Indeed, if you are having problems with ds9.set() or ds9.get(), it
        often is helpful to try the equivalent command using the Unix xpaset
        and xpaget programs.

        """
        self._selftest()
        if ds9Globals["numpy"] and type(buf) == numpy.ndarray:
                s = buf.tostring()
        elif type(buf) == array.array:
            try:  # Python >= 3.2
                s = buf.tobytes()
            except AttributeError:
                s = buf.tostring()
        else:
            s = string_to_bytes(buf)

        return xpa.xpaset(string_to_bytes(self.id), string_to_bytes(paramlist),
                          s, blen, 1)

    def info(self, paramlist):
        """
        :rtype: 1 for success, 0 for failure

        Once a DS9 object has been initialized, use 'info' to send xpa info
        messages to ds9. (NB: ds9 currently does not support info messages.)
        """
        self._selftest()
        return xpa.xpainfo(string_to_bytes(self.id),
                           string_to_bytes(paramlist), 1)

    def access(self):
        """
        :rtype: xpa target name and id

        The 'access' method returns the xpa id of the current instance of ds9,
        by making a direct contact with ds9 itself.
        """
        self._selftest()
        x = xpa.xpaaccess(string_to_bytes(self.id), None, 1)
        return bytes_to_string(x[0])

    if ds9Globals["pyfits"]:
        def get_pyfits(self):
            """
            :rtype: pyfits hdulist

            To read FITS data or a raw array from ds9 into pyfits, use the
            'get_pyfits' method. It takes no args and returns an hdu list::

              >>> hdul = d.get_pyfits()
              >>> hdul.info()
              Filename: StringIO
              No.    Name         Type      Cards   Dimensions   Format
              0    PRIMARY     PrimaryHDU      24  (1024, 1024)  float32
              >>> data = hdul[0].data
              >>> data.shape
              (1024, 1024)

            """
            self._selftest()
            imgData = self.get('fits')
            imgString = BytesIO(string_to_bytes(imgData))
            return pyfits.open(imgString)

        def set_pyfits(self, hdul):
            """
            :param hdul: pyfits hdulist

            :rtype: 1 for success, 0 for failure

            After manipulating or otherwise modifying a pyfits hdulist (or
            making a new one), you can display it in ds9 using the 'set_pyfits'
            method, which takes the hdulist as its sole argument::

              >>> d.set_pyfits(nhdul)
              1

            A return value of 1 indicates that ds9 was contacted successfully,
            while a return value of 0 indicates a failure.
            """
            self._selftest()
            if not ds9Globals["pyfits"]:
                raise ValueError('set_pyfits not defined (pyfits not found)')
            if type(hdul) != pyfits.HDUList:
                if ds9Globals["pyfits"] == 1:
                    raise ValueError('requires pyfits.HDUList as input')
                else:
                    raise ValueError('requires astropy.HDUList as input')
            # for python2 BytesIO and StringIO are the same
            with contextlib.closing(BytesIO()) as newFitsFile:
                hdul.writeto(newFitsFile)
                newfits = newFitsFile.getvalue()
                got = self.set('fits', newfits, len(newfits))
                return got

    else:
        def get_pyfits(self):
            """
            This method is not defined because pyfits in not installed.
            """
            raise ValueError('get_pyfits not defined (pyfits not found)')

        def set_pyfits(self):
            """
            This method is not defined because pyfits in not installed.
            """
            raise ValueError('set_pyfits not defined (pyfits not found)')

    if ds9Globals["numpy"]:
        def get_arr2np(self):
            """
            :rtype: numpy array

            To read a FITS file or an array from ds9 into a numpy array, use
            the 'get_arr2np' method. It takes no arguments and returns the
            np array::

              >>> d.get("file")
              '/home/eric/data/casa.fits[EVENTS]'
              >>> arr = d.get_arr2np()
              >>> arr.shape
              (1024, 1024)
              >>> arr.dtype
              dtype('float32')
              >>> arr.max()
              51.0

            """
            self._selftest()
            w = int(self.get('fits width'))
            h = int(self.get('fits height'))
            d = int(self.get('fits depth'))
            bp = int(self.get('fits bitpix'))
            s = self.get('array')
            if d > 1:
                arr = numpy.fromstring(s, dtype=_bp2np(bp)).reshape((d, h, w))
            else:
                arr = numpy.fromstring(s, dtype=_bp2np(bp)).reshape((h, w))
            # if sys.byteorder != 'big': arr.byteswap(True)
            return arr

        def set_np2arr(self, arr, dtype=None):
            """
            :param arr: numpy array
            :param dtype: data type into which to convert array before sending

            :rtype: 1 for success, 0 for failure

            After manipulating or otherwise modifying a numpy array (or making
            a new one), you can display it in ds9 using the 'set_np2arr'
            method, which takes the array as its first argument::

              >>> d.set_np2arr(arr)
              1

            A return value of 1 indicates that ds9 was contacted successfully,
            while a return value of 0 indicates a failure.

            An optional second argument specifies a datatype into which the
            array will be converted before being sent to ds9. This is
            important in the case where the array has datatype np.uint64,
            which is not recognized by ds9::

              >>> d.set_np2arr(arru64)
              ...
              ValueError: uint64 is unsupported by DS9 (or FITS)
              >>> d.set_np2arr(arru64,dtype=np.float64)
              1

            Also note that np.int8 is sent to ds9 as int16 data, np.uint32 is
            sent as int64 data, and np.float16 is sent as float32 data.
            """
            self._selftest()
            if type(arr) != numpy.ndarray:
                raise ValueError('requires numpy.ndarray as input')
            if dtype and dtype != arr.dtype:
                narr = arr.astype(dtype)
            else:
                if arr.dtype == numpy.int8:
                    narr = arr.astype(numpy.int16)
                elif arr.dtype == numpy.uint32:
                    narr = arr.astype(numpy.int64)
                elif hasattr(numpy, "float16") and arr.dtype == numpy.float16:
                    narr = arr.astype(numpy.float32)
                else:
                    narr = arr
            if not narr.flags['C_CONTIGUOUS']:
                narr = numpy.ascontiguousarray(narr)
            bp = _np2bp(narr.dtype)
            buf = narr.tostring('C')
            blen = len(buf)
            (w, h) = narr.shape

            # note that this needs the "endian=" part because sometimes it's
            # left out completely
            endianness = ''
            if narr.dtype.byteorder == '=':
                endianness = ',endian=' + sys.byteorder
            elif narr.dtype.byteorder == '<':
                endianness = ',endian=little'
            elif narr.dtype.byteorder == '>':
                endianness = ',endian=big'

            paramlist = 'array [xdim={0},ydim={1},bitpix={2}{3}]'
            return self.set(paramlist.format(h, w, bp, endianness), buf,
                            blen+1)

    else:
        def get_arr2np(self):
            """
            This method is not defined because numpy in not installed.
            """
            raise ValueError('get_arr2np not defined (numpy not found)')

        def set_np2arr(self):
            """
            This method is not defined because numpy in not installed.
            """
            raise ValueError('set_np2arr not defined (numpy not found)')


class ds9(DS9):
    """
    This is a backwards-compatibility "shell" class that acts like the DS9
    class but has the old name.  In the future, you should switch to using the
    new name (``DS9``).
    """
    def __init__(self, *args, **kwargs):
        from warnings import warn

        warn('The class name "ds9" is deprecated.  In the future, use "DS9" '
             'instead.')

        super(ds9, self).__init__(*args, **kwargs)

# start xpans, if necessary
# it seems that this must be done at import time, so that we can sense the
# case where xpa is not installed, and ds9 is started before python
if "PYDS9_NOXPANS" not in os.environ.keys():
    ds9_xpans()


def test():
    print("starting quick test for pyds9 version " + __version__)

    # start ds9 if necessary
    tries = 0
    print("looking for our 'pytest' ds9 ...")
    while ds9_targets("pytest") == None:
        if tries == 0:
            print("starting ds9 ...")
            subprocess.Popen(ds9Globals["progs"][1] + ['-title', 'pytest'])
            print("\nwaiting for ds9 to be available ",)
        elif tries == 10:
            raise ValueError("tired of waiting for ds9!")
        print(".",)
        time.sleep(1)
        tries += 1
    print(" ds9 is running!")

    print("\ntesting ds9 support ...")
    l = ds9_targets("pytest")
    print("target list:\n", l)

    d = DS9(l[0].split()[1])
    print("connected to ds9 with id %s" % d.id)

    print("connected to ds9 with id %s" % d.id)

    tfits = os.path.join(os.getcwd(), "test.fits")
    if os.path.exists(tfits):
        cmd = "file " + tfits
        d.set(cmd)
        print("sent file=%s dims=(%s,%s) bitpix=%s" %
              (d.get("file"), d.get("fits width"),
               d.get("fits height"), d.get("fits bitpix")))

        if ds9Globals["numpy"]:
            print("\ntesting numpy support ...")
            a = d.get_arr2np()
            print("reading nparray: shape=%s dtype=%s" % (a.shape, a.dtype))
            print(a)

            print("writing modified nparray ...")
            a[0:3, 0:3] = 8
            a[12:15, 12:15] = 9
            d.set_np2arr(a)

            a = d.get_arr2np()
            print("re-reading nparray: shape=%s dtype=%s" % (a.shape, a.dtype))
            print(a)
        else:
            print("\nskipping numpy test ...")

        if ds9Globals["pyfits"]:
            print("\ntesting pyfits support (%d) ..." % ds9Globals["pyfits"])
            hdul = d.get_pyfits()
            print(hdul.info())
            i = hdul[0].data
            print("reading back pyfits: shape=%s dtype=%s" % (i.shape,
                                                              i.dtype))
            print(i)
        else:
            print("\nskipping pyfits test ...")
    else:
        print("could not find " + tfits + " ... skipping numpy,pyfits tests")

    stime = 7
    print("sleeping for " + str(stime) + " seconds ...")
    time.sleep(stime)
    print("stopping ds9 ...")
    d.set("exit")

    casa = os.path.join(os.getcwd(), "casa.fits")
    if os.path.exists(casa):
        print("starting ds9 (no args) ...")
        d2 = DS9('pytest2')
        d2.set("file " + casa)

        print("starting ds9 (string args) ...")
        d3 = DS9('pytest3', start=["-grid", "-cmap", "sls", casa])

        print("starting ds9 (list args) ...")
        d4 = DS9('pytest4', start=["-grid", "-cmap", "heat", casa])

        print("testing ds9_targets ... ")
        print(ds9_targets())
        ds = ds9_openlist("pytest*")
        for d in ds:
            print(d.id + ": file: " + d.get("file") + " cmap: " +
                  d.get("cmap"))

        time.sleep(stime)
        for d in ds:
            print("stopping ds9: " + d.id + " ...")
            d.set("exit")

    else:
        print("could not find " + casa + " ... skipping casa tests")


if __name__ == '__main__':
    test()

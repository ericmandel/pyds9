"""
python support for XPA client access
"""

import glob
import os
import platform
import sys
import ctypes
import ctypes.util


# look for the shared library in sys.path
def _find_shlib(_libbase):

    dir_ = os.path.dirname(__file__)
    libxpa = glob.glob(os.path.join(dir_, "libxpa*so*"))
    if libxpa:
        return libxpa[0]
    else:
        return None

_libpath = _find_shlib('xpa')
if _libpath:
    libxpa = ctypes.cdll.LoadLibrary(_libpath)
    _ulist = platform.uname()
    if ((_ulist[0] == 'Windows') or ((_ulist[0]).find('CYGWIN') != -1)):
        libc = ctypes.cdll.msvcrt
    else:
        libc = ctypes.cdll.LoadLibrary(None)
else:
    raise ImportError("can't find XPA shared library")

# factory routine returning pointer to byte array
c_byte_p = ctypes.POINTER(ctypes.c_byte)


# free C buffers returned by xpa calls
def _freebufs(p_arr, len_):
    for i in range(len_):
        if p_arr[i]:
            libc.free(p_arr[i])


## XPA XPAOpen(char *mode);
libxpa.XPAOpen.restype = ctypes.c_void_p
libxpa.XPAOpen.argtypes = [ctypes.c_char_p]
def XPAOpen(mode):
    return libxpa.XPAOpen(mode)


## void XPAClose(XPA xpa);
libxpa.XPAClose.argtypes = [ctypes.c_void_p]
def XPAClose(xpa):
    libxpa.XPAClose(xpa)


## int XPAGet(XPA xpa, char *template, char *paramlist, char *mode,
##            char **bufs, int *lens, char **names, char **messages, int n);
libxpa.XPAGet.restype = ctypes.c_int
def XPAGet(xpa, target, paramlist, mode, bufs, lens, names, messages, n):
    libxpa.XPAGet.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                              ctypes.c_char_p, ctypes.c_char_p,
                              c_byte_p*n, ctypes.c_int*n,
                              c_byte_p*n, c_byte_p*n,
                              ctypes.c_int]
    return libxpa.XPAGet(xpa, target, paramlist, mode,
                         bufs, lens, names, messages, n)


## int XPASet(XPA xpa,
##             char *template, char *paramlist, char *mode,
##             char *buf, int len, char **names, char **messages,
##             int n);
XPASet = libxpa.XPASet
libxpa.XPASet.restype = ctypes.c_int
def XPASet(xpa, target, paramlist, mode, buf, blen, names, messages, n):
    libxpa.XPASet.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                              ctypes.c_char_p, ctypes.c_char_p,
                              ctypes.c_char_p, ctypes.c_int,
                              c_byte_p*n, c_byte_p*n,
                              ctypes.c_int]
    return libxpa.XPASet(xpa, target, paramlist, mode,
                         buf, blen, names, messages, n)


## int XPAInfo(XPA xpa,
##              char *template, char *paramlist, char *mode,
##              char **names, char **messages, int n);
XPAInfo = libxpa.XPAInfo
libxpa.XPAInfo.restype = ctypes.c_int
def XPAInfo(xpa, target, paramlist, mode, names, messages, n):
    libxpa.XPAInfo.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                               ctypes.c_char_p, ctypes.c_char_p,
                               c_byte_p*n, c_byte_p*n,
                               ctypes.c_int]
    return libxpa.XPAInfo(xpa, target, paramlist, mode, names, messages, n)


## int XPAAccess(XPA xpa,
##              char *template, char *paramlist, char *mode,
##              char **names, char **messages, int n);
libxpa.XPAAccess.restype = ctypes.c_int
def XPAAccess(xpa, target, paramlist, mode, names, messages, n):
    libxpa.XPAAccess.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                 ctypes.c_char_p, ctypes.c_char_p,
                                 c_byte_p*n, c_byte_p*n,
                                 ctypes.c_int]
    return libxpa.XPAAccess(xpa, target, paramlist, mode, names, messages, n)

# default value for n (max number of access points)
xpa_n = 1024


def to_string(buf, size=-1, strip=True):
    """Wrap conversion of ctypes string to Python"""

    s = ctypes.string_at(buf, size).decode('utf-8')
    if strip:
        s = s.strip()

    return s


def xpaget(target, plist=None, n=xpa_n):
    buf_t = c_byte_p*n
    bufs = buf_t()
    names = buf_t()
    errs = buf_t()
    int_t = ctypes.c_int*n
    lens = int_t()
    errmsg = ''
    got = XPAGet(None, target, plist, None, bufs, lens, names, errs, n)
    if got:
        buf = []
        for i in range(got):
            if lens[i]:
                cur = ctypes.string_at(bufs[i], lens[i])
                buf.append(cur)
        for i in range(got):
            if errs[i]:
                errmsg += to_string(errs[i]) + '\n'
    else:
        buf = None
    _freebufs(bufs, n)
    _freebufs(names, n)
    _freebufs(errs, n)
    if errmsg:
        raise ValueError(errmsg)
    return buf


def xpaset(target, plist=None, buf=None, blen=-1, n=xpa_n):
    if blen < 0:
        if buf is not None:
            blen = len(buf)
        else:
            blen = 0
    buf_t = c_byte_p*n
    names = buf_t()
    errs = buf_t()
    errmsg = ''
    got = XPASet(None, target, plist, None, buf, blen, names, errs, n)
    for i in range(got):
        if errs[i]:
            errmsg += to_string(errs[i]) + '\n'
    _freebufs(names, n)
    _freebufs(errs, n)
    if errmsg:
        raise ValueError(errmsg)
    return got


def xpainfo(target, plist=None, n=xpa_n):
    buf_t = c_byte_p*n
    names = buf_t()
    errs = buf_t()
    errmsg = ''
    got = XPAInfo(None, target, plist, None, names, errs, n)
    for i in range(got):
        if errs[i]:
            errmsg += to_string(errs[i]) + '\n'
    _freebufs(names, n)
    _freebufs(errs, n)
    if errmsg:
        raise ValueError(errmsg)
    return got


def xpaaccess(target, plist=None, n=xpa_n):
    buf_t = c_byte_p*n
    names = buf_t()
    errs = buf_t()
    errmsg = ''
    got = XPAAccess(None, target, plist, None, names, errs, n)
    if got:
        buf = []
        for i in range(got):
            if names[i]:
                buf.append(to_string(names[i]))
        for i in range(got):
            if errs[i]:
                errmsg += to_string(errs[i]) + '\n'
    else:
        buf = None
    _freebufs(names, n)
    _freebufs(errs, n)
    if errmsg:
        raise ValueError(errmsg)
    return buf

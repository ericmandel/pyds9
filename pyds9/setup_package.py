# Licensed under a 3-clause BSD style license - see PYFITS.rst
from __future__ import (print_function, absolute_import, division)

from contextlib import contextmanager
import glob
import os
import platform
import subprocess as sp
import struct

from distutils.core import Extension

from astropy_helpers import setup_helpers
from astropy_helpers.distutils_helpers import get_distutils_build_option


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def get_extensions():
    ulist = platform.uname()
    xpa_dir = os.path.join('cextern', 'xpa')
    debug = get_distutils_build_option('debug')

    # libxpa configurations
    cfg = setup_helpers.DistutilsExtensionArgs()
    cfg['extra_compile_args'].append('-DHAVE_CONFIG_H')

    if 'CFLAGS' not in os.environ and struct.calcsize("P") == 4:
        if ulist[0] == 'Darwin' or ulist[4] == 'x86_64':
            if debug:
                print('adding -m32 to compiler flags ...')
            cflags = '-m32'
            cfg['extra_compile_args'].append(cflags)

    # cfg['extra_compile_args'].extend([# '--enable-shared',
    #                                   '--without-tcl',
    #                                   cflags])

    # import pdb; pdb.set_trace()

    if not setup_helpers.use_system_library('libxpa'):
        if not debug:
            # All of these switches are to silence warnings from compiling
            cfg['extra_compile_args'].extend([
                '-Wno-declaration-after-statement',
                '-Wno-unused-variable', '-Wno-parentheses',
                '-Wno-uninitialized', '-Wno-format',
                '-Wno-strict-prototypes', '-Wno-unused', '-Wno-comments',
                '-Wno-switch', '-Wno-strict-aliasing', '-Wno-return-type',
                '-Wno-address', '-Wno-unused-result'
            ])

        cfg['include_dirs'].append(xpa_dir)
        sources = ['xpa.c', 'xpaio.c', 'command.c', 'acl.c', 'remote.c',
                   'clipboard.c', 'port.c', 'tcp.c', 'client.c', 'word.c',
                   'xalloc.c', 'find.c', 'xlaunch.c', 'timedconn.c',
                   'tclloop.c', 'tcl.c']
        cfg['sources'].extend([os.path.join(xpa_dir, s) for s in sources])
    else:
        cfg.update(setup_helpers.pkg_config(['libxpa'], ['libxpa']))

    libxpa = Extension('pyds9.libxpa', **cfg)

    return [libxpa, ]


def get_package_data():
    # Installs the testing data files
    return {
        'pyds9.tests': [os.path.join('data', '*.fits')]}


def get_external_libraries():
    return ['libxpa']


def pre_build_ext_hook(cmd):
    "Run configure to get all the needed files"
    libxpa = cmd.ext_map['pyds9.libxpa']
    xpa_dir = [i for i in libxpa.include_dirs if 'xpa' in i][0]

    with cd(xpa_dir):
        sp.check_call([os.path.join('.', 'configure'), '--without-tcl'])


def post_build_ext_hook(cmd):
    """Build the xpans executable and then run ``make distclean`` in the xpa
    directory"""
    # get all the important information
    compiler = cmd.compiler
    libxpa = cmd.ext_map['pyds9.libxpa']
    flags = libxpa.extra_compile_args
    include_dirs = libxpa.include_dirs
    build_lib = cmd.build_lib
    build_temp = cmd.build_temp
    # shorter name for getmtime
    gettime = os.path.getmtime
    force_rebuild = get_distutils_build_option('force')

    # build the file names
    xpans_c = os.path.join('cextern', 'xpa', 'xpans.c')
    xpans_o = os.path.join(build_temp, xpans_c.replace('.c', '.o'))
    xpans = os.path.join(build_lib, cmd.distribution.get_name(), 'xpans')
    xpa_o = glob.glob(xpans_o.replace('xpans', '*'))

    # decide whether to recompile the object file
    if os.path.exists(xpans_o):
        make_obj = gettime(xpans_o) < gettime(xpans_c)
        headers = sum((glob.glob(os.path.join(i, '*.h'))
                       for i in include_dirs), [])
        make_obj |= any(gettime(xpans_o) < gettime(i) for i in headers)
    else:
        make_obj = True
    # use distutils compiler to build the xpans.o
    if make_obj or force_rebuild:
        compiler.compile([xpans_c, ], output_dir=build_temp,
                         include_dirs=include_dirs,
                         debug=get_distutils_build_option('debug'),
                         extra_postargs=flags, depends=[xpans_c, ])
    # decide whether to recompile the executable
    if os.path.exists(xpans):
        make_exe = gettime(xpans) < gettime(xpans_o)
        make_obj |= any(gettime(xpans) < gettime(i) for i in xpa_o)
    else:
        make_exe = True
    # compile the executable by hand
    if make_exe or force_rebuild:
        compile_cmd = compiler.compiler
        compile_cmd += ['-o', xpans, xpans_o] + xpa_o
        compile_cmd += flags
        print(" ".join(compile_cmd))
        sp.check_call(compile_cmd)

    # run make clean
    xpa_dir = [i for i in libxpa.include_dirs if 'xpa' in i][0]

    with cd(xpa_dir):
        sp.check_call(['make', 'distclean'])


def requires_2to3():
    return False

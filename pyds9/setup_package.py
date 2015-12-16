# Licensed under a 3-clause BSD style license - see PYFITS.rst
from __future__ import absolute_import

from glob import glob
import os
import platform
import struct

from distutils.core import Extension

from astropy_helpers import setup_helpers
from astropy_helpers.distutils_helpers import get_distutils_build_option


def get_extensions():
    ulist = platform.uname()

    cfg = setup_helpers.DistutilsExtensionArgs()

    xpa_dir = os.path.join('cextern', 'xpa')

    cfg['extra_compile_args'].append('-DHAVE_CONFIG_H')

    # cflags = ''
    if 'CFLAGS' not in os.environ and struct.calcsize("P") == 4:
        if ulist[0] == 'Darwin' or ulist[4] == 'x86_64':
            os.system('echo "adding -m32 to compiler flags ..."')
            cflags = '-m32'
            cfg['extra_compile_args'].append(cflags)

    # cfg['extra_compile_args'].extend([# '--enable-shared',
    #                                   '--without-tcl',
    #                                   cflags])

    # import pdb; pdb.set_trace()

    if not setup_helpers.use_system_library('libxpa'):
        if not get_distutils_build_option('debug'):
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

        # i for i in glob(os.path.join(xpa_dir, '*.c'))
        #                    if 'test' not in i])
    else:
        cfg.update(setup_helpers.pkg_config(['libxpa'], ['libxpa']))

    return [Extension('pyds9.libxpa', **cfg)]


def get_package_data():
    # Installs the testing data files
    return {
        'pyds9.tests': [os.path.join('data', '*.fits')]}


def get_external_libraries():
    return ['libxpa']


def requires_2to3():
    return False

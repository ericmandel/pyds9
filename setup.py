#!/usr/bin/env python
from distutils.core import setup
from distutils.command import build_py, install_data, clean
from os import system, path
import os
import platform
import struct

# which shared library?
ulist=platform.uname()
if ulist[0] == 'Darwin':
    xpalib = 'libxpa.dylib'
    xpans = 'xpans'
elif ulist[0] == 'Windows':
    xpalib = 'libxpa.dll'
    xpans = 'xpans.exe'
else:
    xpalib = 'libxpa.so'
    xpans = 'xpans'

# make command for xpa
xpadir='xpa-2.1.15'
def make(which):
    curdir=os.getcwd()
    srcDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),xpadir)
    os.chdir(srcDir)
    if which == 'all':
        os.system('echo "building XPA shared library ..."')
        cflags=''
        if not 'CFLAGS' in os.environ and struct.calcsize("P") == 4:
            if ulist[0] == 'Darwin' or ulist[4] == 'x86_64':
                os.system('echo "adding -m32 to compiler flags ..."')
                cflags=' CFLAGS="-m32"'
        os.system('./configure --enable-shared --without-tcl'+cflags)
        os.system('make clean; make; rm -f *.o')
    elif which == 'clean':
        os.system('echo "cleaning XPA ..."')
        os.system('make clean')
    elif which == 'mingw-dll':
        os.system('echo "building XPA shared library ..."')
        os.system('sh configure --without-tcl')
        os.system('make clean')
        os.system('make')
        os.system('make mingw-dll')
        os.system('rm -f *.o')
    os.chdir(curdir)

# rework build_py to make the xpa shared library as well
class my_build_py(build_py.build_py):
    def run(self):
        if platform.uname()[0] == 'Windows':
            make('mingw-dll')
        else:
            make('all')
        build_py.build_py.run(self)

# thanks to setup.py in ctypes
class my_install_data(install_data.install_data):
    """A custom install_data command, which will install it's files
    into the standard directories (normally lib/site-packages).
    """
    def finalize_options(self):
        if self.install_dir is None:
            installobj = self.distribution.get_command_obj('install')
            self.install_dir = installobj.install_lib
        print 'Installing data files to %s' % self.install_dir
        install_data.install_data.finalize_options(self)

# clean up xpa as well
class my_clean(clean.clean):
    def run(self):
        make('clean')
        clean.clean.run(self)

# setup command
setup(name='pyds9',
    version='1.7',
    description='Python/DS9 connection via XPA (with numpy and pyfits support)',
    author='Bill Joye and Eric Mandel',
    author_email='saord@cfa.harvard.edu',
    url='http://hea-www.harvard.edu/saord/ds9/',
    py_modules=['ds9', 'xpa'],
    data_files=[('', [xpadir+'/'+xpalib, xpadir+'/'+xpans])],
    cmdclass = {'build_py': my_build_py, 	 \
                'install_data': my_install_data, \
                'clean': my_clean },
   )

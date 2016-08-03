# Python connection to ds9 via XPA

The [XPA messaging system](https://github.com/ericmandel/xpa) provides 
seamless communication between many kinds of Unix programs, including Tcl/Tk
programs such as ds9. The ``pyds9`` module uses a Python interface to XPA to 
communicate with ds9. It supports communication with all of ds9's XPA access
points.

pyds9 is available from GitHub at:

https://github.com/ericmandel/pyds9


The easiest way to install ``pyds9`` is:

    # install from the repository
    > pip install [--user] git+https://github.com/ericmandel/pyds9.git#egg=pyds9

Alternatively, you can clone the git repository or download and unpack the [zip
file](https://github.com/ericmandel/pyds9/archive/master.zip). Then ``cd`` into
the pyds9 directory and issue:

    > python setup.py [--user] install


If the compilation of the C files in ``xpa`` directory fails saying that doesn't
find the header file ``X11/Intrinsic.h`` make sure to install the relevant
packages:

* openSUSE: sudo zypper install libXt-devel
* Ubuntu: sudo apt-get install libxt-dev

To run:

    # start up python
    > python
        ... (startup messages) ...
    >>> import pyds9
    >>> print(pyds9.ds9_targets())
    >>> d = pyds9.DS9()  # will open a new ds9 window or connect to an existing one
    >>> d.set("file /path/to/fits")  # send the file to the open ds9 session

If you create a ``test.fits`` file and a ``casa.fits`` file in the working
directory you can test basic ds9 functionalities running the function:

    > pyds9.test()


The setup.py install will build and install both the XPA shared library and 
the xpans name server. By default, the code generated for the shared object
will match the address size of the host machine, i.e. 32-bit or 64-bit
as the case may be. But on 64-bit Intel machines, the XPA build also will check
whether python itself is 64-bit. If not, will add the "-m32" switch to the
compile options to build a 32-bit shared object. This check can be overridden
by defining the CFLAGS environment variable (which can be anything sensible,
including an empty string).

For Linux, the X Window System libraries and header files must be available.
On some versions of Linux (e.g., debian), the development libraries must be
installed explicitly. If you have problems, please let us know.

To report a bug, ask for a new feature, or request support, please contact us at
https://github.com/ericmandel/pyds9/issues


Eric Mandel and Francesco Montesano

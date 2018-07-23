.. pyds9 documentation master file, created by
   sphinx-quickstart on Mon Nov  9 10:20:44 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyds9's documentation!
=================================

.. currentmodule:: pyds9

**A Python Connection to DS9 via XPA**

The XPA messaging system (http://hea-www.harvard.edu/saord/xpa) provides
seamless communication between many kinds of Unix programs, including Tcl/Tk
programs such as ds9. The pyds9 module uses a Python interface to XPA to
communicate with ds9. It supports communication with all of ds9's XPA access
points. See http://ds9.si.edu/doc/ref/xpa.html for more info on DS9's access
points.

pyds9 is available from GitHub:

	 https://github.com/ericmandel/pyds9

To install in the default directory::

	# install in default system directory
	> pip install git+https://github.com/ericmandel/pyds9.git

or to install in a user-specified directory::

	# install in specified directory
	> python setup.py install --prefix=<install-dir>
	> setenv PYTHONPATH <install-dir>lib/python2.x/site-packages

To run::

	# start up ipython
	> ipython
        ... (startup messages) ...
	In [1]: import pyds9
	In [2]: print(pyds9.ds9_targets())
	In [3]: d = pyds9.DS9()

The setup.py install will build and install both the XPA shared library and
the xpans name server. By default, the code generated for the shared object
will match the address size of the host machine, i.e. 32-bit or 64-bit
as the case may be. But on 64-bit Intel machines, the XPA build also will check
whether python itself is 64-bit. If not, it will add the "-m32" switch to the
compile options to build a 32-bit shared object. This check can be overridden
by defining the CFLAGS environment variable (which can be anything sensible,
including an empty string).

Contact saord@cfa.harvard.edu for help.

The DS9 Class
-------------

.. autoclass:: DS9
   :members: __init__, get, set, info, access, get_pyfits, set_pyfits, get_arr2np, set_np2arr
   :noindex:

Auxiliary Routines
------------------

.. autofunction:: ds9_targets
   :noindex:

.. autofunction:: ds9_openlist
   :noindex:

.. autofunction:: ds9_xpans
   :noindex:

.. toctree::
   :maxdepth: 2

Reference/API
-------------
.. from astropy template

.. automodapi:: pyds9

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


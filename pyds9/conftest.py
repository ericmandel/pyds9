# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

# As of AstroPy 3.0 the plugins are made available when
# AstroPy is installed.
#
from astropy.version import version as astropy_version
if astropy_version < '3.0':
    from astropy.tests.pytest_plugins import *

import py.path
import pytest

# Uncomment the following line to treat all DeprecationWarnings as
# exceptions
# pytest_plugins.enable_deprecations_as_exceptions()

# Uncomment and customize the following lines to add/remove entries from
# the list of packages for which version numbers are displayed when running
# the tests. Making it pass for KeyError is essential in some cases when
# the package uses other astropy affiliated packages.
# try:
#     PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
#     PYTEST_HEADER_MODULES['scikit-image'] = 'skimage'
#     del PYTEST_HEADER_MODULES['h5py']
# except (NameError, KeyError):  # NameError is needed to support Astropy < 1.0
#     pass

# Uncomment the following lines to display the version number of the
# package rather than the version number of Astropy in the top line when
# running the tests.
import os

# This is to figure out the affiliated package version, rather than
# using Astropy's
try:
    from .version import version
except ImportError:
    version = 'dev'

try:
    packagename = os.path.basename(os.path.dirname(__file__))
    TESTED_VERSIONS[packagename] = version
except NameError:   # Needed to support Astropy <= 1.0.0
    pass


@pytest.fixture
def test_data_dir():
    '''Returns the name of the test data directory as a py.path.local object'''
    this_file = py.path.local(__file__)
    return this_file.dirpath('tests', 'data')


@pytest.fixture
def test_fits(test_data_dir):
    '''Returns the name of the test fits file as a py.path.local object'''
    return test_data_dir.join('test.fits')


def pytest_report_header(config):
    """Report the DISPLAY setting.

    This is mainly to help identify issues with the display
    on CI services.
    """
    import os
    try:
        display = os.environ['DISPLAY']
    except KeyError:
        display = "< UNSET >"

    return "pyds9: DISPLAY={}".format(display)

# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
Connects python and ds9 via the xpa messaging system.

This package aims at being an Astropy affiliated package.
"""

from __future__ import (print_function, absolute_import, division,
                        unicode_literals)

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
if not _ASTROPY_SETUP_:
    from .pyds9 import *

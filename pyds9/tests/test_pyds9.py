import random
import subprocess as sp
import time

import numpy as np
import pytest

from pyds9 import pyds9

parametrize = pytest.mark.parametrize

type_mapping = parametrize('bitpix, dtype ',
                           [(8, np.dtype(np.uint8)),
                            (16, np.dtype(np.int16)),
                            (32, np.dtype(np.int32)),
                            (64, np.dtype(np.int64)),
                            (-32, np.dtype(np.float32)),
                            (-64, np.dtype(np.float64)),
                            (-16, np.dtype(np.uint16)),
                            pytest.mark.xfail(raises=ValueError,
                                              reason='Wrong input')
                                             ((42, np.dtype(str)))
                            ])


@pytest.fixture
def ds9_title():
    '''Start a ds9 instance in a subprocess and returns its title'''
    name = 'test.{}'.format(random.randint(0, 10000))
    cmd = ['ds9', '-title', name]
    p = sp.Popen(cmd)
    # wait for ds9 to come alive
    while not pyds9.ds9_targets():
        time.sleep(0.1)

    yield name

    returncode = p.poll()
    if returncode is None:
        p.kill()
        p.communicate()
    elif returncode != 0:
        raise sp.CalledProcessError(returncode, ' '.join(cmd))


@type_mapping
def test_bp2np(dtype, bitpix):
    """Test from bitpix to dtype"""
    output = pyds9._bp2np(bitpix)

    assert output == dtype


@type_mapping
def test_np2bp(dtype, bitpix):
    """Test from dtype to bitpix"""
    output = pyds9._np2bp(dtype)

    assert output == bitpix


def test_ds9_targets_empty():
    '''If no ds9 instance is running, ds9_targets returns None'''
    targets = pyds9.ds9_targets()
    assert targets is None


def test_ds9_targets(ds9_title):
    '''ds9_targets returns open ds9 names'''
    targets = pyds9.ds9_targets()
    assert len(targets) == 1
    assert ds9_title in targets[0]


@pytest.mark.xfail(raises=ValueError, reason='No target ds9 instance')
def test_ds9_openlist_empty():
    '''If no ds9 instance is running, ds9_openlist raises an exception'''
    pyds9.ds9_openlist()


def test_ds9_openlist(ds9_title):
    '''ds9_openlist returns running ds9 instances'''
    ds9s = pyds9.ds9_openlist()
    assert len(ds9s) == 1
    assert ds9_title in ds9s[0].target


# def test_ds9(ds9_title):
    # ''''''
    # ds9 = pyds9.ds9_openlist(target=ds9_title)[0]

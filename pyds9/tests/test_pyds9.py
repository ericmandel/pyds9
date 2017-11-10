import random
import subprocess as sp
import time

from astropy.io import fits
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


@parametrize('meth, n_warning',
             [('get_fits', 0), ('get_pyfits', 1)])
def test_ds9_get_fits(monkeypatch, ds9_title, test_fits, meth,
                      n_warning):
    '''get a fits file as an astropy fits object'''
    monkeypatch.setitem(pyds9.ds9Globals, 'pyfits', False)
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]

    ds9.set('file {}'.format(test_fits))

    with pytest.warns(None) as warn_records:
        hdul_from_ds9 = getattr(ds9, meth)()

    assert isinstance(hdul_from_ds9, fits.HDUList)
    assert len(warn_records) == n_warning

    diff = fits.FITSDiff(test_fits.strpath, hdul_from_ds9,
                         ignore_comments=['*', ])

    assert diff.identical


@pytest.mark.xfail(raises=ValueError, reason='Not an astropy hdu')
def test_ds9_set_fits_fail(ds9_title):
    '''set_fits wants an astropy HDUList'''
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    ds9.set_fits('random_type')


@parametrize('meth, n_warning',
             [('set_fits', 0), ('set_pyfits', 1)])
def test_ds9_set_fits(monkeypatch, tmpdir, ds9_title, test_fits,
                      meth, n_warning):
    '''Set the astropy fits'''
    monkeypatch.setitem(pyds9.ds9Globals, 'pyfits', False)
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]

    with fits.open(test_fits.strpath) as hdul,\
            pytest.warns(None) as warn_records:
        success = getattr(ds9, meth)(hdul)

    assert success == 1
    assert len(warn_records) == n_warning

    out_fits = tmpdir.join('out.fits')
    with out_fits.open('w') as f:
        sp.call(['xpaget', ds9.target, 'fits'], stdout=f)

    diff = fits.FITSDiff(test_fits.strpath, out_fits.strpath,
                         ignore_comments=['*', ])

    assert diff.identical


def test_ds9_get_pyfits(ds9_title, test_fits):
    'use pytest to get fits'
    pyfits = pytest.importorskip('pyfits', minversion='0.2')

    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    ds9.set('file {}'.format(test_fits))

    with pytest.warns(None) as warn_records:
        hdul_from_ds9 = ds9.get_pyfits()

    assert isinstance(hdul_from_ds9, pyfits.HDUList)
    assert len(warn_records) == 0

    diff = pyfits.FITSDiff(test_fits.strpath, hdul_from_ds9,
                           ignore_comments=['*', ])

    assert diff.identical


@pytest.mark.xfail(raises=ValueError, reason='Not an astropy hdu')
def test_ds9_set_pyfits_fail(ds9_title):
    '''set_fits wants an astropy HDUList'''
    pytest.importorskip('pyfits', minversion='0.2')
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    ds9.set_pyfits('random_type')


def test_ds9_set_pyfits(tmpdir, ds9_title, test_fits):
    '''Set the astropy fits'''
    pyfits = pytest.importorskip('pyfits', minversion='0.2')
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]

    with pyfits.open(test_fits.strpath) as hdul,\
            pytest.warns(None) as warn_records:
        success = ds9.set_pyfits(hdul)

    assert success == 1
    assert len(warn_records) == 0

    out_fits = tmpdir.join('out.fits')
    with out_fits.open('w') as f:
        sp.call(['xpaget', ds9.target, 'fits'], stdout=f)

    diff = pyfits.FITSDiff(test_fits.strpath, out_fits.strpath,
                           ignore_comments=['*', ])

    assert diff.identical


def test_get_arr2np(ds9_title, test_fits):
    '''Get the data on ds9 as a numpy array'''
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    ds9.set('file {}'.format(test_fits))

    arr = ds9.get_arr2np()

    fits_data = fits.getdata(test_fits.strpath)

    np.testing.assert_array_equal(arr, fits_data)


@pytest.mark.xfail(raises=ValueError, reason='Not a numpy array')
def test_ds9_set_np2arr_fail(tmpdir, ds9_title, test_fits):
    '''Set the astropy fits'''
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    ds9.set_np2arr('random_type')


def test_ds9_set_np2arr(tmpdir, ds9_title, test_fits):
    '''Set the astropy fits'''
    ds9 = pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]
    fits_data = fits.getdata(test_fits.strpath)

    success = ds9.set_np2arr(fits_data)

    assert success == 1

    out_fits = tmpdir.join('out.fits')
    with out_fits.open('w') as f:
        sp.call(['xpaget', ds9.target, 'fits'], stdout=f)

    np.testing.assert_array_equal(fits_data, fits.getdata(out_fits.strpath))

from collections import Counter
import contextlib
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
                            (-16, np.dtype(np.uint16))
                            ])


@pytest.fixture
def run_ds9s():
    '''Returns a context manager that accepts a list of names and run a ds9
    instance the for each name. On return from the yield, stop the instances'''

    @contextlib.contextmanager
    def _run_ds9s(*names):
        processes = []
        for name in names:
            cmd = ['ds9', '-title', name]
            processes.append(sp.Popen(cmd))
        # wait for all the ds9 to come alive
        while True:
            targets = pyds9.ds9_targets()
            if targets and len(targets) == len(processes):
                break
            time.sleep(0.1)

        try:
            yield
        finally:
            errors = []
            for p in processes:
                returncode = p.poll()
                if returncode is None:
                    p.kill()
                    p.communicate()
                elif returncode != 0:
                    errors.append([cmd, returncode])
            if errors:
                msg = 'Command {} failed with error {}.'
                msgs = [msg.format(' '.join(e[0]), e[1]) for e in errors]
                raise RuntimeError('\n'.join(msgs))

    return _run_ds9s


@pytest.fixture
def ds9_title(run_ds9s):
    '''Start a ds9 instance in a subprocess and returns its title'''
    name = 'test.{}'.format(random.randint(0, 10000))

    with run_ds9s(name):
        yield name


@pytest.fixture
def ds9_obj(ds9_title):
    '''returns the DS9 instance for ``ds9_title``'''
    return pyds9.ds9_openlist(target='*' + ds9_title + '*')[0]


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


def test_bp2np_fail():
    """Test from bitpix to dtype: invalid bitpix"""

    with pytest.raises(ValueError,
                       match='unsupported bitpix: 43'):
        pyds9._bp2np(43)


def test_np2bp_fail():
    """Test from dtype to bitpix: invalid dtype"""

    with pytest.raises(ValueError,
                       match='unsupported dtype'):
        pyds9._np2bp(np.dtype(str))


def test_ds9_targets_empty():
    '''If no ds9 instance is running, ds9_targets returns None'''
    targets = pyds9.ds9_targets()
    assert targets is None


def test_ds9_targets(run_ds9s):
    '''ds9_targets returns open ds9 names'''
    names = ['test1', 'test1', 'test2']
    with run_ds9s(*names):
        targets = pyds9.ds9_targets()

    assert len(targets) == len(names)
    names = Counter(names)
    for name, count in names.items():
        assert sum(name in t for t in targets) == count


def test_ds9_openlist_empty():
    '''If no ds9 instance is running, ds9_openlist raises an exception'''
    with pytest.raises(ValueError,
                       match='no active ds9 found for target: DS9:*'):
        pyds9.ds9_openlist()


def test_ds9_openlist(run_ds9s):
    '''ds9_openlist returns running ds9 instances'''
    names = ['test4', 'test5', 'test6']
    with run_ds9s(*names):
        ds9s = pyds9.ds9_openlist()

    assert len(ds9s) == len(names)

    # It is not obvious to DJB what this test was meant to do
    # since the .target and .id field values are very different.
    #
    # target_is_id = [ds9.target == ds9.id for ds9 in ds9s]
    # assert sum(target_is_id) == 2

    # I have replaced them by a simple set check that the
    # expected names are returned.
    #
    expected = {"DS9:" + n for n in names}
    got = {d.target for d in ds9s}
    assert expected == got

def test_ds9_get_fits(ds9_obj, test_fits):
    '''get a fits file as an astropy fits object'''

    ds9_obj.set('file {}'.format(test_fits))

    with pytest.warns(None) as warn_records:
        hdul_from_ds9 = ds9_obj.get_fits()

    assert isinstance(hdul_from_ds9, fits.HDUList)
    assert len(warn_records) == 0

    diff = fits.FITSDiff(test_fits.strpath, hdul_from_ds9,
                         ignore_comments=['*', ])

    assert diff.identical


def test_ds9_set_fits_fail(ds9_obj):
    '''set_fits wants an astropy HDUList'''

    with pytest.raises(ValueError,
                       match='The input must be an astropy HDUList'):
        ds9_obj.set_fits('random_type')


def test_ds9_set_fits(tmpdir, ds9_obj, test_fits):
    '''Set the astropy fits'''

    with fits.open(test_fits.strpath) as hdul,\
            pytest.warns(None) as warn_records:
        success = ds9_obj.set_fits(hdul)

    assert success == 1
    assert len(warn_records) == 0

    out_fits = tmpdir.join('out.fits')
    with out_fits.open('w') as f:
        sp.call(['xpaget', ds9_obj.target, 'fits'], stdout=f)

    diff = fits.FITSDiff(test_fits.strpath, out_fits.strpath,
                         ignore_comments=['*', ])

    assert diff.identical


fits_names = parametrize('fits_name', ['test.fits', 'test_3D.fits'])


@fits_names
def test_get_arr2np(ds9_obj, test_data_dir, fits_name):
    '''Get the data on ds9 as a numpy array'''
    fits_file = test_data_dir.join(fits_name)
    ds9_obj.set('file {}'.format(fits_file))

    arr = ds9_obj.get_arr2np()

    fits_data = fits.getdata(fits_file.strpath)

    np.testing.assert_array_equal(arr, fits_data)


@parametrize('input_', ['random_type', np.arange(5)])
def test_ds9_set_np2arr_fail(tmpdir, ds9_obj, input_):
    '''Set the passing wrong arrays'''

    with pytest.raises(ValueError):
        ds9_obj.set_np2arr(input_)


@fits_names
def test_ds9_set_np2arr(tmpdir, ds9_obj, test_data_dir, fits_name):
    '''Set the astropy fits'''
    fits_file = test_data_dir.join(fits_name)

    fits_data = fits.getdata(fits_file.strpath)

    success = ds9_obj.set_np2arr(fits_data)

    assert success == 1

    out_fits = tmpdir.join('out.fits')
    with out_fits.open('w') as f:
        sp.call(['xpaget', ds9_obj.target, 'fits'], stdout=f)

    np.testing.assert_array_equal(fits_data, fits.getdata(out_fits.strpath))


@parametrize('attr', ['target', 'id', 'method'])
def test_ds9_readonly_props(ds9_obj, attr):
    '''Make sure that readonly attributes are such'''

    # we can read them
    getattr(ds9_obj, attr)


@parametrize('attr', ['target', 'id', 'method'])
def test_ds9_readonly_props_fail(ds9_obj, attr):
    '''Make sure that readonly attributes are such'''

    # We can not set them
    with pytest.raises(AttributeError,
                       match="can't set attribute"):
        setattr(ds9_obj, attr, 41)


def test_ds9_extra_prop(ds9_title):
    '''Regression test to make sure that issues like #34 don't happen
    anymore'''
    class DS9_(pyds9.DS9):
        @property
        def frame(self):
            return self.get("frame")

        @frame.setter
        def frame(self, value):
            self.set("frame {}".format(value))

    ds9 = DS9_(target='*' + ds9_title + '*')
    a = ds9.frame
    ds9.frame = int(a) + 1

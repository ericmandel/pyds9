import os


def get_package_data():
    return {
        _ASTROPY_PACKAGE_NAME_ + '.tests': ['coveragerc'],
        'pyds9.tests': [os.path.join('data', '*')]}

"""
PyHue pip module setup definition.
"""

import os
from setuptools import setup

VERSION = '0.0.1'

DESCRIPTION = """\
Pyhue. Module to provide functions to interact with a Phillips Hue bridge.
"""

packages = [
    'pyhue'
]

package_dir = {
    'pyhue': 'pyhue'
}

scripts = [os.path.join('bin', 'hue_bridge_init.py')]

install_requires = ['requests>=2.23.0', 'zeroconf>=0.28.8']

setup(
    name='pyhue',
    version=VERSION,
    description=DESCRIPTION,
    packages=packages,
    package_dir=package_dir,
    include_package_data=True,
    scripts=scripts,
    install_requires=install_requires,
    python_requires=">=3.8"
)

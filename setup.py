"""
PyHue pip module setup definition.
"""
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

scripts = []

install_requires = ['requests>=2.23.0']

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

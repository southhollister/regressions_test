"""setup.py; setuptools control"""

from setuptools import setup
import os


directory = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(directory, 'README.rst'), 'rb') as f:
    long_descr = f.read().decode('utf-8')

with open(os.path.join(directory, 'VERSION'), 'rb') as f:
    version = f.read().decode('utf-8').strip()

setup(
    name='regressions_test',
    version=version,
    packages=['regressions_test'],
    install_requires=['pytest'],
    scripts=['bin/regressions_test'],
    entry_points={
        'console_scripts': ['regressions_test = regressions_test.regressions_test:main']
    },
    long_description=long_descr,
    author='Hollis',
    include_package_data=True
)

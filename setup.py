"""setup.py; setuptools control"""

from setuptools import setup

with open('README.rst', 'rb') as f:
    long_descr = f.read().decode('utf-8')

setup(
    name='regressions_test',
    version='3.2',
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

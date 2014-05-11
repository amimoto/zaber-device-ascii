from __future__ import print_function
from setuptools import setup, find_packages

import zaber.device.ascii

setup(
    name='zaber-device-ascii',
    version=zaber.device.ascii.__version__,
    url='https://gitlab.ripsum.com/aki/zaber-device-ascii',
    license='LGPL v2.1',
    author='Aki Mimoto',
    install_requires=['pyserial>=2.5'],
    author_email='amimoto+zaber-device-ascii@gmail.com',
    description="Support for programmatic access to Zaber's ASCII Devices",
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: OS Independent',
        'Topic :: System :: Hardware :: Hardware Drivers'
        ],
)


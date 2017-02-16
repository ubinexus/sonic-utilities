from setuptools import setup

setup(
    name='sonic-utilities',
    version='1.0',
    description='Command-line utilities for SONiC',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='linuxnetdev@microsoft.com',
    url='https://github.com/Azure/sonic-utilities',
    maintainer='Joe LeVeque',
    maintainer_email='jolevequ@microsoft.com',
    packages=['show'],
    package_data={
        'show': ['aliases.ini']
    },
    scripts=[
        'scripts/boot_part',
        'scripts/coredump-compress',
        'scripts/decode-syseeprom',
        'scripts/generate_dump',
        'scripts/portstat',
        'scripts/sfputil',
    ],
    data_files=[
        ('/usr/lib/python2.7/dist-packages', [
            'dist-packages/bcmshell.py',
            'dist-packages/eeprom_base.py',
            'dist-packages/eeprom_dts.py',
            'dist-packages/eeprom_tlvinfo.py',
            'dist-packages/sff8436.py',
            'dist-packages/sff8472.py',
            'dist-packages/sffbase.py',
            'dist-packages/sfputilbase.py'
            ]
        ),
    ],
    entry_points={
        'console_scripts': [
            'show = show.main:cli',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],
    keywords='sonic SONiC utilities command line cli CLI',
)

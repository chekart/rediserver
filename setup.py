import sys
from distutils.core import setup

if sys.version_info < (3, 5):
    raise NotImplementedError("Sorry only Python 3.5+ is supported")

setup(
    name='rediserver',
    packages=['rediserver'],
    version='0.1',
    description='Pure Python Redis server implementation',
    license='MIT',
    author='chekart',
    url='https://github.com/chekart/rediserver',
    keywords=['redis', 'server',],
    install_requires=[
        'lupa',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ]
)
"""
pindo-cli
--------------

Pindo is a communication platform for humans and machines
"""
from setuptools import setup
from os import path


this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pindo-cli',
    version='0.1.8',
    url='http://github.com/pindo-io/pindo-cli',
    license='MIT',
    author='Team Pindo',
    author_email='team@pindo.io',
    description=('Pindo is a communication platform for humans and machines'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['pindo_cli'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    py_modules=['pindo_cli'],
    install_requires=[
        'Click==7.0',
        'requests==2.20.0',
        'click-spinner==0.1.8'
    ],
    extras_require={
        'test': [
            'pytest==3.10.1',
            'pytest-flake8==1.0.6',
            'pytest-cov==2.6.1'
        ]
    },
    entry_points='''
    [console_scripts]
    pindo=pindo_cli:cli
    ''',
    test_suite="tests",
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ]
)

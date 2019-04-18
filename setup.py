"""
pindo-cli
--------------

Pindo is a communication platform for humans and machines
"""
from setuptools import setup


setup(
    name='pindo-cli',
    version='0.1.4',
    url='http://github.com/pindo-io/pindo-cli',
    license='MIT',
    author='Team Pindo',
    author_email='team@pindo.io',
    description=('Pindo is a communication platform for humans and machines'),
    packages=['pindo_cli'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    py_modules=['pindo_cli'],
    install_requires=[
        'Click==7.0',
        'requests==2.20.0',
        'pytest==4.1',
        'pytest-flake8==1.0.4',
        'pytest-cov==2.6.1',
        'click-spinner==0.1.8',
    ],
    tests_require=[],
    entry_points='''
        [console_scripts]
        pindo=pindo_cli:cli
    ''',
    test_suite="tests",
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

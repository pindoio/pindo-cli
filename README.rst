pindo-cli
=========
.. image:: https://travis-ci.org/pindo-io/pindo-cli.svg?branch=master
    :target: https://travis-ci.org/pindo-io/pindo-cli
    
A simple command line interface for requesting token and test SMS. 

Installation
------------

Install from PyPi using
`pip <http://www.pip-installer.org/en/latest/>`__, a package manager for
Python.

::

   pip install pindo-cli

Don't have pip installed? Try installing it, by running this from the
command line:

::

   $ curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

::

   python setup.py install

You may need to run the above commands with ``sudo``.

Getting Started
---------------

Once you're have install `Pindo CLI` you're ready to go.

::

    pindo --help

::

Create an account
~~~~~~~~~~~~~~~~~

For creating a `Pindo` account you need to provide your `username`, `email`, 
and `password`

::

   pindo register

::


Request a Token
~~~~~~~~~~~~~~~

Requesting a `token` require you to provide your `username` and `password`

::

   pindo register

::

Send a test message
~~~~~~~~~~~~~~~~~~~

Sending a test message will require you providing the requested `token`, a receiver, 
the message your want to send, and also the sender id.

::

   pindo sms

::

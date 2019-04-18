pindo-cli
=========
.. image:: https://travis-ci.org/pindo-io/pindo-cli.svg?branch=master
    :target: https://travis-ci.org/pindo-io/pindo-cli
.. image:: https://badge.fury.io/py/pindo-cli.svg
    :target: https://pypi.python.org/pypi/pindo-cli
.. image:: https://pypip.in/d/pindo-cli/badge.png
    :target: https://crate.io/packages/pindo-cli/

Installation
------------

Install from PyPi using
`pip <http://www.pip-installer.org/en/latest/>`__, a package manager for
Python.

::

   pip3 install pindo-cli

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


Token
~~~~~~~~~~~~~~~

Requesting a `token` require you to provide your `username` and `password`

::

   pindo token

::

Refresh your token
::

   pindo refresh-token

::

Send a test message
~~~~~~~~~~~~~~~~~~~

Sending a test message will require you providing the requested `token`, a receiver, 
the message your want to send, and also the sender id.

::

   pindo sms

::

 
API Usage
~~~~~~~~~~~

The ``pindo api`` needs your Token. You can either pass the token
directly to the constructor (see the code below) or via environment
variables.


.. code:: python
	  import requests

	  token='kbkcmbkcmbkcbc9ic9vixc9vixc9v'
	  hedears = {'Authorization': 'Bearer ' + auth_token}
	  data = {'app' : 'aaaaa'}

	  url = 'http://api.pindo.io'
	  response = requests.post(url, json=data, headers=hedears)
	  print(response)
	  print(response.json())




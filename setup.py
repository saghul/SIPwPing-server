#!/usr/bin/python
# coding=utf8

# Copyright (C) 2011 Saúl Ibarra Corretgé <saghul@gmail.com>
#

import os

from distutils.core import setup

from sipwping import __version__


def find_packages(toplevel):
    return [directory.replace(os.path.sep, '.') for directory, subdirs, files in os.walk(toplevel) if '__init__.py' in files]

setup(name         = "sipwping",
      version      = __version__,
      author       = "saghul",
      author_email = "saghul@gmail.com",
      url          = "http://github.com/saghul",
      description  = "SIPwPing - An easy way to ping SIP servers from the Web",
      classifiers  = [
            "Development Status :: 4 - Beta",
            "License :: OSI Approved :: GNU General Public License (GPL) version 3",
            "Operating System :: OS Independent",
            "Programming Language :: Python"
                     ],
      packages     = find_packages('sipwping'),
      scripts      = ['sipwping-server'],
      data_files   = [('/etc/sipwping', ['config.ini.sample'])]
      )


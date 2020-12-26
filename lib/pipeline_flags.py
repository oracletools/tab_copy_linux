#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""One-line documentation for pipeline_flags module.
A detailed description of pipeline_flags.
"""
__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'


import sys
import exceptions
import os
import re
from pprint import pprint

import lib.flags as flags

FLAGS = flags.FLAGS
#FLAGS ={}

#absolute path where xml pipeline spec is located.
#FLAGS['pipeline_spec_dir']='I:/pipeline/'
#FLAGS['client_dir']='I:/clients/'

"""flags.DEFINE_string('schema_spec',
					'schema.xml',
					'absolute path where schema file is located.')

flags.DEFINE_string('etl_spec',
					'etl.xml',
					'absolute path where etl file is located.')
"""                    
#the temporary directory to use for dumpfiles and log files.  This is used in the ETLEnvironment class.
if os.name == 'nt':
	FLAGS['tmpdir']= 'c:\\tmp\\applog\\'
else:
	FLAGS['tmpdir']= 'tmp/'
			

class PipelineFlags:
  """The Class handling the command line options."""

  def __init__(self, singleton_logger):
	"""Setup the command line flags."""
	self._singleton_logger=singleton_logger
	self._SetConfigFileFlags()
	self.binaries_path = "./"
	self.tmpdir = FLAGS['tmpdir']
	self.release=0
	self._SetOtherFlags()
	#sys.exit(0)

  def _SetConfigFileFlags(self):
	self.pipeline_spec = FLAGS['pipeline_spec']
	assert self._IsFileReadable(self.pipeline_spec), (
		'Pipeline spec file is not readable.')
	self.pipeline = FLAGS['pipeline']
	pprint(FLAGS)
	assert self._IsFileReadable(self.pipeline), (
		'Pipeline etldataflow file is not readable.')

	"""self.schema_spec = FLAGS.schema_spec
	assert self._IsFileReadable(self.schema_spec), (
		'Schema file is not readable.')
	self.etl_spec = FLAGS.etl_spec
	assert self._IsFileReadable(self.etl_spec), (
		'Etl file is not readable.')"""

  def _SetOtherFlags(self):
	if FLAGS.has_key('release') and FLAGS['release']:
		self.release=FLAGS['release']
	#self.code_only = FLAGS['pipeline_spec']
		
  def _CheckFile(self, filename):
	"""Checks for file existence.

	Args:
	  filename: A string represent the path of the file.

	Returns:
	  True: The file specified is existed.
	  False: Otherwise.
	"""
	assert filename, 'filename can not be None.'
	return os.path.lexists(filename)

  def _CheckDir(self, path):
	"""Checks if the given path is a directory.

	Args:
	  path: A string represent the path of the directory.

	Returns:
	  True: The dir specified is existed.
	  False: Otherwise.
	"""
	assert path, 'Path can not be None.'
	return os.path.isdir(path)

  def _IsFileReadable(self, filename):
	"""Check if the file is existed.

	Args:
	  filename: A string represent the path of the file.

	Returns:
	  True: The file specified is readable.
	  False: Otherwise.
	"""
	file_opened = False
	test_file = None
	try:
	  test_file = open(filename, 'r')
	  file_opened = True
	except exceptions.Exception:
	  file_opened = False

	if file_opened:
	  test_file.close()
	return file_opened


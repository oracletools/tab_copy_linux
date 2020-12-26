#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""One-line documentation for Environment.
This module defines a simple class for holding information about
the ETL environment.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import os
import sysutil
import time
import re

from pprint import pprint


#import pipeline_flags
import xml_pipeline_spec
import xml_pipeline
#import xml_schema_spec 
#import xml_etl_spec as etlmeta
import logger, sys

import lib.flags as flags

FLAGS = flags.FLAGS

def confirm(test, testname = "Test", logger=None):
	if not test:
		msg=  "Failed: " + testname
		if logger:
			print logger,  logger._is_singleton_logger
			if logger._is_singleton_logger:
				logger.sys('%s (%s)' % (msg, test) )
			else: 
				logger.error('%s (%s)' % (msg, test) )
			
		raise Exception( '%s (%s)' % (msg, test) )
		
class Environment:
  def __init__(self,flags, singleton_logger):
	"""Initializes object based on the the values in flags.FLAGS.

	# It is therefore important to make sure that FLAGS is properly initialized
	# before creating the Environment.

	# Here are the flags used.  See etl.py for sample settings:
	#    source_schema
	#    tmpdir
	"""
	self._singleton_logger=singleton_logger
	self._logger=None
	self.timestamp_string = time.strftime('%Y%m%d-%H%M%S')
	self._local_temp_dir           = FLAGS['tmpdir']
	self._root_node = 'etldataflow'
	#print FLAGS
	#self._test_spec                = xml_test_spec.FromXML(FLAGS['test_spec'])
	self._etl_spec              = None
	self._schema_spec              = None
	self._pipeline_flags = flags
	self._FLAGS=FLAGS
	self.pipeline_name=None
	self._Prepare()
	
	

  def _Prepare(self):
	"""Finishes attribute initialization for attributes that need to
	   be pulled from files or other resources.
	# Initializes attributes:
	#   schema
	#   etl
	"""

   #try:
	#print self._pipeline_flags.pipeline_spec
	#sys.exit(0)
	self._pipeline_spec = xml_pipeline_spec.FromXML(self._pipeline_flags.pipeline_spec,self.get_logger()) 
	self.process_spec = self._pipeline_spec['process_spec']
	
	self._pipeline = xml_pipeline.FromXML(self._pipeline_flags.pipeline, self._pipeline_spec)
	self._etl_spec = self._pipeline
	self.set_pipeline_name()
	
  def set_pipeline_name(self):
	print self._FLAGS
	
	regexp=re.compile(r'(%[\w\_]+\%)')
	pn = self._pipeline[self._root_node]['name']
	m = re.findall(regexp,pn)
	if m:
		print m
		for arg in m:			
			assert self._FLAGS.get(arg.strip('%')), 'PARAMETER %s is not defined but used in PIPELINE_NAME.' % arg.strip('%')
			pn=pn.replace(arg,self._FLAGS.get(arg.strip('%')))
	self.pipeline_name = pn
	#sys.exit(1)
  def get_pipeline_name(self):
	return self.pipeline_name
  def get_logger(self):
	if self._logger:
		return self._logger
	else:
		return self._singleton_logger

  def get_process_spec(self,spec):
	confirm(self.process_spec.has_key(spec),'Process spec doesn\'t have spec %s.' % spec ,self.get_logger())
	return self.process_spec[spec]
  def pipeline_spec(self):
	return self._pipeline_spec	  
  def get_env_default(self, param):
	env=self.env_default()
	confirm(env['param'].has_key(param),'Pipeline default doesn\'t include param %s.' % param ,self.get_logger())
	return env['param'][param]
	
  def get_env_attr(self, key ):
	attr=None

	env = self.env_default()
	#pprint(env)
	if env['attr'].has_key(key):
		attr=env['attr'][key]
		regexp=re.compile(r'((%)([\w\_]+)(%))')		
		m = re.match(regexp, attr)
		if m:		
			attr_key=m.groups()[2]
			confirm(self.process_spec.has_key(attr_key), 'Attribute %s is not defined in process spec.' % attr_key,self.get_logger())
			attr = self.process_spec[attr_key]		
	else:
		confirm(self.process_spec.has_key(key), 'Attribute %s key is not defined in process spec.' % key, self.get_logger())
		attr=self.process_spec[key]

	return attr	
  def get_env_attr_2(self, key ):
	attr=None
	regexp=re.compile(r'((%)([\w\_]+)(%))')		
	m = re.match(regexp, key)
	if m:
		key=m.groups()[2]
		env = self.env_default()
		#pprint(env)
		if env['attr'].has_key(key):
			attr=env['attr'][key]
			regexp=re.compile(r'((%)([\w\_]+)(%))')		
			m1 = re.match(regexp, attr)
			if m1:		
				attr_key=m1.groups()[2]
				confirm(self.process_spec.has_key(attr_key), 'Attribute %s is not defined in process spec.' % attr_key,self.get_logger())
				attr = self.process_spec[attr_key]		
		else:
			confirm(self.process_spec.has_key(key), 'Attribute %s key is not defined in process spec.' % key, self.get_logger())
			attr=self.process_spec[key]
	else:
		return key
	return attr	
  def get_email_to(self, key ='EMAIL_TO'):
	email=None
	env = self.env_default()
	#pprint(env)
	if env['param'].has_key(key):
		email=env['param'][key]
		#pprint( email)
		regexp=re.compile(r'((%)([\w\_]+)(%))')		
		m = re.match(regexp, email)
		if m:		
			email_key=m.groups()[2]
			confirm(self.process_spec.has_key(email_key), 'Email address %s is not defined in process spec.' % email_key, self.get_logger())
			email = self.process_spec[email_key]		
	else:
		confirm(self.process_spec.has_key(key), 'Email address %s key is not defined in process spec.' % key, self.get_logger())
		email=self.process_spec[key]

	return email
		
	
  def env_default(self):
	env = self.get_process_spec('env')
	confirm(self._pipeline_spec.has_key('default'),'Pipeline spec doesn\'t have <defaults> section.',self.get_logger())
	confirm(self._pipeline_spec['default'].has_key('env'),'Pipeline spec doesn\'t have <defaults>-<env> section.',self.get_logger())
	confirm(self._pipeline_spec['default']['env'].has_key(env),'Pipeline spec doesn\'t have <defaults>-<env>-<%s> section.' % env,self.get_logger())
	#self._singleton_logger.info(env)
	return self._pipeline_spec['default']['env'][env]
	
  def pipeline(self):
	#pprint(self._pipeline)
	#sys.exit(1)
	return self._pipeline[self._root_node]
  def pipeline_globals(self):
	#pprint(self._pipeline)
	#sys.exit(1)
	return self._pipeline[self._root_node]['globals']
  def etl(self):
	return self._etl_spec
  def schema(self):
	return self._schema_spec
 
  def _GetLogDirBase(self, job_or_table_name):
	"""Calculate the base directory for logging for the given job or table name.

	We calculate the log directory name based on the local_temp_dir attribute,
	appended by the job or table name as the name of a subdirectory.

	Args:
	  job_or_table_name: The job or table name that we need.  We expect the name
	  to be valid as a directory name.

	Returns:
	  The required directory name.
	  Typically: {local_temp_dir}/logs/{job_or_table_name}
			 OR  {local_temp_dir}/logs
	"""
	if 0 == len(job_or_table_name):
	  log_extension = "logs/"
	else:
	  log_extension = "logs/%s" % (job_or_table_name)
	#print os.path.join(self._local_temp_dir, log_extension)
	return os.path.join(self._local_temp_dir, log_extension)

  def GetLogDir(self, job_or_table_name):
	"""Calculate the base directory for logging for the given job or table name.

	We calculate the log directory name based on the local_temp_dir attribute,
	appended by the job or table name as the name of a subdirectory.  In
	addition, we differentiate logs by a timestamp string.

	Args:
	  timestamp_string: A string representing an individual point in time.  Must
		be suitable as the name of a directory.  If specified as None, the
		current wall-clock time is used to generate an appropriate string.
	  job_or_table_name: The job or table name that we need.  We expect the name
	  to be valid as a directory name.

	Returns:
	  The required directory name.
	  Typically: {local_temp_dir}\\logs\\{job_or_table_name}\\{timestamp_string}
			 OR  {local_temp_dir}\\logs\\{timestamp_string}
	"""
	log_dir_base = self._GetLogDirBase(job_or_table_name)

	#if timestamp_string is None:
	timestamp_string = self.timestamp_string #time.strftime('%Y%m%d-%H%M%S')

	return os.path.join(log_dir_base, timestamp_string)
  def getLatestDir(self, log_dir_base):
	dir = os.path.join(log_dir_base, 'latest')
	if os.name == 'nt':
	  try:
		sysutil.LocalRmdir(dir)
	  except Exception, e:
		self._singleton_logger.sys(e,__name__)
		#pprint((e))
		#raise e
		
	  sysutil.LocalMkdir(dir,1)
	  return dir

  def SetupStructuredLogger(self, project_name, 
	  job_or_table_name, singleton_logger = None, is_singleton_logger=False):
	"""
	Sets up logging using a logger.StructuredLogger.

	Args:
	  project_name: String representing name of a project.  Must
		be valid as the 'filename' argument to
		logger.set_googlestyle_logfile(filename, log_dir).
	  timestamp_string: String used to differentiate this log
		from other logs run for similar jobs, but at differernt
		times.  Must be valid as a directory name.
	  job_or_table_name: String used to define the job or
		table name for logging.  Must be valid as a directory name.
	  is_singleton_logger: Boolean parameter used to determine whether to
		initialize logging for the singleton logger.logger variable, or to
		create a new StructuredLogger.  If evaluates as True, then the
		singleton logger.logger gets initialized.
	"""
	timestamp_string = self.timestamp_string
	log_dir_base = self._GetLogDirBase(job_or_table_name)
	self._singleton_logger.sys('log_dir_base:  %s' % log_dir_base,__name__)


	if is_singleton_logger:
	  structured_logger = self._singleton_logger
	else:
	  structured_logger = logger.StructuredLogger(is_singleton_logger)
	
	log_dir = structured_logger.GetLogDir(job_or_table_name)
	self._singleton_logger.sys('log_dir:  %s' % log_dir,__name__)
	#log_dir_symlink = os.path.join(log_dir_base, 'latest')
	#log_dir_symlink = self.getLatestDir(log_dir_base)
	#sysutil.LocalMkdir(log_dir_symlink)
	#self._singleton_logger.sys('log_dir_symlink:  %s' % log_dir_symlink,__name__)
	#print self._singleton_logger.sys_file
	#sys.exit(1)

	if not sysutil.LocalMkdir(log_dir, recurse = 1):
	  print "Cannot create log_dir: %s" % log_dir
	  return None
	structured_logger.set_logfile( project_name,'INFO', log_dir)
	structured_logger.set_logfile( project_name,'LOG', log_dir)
	structured_logger.set_logfile( project_name,'SQL', log_dir)
	structured_logger.set_logfile( project_name,'INS', log_dir)
	structured_logger.set_logfile( project_name,'WARN', log_dir)
	structured_logger.set_logfile( project_name,'ERR', log_dir)
	structured_logger.set_logfile( project_name,'FATAL', log_dir)
	#print 'structured_logger.info_file: ', structured_logger.info_file
	#sys.exit(1)
	if 0:
		if os.name=='posix':
		  sysutil.LocalRM(log_dir_symlink)
		  sysutil.LocalMkSymlink(log_dir, log_dir_symlink)
		if os.name == 'nt':
		  try:
			sysutil.LocalRmdir(log_dir_symlink)
		  except Exception, e:
			self._singleton_logger.sys(e,__name__)
		  sysutil.LocalMkdir(log_dir_symlink)
	structured_logger._is_structured_logger =False
	if singleton_logger:
		structured_logger._singleton_logger=singleton_logger
	
	self._logger=structured_logger
	#print type(self._logger)
	#sys.exit(0)
	return self._logger

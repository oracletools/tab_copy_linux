#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""A structured logging library for all of our data warehousing needs.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import os
import time
import sys
import re
import datetime
import string
import commands
import tempfile

from pprint import pprint


ExtractEvent   = 'EXTRACT'
TransformEvent = 'TRANSFORM'
PublishEvent   = 'PUBLISH'
LoadEvent      = 'LOAD'
#EtlEvent       = 'ETL_PIPELINE'
TestEvent       = 'TEST'
SysEvent       = 'SYSTEM'
StatsEvent     = 'STATS'

ALL            = 'ALL'

class StructuredLogger:
	def __init__(self,is_singleton_logger=True):
		self.time_format = '%Y-%m-%d %H:%M:%S'
		self.proc_start_time = (time.time())
		self.ptc = datetime.datetime.now()
		self.start_time = self.proc_start_time
		self._is_singleton_logger=is_singleton_logger
		self._singleton_logger =None
		self.joblogid = 0
		self.datasource = ''
		self.line_number=''
		self.co_name=''
		self.datadate = ''
		self.eventname = ''
		self.jobname = TestEvent
		self.sys_file = None
		self.info_file = None
		self.log_file = None
		self.sql_file = None
		self.ins_file = None
		self.code_file = None
		self.warn_file = None
		self.err_file = None
		self.fatal_file = None
		self._local_temp_dir = 'tmp/'
		self.sys_filename = ''
		self.info_filename = ''
		self.sql_filename = ''
		self.ins_filename = ''
		self.log_filename = ''
		self.code_filename = None
		self.warn_filename = None
		self.err_filename = None
		self.fatal_filename = None
		self.enabled = True
		self._ns_log_dir = None
		self._s_log_dir = None
		self.timestamp_string = time.strftime('%Y%m%d_%H%M%S')
		self.temp_file_name = tempfile.mkstemp()[1]
		
		if is_singleton_logger:
			
			self.make_file(self.sys_file, 'syslog.%s' % self.proc_start_time, 'SYS')

	def flush(self, file):
		if file is not None and self.is_enabled():
			file.flush()
 
	def get_ts(self):
		return '%s_%s' % (time.strftime('%Y%m%d_%H%M'), datetime.datetime.now().microsecond) 
	def escape(self, rawstr):
		if rawstr is not None:
			if type(rawstr) is not str:
				rawstr = str(rawstr)

		rawstr = rawstr.replace("\\","\\\\")
		rawstr = rawstr.replace("\'","\\\'")
		rawstr = rawstr.replace("\n"," ")
		rawstr = rawstr.replace("|", "\\|")
		return rawstr

	def is_enabled(self):
		return self.enabled

	def enable(self):
		"""Enable logging for this logger."""
		self.enabled = True

	def disable(self):
		"""Disable logging."""
		self.enabled = False
	def getElapsedSec(self):
		c=datetime.datetime.now() - self.ptc
		return float(c.seconds)+ float(c.microseconds/1000)/1000
		
	def getLogString(self, message):
		message = self.escape(message)
		#time.sleep(1)
		tc=datetime.datetime.now()
		end_time = (time.time())
		#print 'set_joblogid = %d delta = %s' % (self.joblogid, end_time)
		c=tc-self.ptc
		#pprint(dir(c))
		if self.joblogid == 0:
			logmsg = "%02d:%02d.%03d|%s,%s|%s" % \
				(#self.jobname, self.eventname, 
				 #end_time - self.start_time, 
				 round(c.seconds/60),c.seconds%60,c.microseconds/1000, #self.datasource, 
				 self.co_name,
				 self.line_number, message )       
				 #string.rstrip(message,"\n"))
		else:
			logmsg = "%d|%s|%s|%s|%s|\n" % \
				(self.joblogid, self.jobname, self.eventname, self.datasource,
				 message)
		
		#print self.start_time,end_time
		#print tc-self.ptc
		self.start_time = end_time
		#print logmsg
		#sys.exit(0)
		return logmsg #string.rstrip(logmsg,".") 
	def get_jobid(self):
		return self.timestamp_string

	def get_logdir(self):
		if self._is_singleton_logger:
			if self._s_log_dir:
				return  self._s_log_dir
			else:
				self._s_log_dir = '%s/logs/%s' % (self._local_temp_dir,self.timestamp_string)
				return self._s_log_dir
		else:
			if self._ns_log_dir:
				return self._ns_log_dir
			else:
				self.warn('ns logdir is not set.')
				self.warn('setting ns logdir to %s' % self.GetLogDir(''))
				return self._ns_log_dir
				
		return '%s/logs/%s' % (self._local_temp_dir,self.timestamp_string)
				
				
	def make_file(self, file, filename, type):
		if file is None:
			timestamp_string = self.timestamp_string #time.strftime('%Y%m%d-%H%M%S')
			log_dir=self.get_logdir()
			command = 'mkdir -p %s' % log_dir
			#print command
			(exitstatus, output) = commands.getstatusoutput(command)
			#print 'code:%s:command:%s:status:%d:output:%s' % (__name__,command, exitstatus, output)
			if exitstatus is not 0:
				raise Exception('Could not create log dir %s' % log_dir)
			
			self.set_logfile( filename,type, log_dir)
			#self.set_logfile('syslog', log_dir)	
	def log_message(self, message, type):
		#print '%s: %s, file: %s' % (__name__, self.is_enabled(), self.file)
		if not self.is_enabled():
			return
		#if type=='SYS' and self.sys_file in None:
			#self.make_file(self.sys_file, 'syslog', 'SYS')
		#self.make_file(self.info_file, self.info_filename, 'INFO')



		
		if self.is_enabled():
			msg= "%s\t\n" % (self.getLogString(message))
			if type=='INFO' and self.info_file:
				self.info_file.write(msg)
				self.flush(self.info_file)
			if type=='LOG' and self.log_file:
				self.log_file.write(msg)
				self.flush(self.log_file)
			if type=='ERR' and self.err_file:
				self.err_file.write(msg)
				self.flush(self.err_file)
			if type=='SQL' and self.sql_file:
				self.sql_file.write(msg)
				self.flush(self.sql_file)
			if type=='INS' and self.ins_file:
				self.ins_file.write(message)
				self.flush(self.ins_file)
				
			if type=='WARN' and self.warn_file:
				self.warn_file.write(msg)
				self.flush(self.warn_file)
			if type=='FATAL' and self.fatal_file:
				self.fatal_file.write(msg)
				self.flush(self.fatal_file)
				
			if type=='SYS' and self.sys_file:
				self.sys_file.write(msg)
				self.flush(self.sys_file)				
			
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
		self._ns_log_dir= os.path.join(self._local_temp_dir, log_extension)
		return self._ns_log_dir

	def GetLogDir(self,  job_or_table_name):
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

		self._ns_log_dir = os.path.join(log_dir_base, self.timestamp_string)
		return self._ns_log_dir
	
	def log_code(self, message):
		if not self.is_enabled():
			return

		if self.code_file is None:
			import commands
			#print self.getLogString(message)

			timestamp_string =  self.timestamp_string #time.strftime('%Y%m%d-%H%M%S')
			log_dir='tmp/logs/%s/%s' % (self.jobname,timestamp_string)
			command = 'mkdir -p %s' % log_dir
			(exitstatus, output) = commands.getstatusoutput(command)
			if exitstatus is not 0:
				raise Exception('Could not create system log dir %s' % log_dir)

			#self.set_googlestyle_code_logfile('codelog', log_dir)

		if self.is_enabled():
			self.code_file.write('%s\n' % message)
			self.flush()

	def SetCodeInfo(self, depth,fname,line):
		"""Return true if the object is a code object.

		Code objects provide these attributes:
			co_argcount     number of arguments (not including * or ** args)
			co_code         string of raw compiled bytecode
			co_consts       tuple of constants used in the bytecode
			co_filename     name of file in which this code object was created
			co_firstlineno  number of first line in Python source code
			co_flags        bitmap: 1=optimized | 2=newlocals | 4=*arg | 8=**arg
			co_lnotab       encoded mapping of line numbers to bytecode indices
			co_name         name with which this code object was defined
			co_names        tuple of names of local variables
			co_nlocals      number of local variables
			co_stacksize    virtual machine stack space required
			co_varnames     tuple of names of arguments and local variables"""
		#pprint(dir(sys))
		if hasattr(sys, '_getframe'):
			frame = sys._getframe(depth)
			self.line_number= frame.f_lineno
			regexp=re.compile(r'(.*)\/([\w\_]+\.[\w]{2,3})')
			#print 'frame.f_code.co_filename', ((frame.f_code.co_filename))
			
			m = re.match(regexp, str(frame.f_code.co_filename))
			filename=frame.f_code.co_filename
			#print 'before', filename
			if m:
				#print filename
				#print 0,m.group(0)
				#print 1,m.group(1)
				#print 2,m.group(2)
				filename= m.group(2)
			self.co_name= '%s:%s' % (filename,frame.f_code.co_name) 
		else:
			self.line_number=line
			self.co_name=fname
		#print 'after', filename
		#print self.co_name
		#sys.exit(1)
    
	def sys(self, message, fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		if self._is_singleton_logger:
			if self.sys_file:
				self.log_message(message,'SYS')
				#print message
		else:
			print "WARNING: syslog in non-singleton logger." 
			self._log(message)
			
	def _log(self,message):
		if self.log_file:
			self.log_message(message,'LOG')
		else: 
			print "Log file is invalid."
	def _sys(self,message):
		if self.sys_file:
			self.log_message(message,'SYS')
		else: 
			print "Sys file is invalid."	
	def _info(self,message):
		if self.info_file:
			self.log_message(message,'INFO')
		else: 
			print "Info file is invalid."	

	def _warn(self,message):
		if self.warn_file:
			self.log_message(message,'WARN')
		else: 
			print "Warn file is invalid."	
	def _sql(self,message):
		if self.sql_file:
			self.log_message(message,'SQL')
		else: 
			print "Sql file is invalid."
	def _ins(self,message):
		if self.ins_file:
			self.log_message(message,'INS')
		else: 
			print "Ins file is invalid."			
	def _err(self,message):
		if self.err_file:
			self.log_message(message,'ERR')
		else: 
			print "Err file is invalid."
	def _fatal(self,message):
		if self.fatal_file:
			self.log_message(message,'FATAL')
		else: 
			print "Fatal file is invalid."				
	def info(self, message, fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		if self._is_singleton_logger:
			self._sys(message)
		else:
			self._info(message)
			self._log(message)
		print message 
		

	def code(self, message,fname='n/a', line =0):		
		self.log_code(message)
		#pprint(message)
	def sql(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg=message
		if self._is_singleton_logger:
			self._sys(msg)
		else:
			
			self._sql(msg)
			self._log(msg)
		#print msg		  
	def ins(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg=message
		if self._is_singleton_logger:
			self._sys(msg)
		else:
			
			self._ins(msg)
			self._log(msg)

	def log(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg=message
		if self._is_singleton_logger:
			self._sys(msg)
		else:

			self._log(msg)
		#print msg
	def warn(self, message,fname='n/a', line =0):
		self.warning(message,fname, line)
	def warning(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg="** WARNING ** %s" % message
		if self._is_singleton_logger:
			self._sys(msg)
		else:
			
			self._warn(msg)
			self._info(msg)
			self._log(msg)			
	
		print msg

	def error(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg="## ERROR ** %s" % message
		if self._is_singleton_logger:
			self._sys(msg)
		else:
			
			self._err(msg)
			self._info(msg)
			self._log(msg)
		print msg

	def fatal(self, message,fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		msg="** FATAL ** : %s" % message
		#print self.getLogString("** FATAL ** %s" % message) 
		if self._is_singleton_logger:
			self._sys(msg)
		else: 
			self._fatal(msg)
			self._info(msg)
			self._log(msg)
		print msg
		sys.exit(1) 

	def set_datasource(self, datasource):
		self.datasource = self.escape(datasource)
	 
	def set_datadate(self, datadate):
		self.datadate =datadate

	def set_eventname(self, eventname):
		self.eventname = self.escape(eventname)

	def set_jobname(self, jobname):
		self.jobname = self.escape(jobname)

	def set_joblogid(self, joblogid):
		self.joblogid = joblogid

	def set_logfile2(self, file):
		"""We don't currently support setting logfile directly."""
		pass

	def logfile_name(self, type='SYS'):
		
		if type=='SYS' and self._is_singleton_logger:
			#print "inside logfile_name: ", type, self._is_singleton_logger
			return self.sys_filename
		else:
			if type=='SYS' and self._singleton_logger:
				return self._singleton_logger.logfile_name(type)
		if type=='INFO':
			return self.info_filename
		return ''

	def set_logfile(self, filename, type,log_dir):
		if not self.is_enabled():
		  return
		
		
		filename = '%s/%s.%s' % (log_dir, filename, type)
		file = open(filename, 'w')
		os.chmod(filename, 0744)
		#print 'set_logfile=',filename
		if type=='INFO':
			self.info_filename=filename
			self.info_file=file
		if type=='LOG':
			self.log_filename=filename
			self.log_file=file		
		if type=='SQL':
			self.sql_filename=filename
			self.sql_file=file
		if type=='INS':
			self.ins_filename=filename
			self.ins_file=file

		if type=='WARN':
			self.warn_filename=filename
			self.warn_file=file	
		if type=='ERR':
			self.err_filename=filename
			self.err_file=file	
		if type=='FATAL':
			self.fatal_filename=filename
			self.fatal_file=file
		if type=='SYS':
			#print 'self.sys_filename= ',filename
			self.sys_filename=filename
			self.sys_file=file


	def set_googlestyle_code_logfile(self, filename, log_dir):
		if not self.is_enabled():
		  return
		
		self.code_filename = '%s/%s.INFO' % (log_dir, filename)
		self.code_file = open(self.code_filename, 'w')
		os.chmod(self.code_filename, 0744)

logger = StructuredLogger()

def info(message, fname='n/a', line =0):
  logger.info(message,fname,line)

def code(message):
  logger.code(message)
  
def warning(message):
  logger.warning(message)
  
def error(message):
  logger.error(message)

def fatal(message):
  logger.fatal(message)
  sys.exit(1)

def flush():
  logger.flush()

def flush_thread_specific_logfile():
  pass

def set_datasource(datasource):
  logger.set_datasource(datasource)

def set_datadate(datadate):
  logger.set_datadate(datadate)

def set_eventname(eventname):
  logger.set_eventname(eventname)

def set_jobname(jobname):
  logger.set_jobname(jobname)

def set_joblogid(joblogid):
  logger.set_joblogid(joblogid)

def set_logfile(logfile):
  logger.set_logfile(logfile)

def logfile_name():
  return logger.logfile_name()

def set_logfile(file, filename, ext,log_dir):
  logger.set_logfile(file, filename, ext,log_dir)

def disable():
  logger.disable()

def enable():
  logger.enable()

def is_enabled():
  return logger.is_enabled()

def main(_):
  logger.info(ExtractEvent)

if __name__ == '__main__':
  #app.start()
  pass

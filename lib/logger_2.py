#!/usr/bin/python2.4
#
# Copyright 2009  Inc.  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Ricky Wong)

"""A structured logging library for all of our data warehousing needs.
"""

import os
import time
import sys
import re
import datetime
import string
import commands

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
	def __init__(self):
		self.time_format = '%Y-%m-%d %H:%M:%S'
		self.proc_start_time = (time.time())
		self.ptc = datetime.datetime.now()
		self.start_time = self.proc_start_time
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
		self.code_file = None
		self.sys_filename = 'tmp/'
		self.info_filename = 'tmp/'
		self.sql_filename = 'tmp/'
		self.log_filename = 'tmp/'
		self.code_filename = None
		self.enabled = True

	def flush(self, file):
		if file is not None and self.is_enabled():
			file.flush()
 

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
		"""Disable logging for this logger."""
		self.enabled = False

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
	def make_file(self, file, filename, type):
		if file is None:
			timestamp_string = time.strftime('%Y%m%d-%H%M%S')
			log_dir='tmp/logs/%s/%s' % (self.jobname,timestamp_string)
			command = 'mkdir -p %s' % log_dir
			#print command
			(exitstatus, output) = commands.getstatusoutput(command)
			#print 'code:%s:command:%s:status:%d:output:%s' % (__name__,command, exitstatus, output)
			if exitstatus is not 0:
				raise Exception('Could not create log dir %s' % log_dir)
			
			self.set_logfile(file, filename,type, log_dir)
			#self.set_logfile('syslog', log_dir)	
	def log_message(self, message, type):
		#print '%s: %s, file: %s' % (__name__, self.is_enabled(), self.file)
		if not self.is_enabled():
			return

		self.make_file(self.sys_file, self.sys_filename, 'SYS')
		self.make_file(self.info_file, self.info_filename, 'INFO')



		#
		if self.is_enabled():
			#pprint(dir(self.file))
			self.info_file.write("%s\t\n" % (self.getLogString(message)))
			self.flush(info_file)

	def log_code(self, message):
		if not self.is_enabled():
			return

		if self.code_file is None:
			import commands
			#print self.getLogString(message)

			timestamp_string = time.strftime('%Y%m%d-%H%M%S')
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
    

	def info(self, message, fname='n/a', line =0):
		self.SetCodeInfo(2,fname,line)
		self.log_message(message, 'INFO')
		print message 

	def code(self, message):
		self.log_code(message)
		pprint(message)
		  

	def warning(self, message):
		msg="** WARNING ** %s" % message
		self.log_message(msg,'INFO')
		print msg

	def error(self, message):
		self.log_message("** ERROR ** %s" % message,'INFO')
		print self.getLogString("** ERROR ** %s" % message) 
		#sys.exit(1)

	def fatal(self, message):
		self.log_message("** FATAL ** : %s" % message,'INFO')
		print self.getLogString("** FATAL ** %s" % message) 
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

	def set_logfile(self, file):
		"""We don't currently support setting logfile directly."""
		pass

	def logfile_name(self):
		return self.info_filename

	def set_logfile(self, file, filename, ext,log_dir):
		if not self.is_enabled():
		  return
		
		filename = '%s/%s.%s' % (log_dir, filename, ext)
		file = open(filename, 'w')
		os.chmod(filename, 0744)


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

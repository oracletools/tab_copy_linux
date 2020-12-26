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

#from google3.pyglib import app
#import gflags as flags

from pprint import pprint


ExtractEvent   = 'EXTRACT'
TransformEvent = 'TRANSFORM'
PublishEvent   = 'PUBLISH'
LoadEvent      = 'LOAD'
ETLEvent       = 'ETL_PIPELINE'
TESTEvent       = 'TEST_PIPELINE'
SysEvent       = 'SYSTEM'
StatsEvent     = 'STATS'

ALL            = 'ALL'

class StructuredLogger:
  def __init__(self):
    self.time_format = '%Y-%m-%d %H:%M:%S'
    self.proc_start_time = int(time.time())
    self.start_time = self.proc_start_time
    self.joblogid = 0
    self.datasource = ''
    self.line_number=''
    self.co_name=''
    self.datadate = ''
    self.eventname = ''
    self.jobname = ETLEvent
    self.file = None
    self.filename = '/tmp/'
    self.enabled = True

  def flush(self):
    if self.file is not None and self.is_enabled():
      self.file.flush()

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
    end_time = int(time.time())
    if self.joblogid == 0:
      logmsg = "%03d|%s|(%s,%s)|%s" % \
        (#self.jobname, self.eventname, 
         end_time - self.start_time, self.datasource, self.co_name,
         self.line_number,         
         message)
    else:
      logmsg = "%d|%s|%s|%s|%s|" % \
        (self.joblogid, self.jobname, self.eventname, self.datasource,
         message)
    self.start_time = end_time

    return logmsg

  def log_message(self, message):
    if not self.is_enabled():
      return

    if self.file is None:
      print self.getLogString(message)
    elif self.is_enabled():
      self.file.write('%s\n' % (self.getLogString(message)))
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
        m = re.match(regexp, str(frame.f_code.co_filename))
        filename=__file__
        if m:
            filename= m.group(2)+':'
        self.co_name= filename+frame.f_code.co_name 
    else:
        self.line_number=line
        self.co_name=fname
    

  def info(self, message, fname='n/a', line =0):
    self.SetCodeInfo(2,fname,line)
    self.log_message(message)
    print message 
	#, broadcast
    #if broadcast:
      #for logger in broadcast:
        #logger.SetCodeInfo(2)
        #logger.log_message(message)		
      

  def warning(self, message):
    self.log_message("** WARNING ** %s" % message)

  def error(self, message):
    self.log_message("** ERROR ** %s" % message)

  def fatal(self, message):
    self.log_message("** FATAL-ERROR ** : %s" % message)
    filename= self.filename
    file= self.file
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
    return self.filename

  def set_googlestyle_logfile(self, filename, log_dir):
    if not self.is_enabled():
      return
    self.filename = '%s/%s.INFO' % (log_dir, filename)
    self.file = open(self.filename, 'w')
    os.chmod(self.filename, 0744)

logger = StructuredLogger()

def info(message):
  logger.info(message)

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

def set_googlestyle_logfile(filename, log_dir):
  logger.set_googlestyle_logfile(filename, log_dir)

def disable():
  logger.disable()

def enable():
  logger.enable()

def is_enabled():
  return logger.is_enabled()

def main(_):
  logger.info(ExtractEvent, 'blah')

if __name__ == '__main__':
  #app.start()
  pass

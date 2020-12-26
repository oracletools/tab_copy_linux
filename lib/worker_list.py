#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains worker list class.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

#import sys, os
#import string
#import re
#import timeit
#import traceback,time
#import StringIO
from pprint import pprint
#from copy import Copy
#import fcntl, shlex, subprocess
#from subprocess import Popen, PIPE
#import shlex
import threading
#from datetime import date, timedelta
#import types


STACKTRACE_MAX_DEPTH = 2

def confirm(test, testname = "Test", logger=None):
	if not test:
		msg=  "Failed: " + testname
		if logger:
			logger.error('%s (%s)' % (msg, test) )
		else:
			self._logger.error('%s (%s)' % (msg, test) )
			#raise Exception( '%s (%s)' % (msg, test) )	

class WorkerList():
	"""A class for extracting dimension data from csv file."""

	def __init__(self, extract_logger):
		"""Worker List
		"""
		self.wl=[]
		self._logger=extract_logger
		#threading.Thread.__init__ ( self )	
	def append(self,worker):
		se;f.wl.append(worker)


#!/usr/bin/python2.4
#
# Copyright 2012 .  All Rights Reserved.
# 
# Original author alex_buz@gmail.com  (Alex Buzunov)

"""This module contains all data export routines
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from lib.app_utils import app_utils

STACKTRACE_MAX_DEPTH = 2



class export_utils(app_utils):
	"""A class for data export."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes metadata collector.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def export_sql(self, args):
		(q, to_tab) = args
		sqdir= '%s/sql' % self._logger.get_logdir()
		sqfn='%s/%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],to_tab)
		if self.is_set('PARTITION'):
			sqfn='%s/%s.%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],to_tab,self._pp['PARTITION'])
		if not os.path.isdir(sqdir):
			try:
				os.mkdir(sqdir) 
			except Exception, e:
							print 'Created in other thread.', e.strerror
		sqf = open(sqfn, "w")
		sqf.write(q)
		sqf.close()	
		return sqfn 
		
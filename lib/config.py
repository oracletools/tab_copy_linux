#!/usr/bin/python2.4
#
# Copyright 2011 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains worker list class.
"""
import time
import logging , sys

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

timestamp =  time.strftime('%Y%m%d_%H%M%S')		
spool_dir = '/home/sz18178/data_spooler_pa_test/out'

FORMAT = '%(asctime)-15s %(module)s %(message)s'
logging.basicConfig(format=FORMAT)

#d = { 'name' : __name__ }
logger = logging.getLogger('pl_parser')
logger.setLevel(logging.DEBUG)

def	confirm2(self,test, testname = "Test"):
		if not test:
			msg=  "Failed: " + testname
			if logger:
				logger.error('%s (%s)' % (msg, test) )
			sys.exit(1)
			
def confirm(test, testname = "Test"):
	if not test:
		msg=  "Failed: " + testname
		if logger:
			logger.error('%s (%s)' % (msg, test) )
		else:
			print ('%s (%s)' % (msg, test) )
		sys.exit(1)
		
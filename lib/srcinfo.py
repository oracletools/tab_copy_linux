#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
#

"""__file__ and __line__ replacement

"""

__author__ = "alexbuzunov@gmail.com (Alex Buzunov)"

import inspect 
import sys 

def currentline(): 
	return inspect.currentframe().f_back.f_lineno 

def currentfile(): 
	return inspect.currentframe().f_back.f_code.co_filename 
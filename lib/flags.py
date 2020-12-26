#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""Pipeline flags parser class
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'


import sys, os
import re
if os.name == 'nt':
	from lib.CmdLine import CmdArgParser
else: 
	import getopt
	
if os.name == 'nt':
	import System.Environment

FLAGS ={}
def usage():
	print 'Usage:'
def confirm(test, testname = "Test", logger=None):
    if not test:
		msg=  "Failed: " + testname
		if logger:
			logger.fatal('%s (%s)' % (msg, test) )
		else:
			raise Exception( '%s (%s)' % (msg, test) )	
			
if len(sys.argv) > 1:
	if os.name == 'nt':
		parser = CmdArgParser(sys.argv)
		parser = CmdArgParser(System.Environment.CommandLine)
		#print (sys.argv)
		#print (parser.Keys)
		for key in parser.Keys:
			FLAGS[key]=parser[key]
	else:
		#print sys.argv
		#args ='pipeline_spec test_plan TABLE_NAME INDEX_NAME FROM_TABLE pipeline release'.split()
		#optlist, args = getopt.getopt(sys.argv[1:], 'x', )
		try:
			optlist, args = getopt.getopt(sys.argv[1:], 'x:', [ 'pipeline_spec=','PARTITION=', 'TABLE_NAME=','DEGREE=','INDEX_NAME=','COB_YEAR=','SOURCE_FILE=','FROM_TABLE=','TO_TABLE=','pipeline=','release='])
			#print optlist
		except getopt.GetoptError, err:
			# print help information and exit:
			print str(err) # will print something like "option -a not recognized"
			usage()
			sys.exit(2)
		#print args
		for arg_id in range(0, len(optlist)):
			FLAGS[optlist[arg_id][0].strip('-')]=optlist[arg_id][1]
			
		print FLAGS
		#sys.exit(1)
		if FLAGS.has_key('INDEX_NAME'):
			assert FLAGS.get('INDEX_NAME'),  'INDEX_NAME is not set'
			rx= re.compile( r'(\W+)')		
			test = rx.sub( '', FLAGS['INDEX_NAME'])
			#print test
			confirm(test==FLAGS['INDEX_NAME'].strip("'"),'Bad index name.')
		if 'FROM_TABLE' in FLAGS:
			assert FLAGS.get('FROM_TABLE'),  'FROM_TABLE is not set'
			#print FLAGS.keys()
			#sys.exit(1)
			if 'TO_TABLE' in FLAGS:
				confirm(FLAGS['FROM_TABLE'] <> FLAGS['TO_TABLE'], 'Target and destination are the same.')
		if FLAGS.has_key('PARTITION'):
			assert len(FLAGS['PARTITION'].strip().strip("'"),'Bad partition name.')				
			rx= re.compile( r'(\W+)')		
			test = rx.sub( '', FLAGS['PARTITION'])
			#print test
			confirm(test==FLAGS['PARTITION'].strip("'"),'Bad partition name.')	
		if FLAGS.has_key('SOURCE_FILE'):
			assert FLAGS.get('SOURCE_FILE'),  'SOURCE_FILE is not set'
			rx= re.compile( r'(\W+)')		
			test = rx.sub( '', FLAGS['SOURCE_FILE'])
			#print test
			confirm(test==FLAGS['SOURCE_FILE'].strip("'"),'Bad source file name.')	
		#print FLAGS
		#sys.exit(1)
		if FLAGS.has_key('COB_YEAR'):
			assert FLAGS.get('COB_YEAR'),  'COB_YEAR is not set'
			test = int( FLAGS['COB_YEAR'])
		if FLAGS.has_key('DEGREE'):
			assert FLAGS.get('DEGREE'),  'DEGREE is not set'
			test = int( FLAGS['DEGREE'])			
		if FLAGS.has_key('TIMESTAMP'):
			assert FLAGS.get('TIMESTAMP'),  'TIMESTAMP is not set'
			
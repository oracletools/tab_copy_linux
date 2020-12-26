#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all hierarchy transformation routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os
if os.name == 'nt':
	import clr
	from ctypes import * 
import string
import re
import timeit
import traceback,time
import StringIO
from pprint import pprint
from copy import Copy
#import fcntl, shlex, subprocess
from subprocess import Popen, PIPE
import shlex
import threading
from datetime import date, timedelta
import types, pickle
from lib.common_utils import utils, confirm
from lib.adjusted2nested import *

STACKTRACE_MAX_DEPTH = 2



class hierarchy(utils):
	"""A class for hierarchy maintenance."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		#Copy.__init__(self, pipelinemeta, None, extract_logger)
		self._result=[]
		#self._gwc={} # global worker cache
		self._wc={} # worker cache
		#self._global_result=[]
		self._process_meta= pipelinemeta["process_spec"]
		self._pipeline_flags=environment._pipeline_flags
		self._FLAGS=environment._FLAGS
		self._connector= pipelinemeta["connector"]
		self._output_files = {}
		self._environment=environment
		self._logger = extract_logger
		self._pipeline= self._environment.pipeline()

		self._globals=self._pipeline['globals']
		self._env_default=self._environment.env_default()

		self._etl_object=None
		self._pp={} #parsed params
		self._p ={} #unparsed params
		self.confirm=confirm

		
	def adj2nested(self, etl_object, logger):
		""" Transforms adjusted list hierarchy to nested set."""
		#global root
		self.set_params(etl_object, logger)
		
		#sys.exit(1)
		out=[]
		latest_tabs=[]
		if 'INPUT_FILE' not in self._pp:
			#from_file_dic= self.get_latest_output_files()
			latest_tabs=self.get_latest_tables()
		else:
			latest_tabs.append(self._pp['INPUT_FILE'])
		#self.confirm('OUTPUT_FILE' in self._gwc, 'INPUT_FILE is not set.')
		tab=latest_tabs[0]
		self._pp['_COLUMNS']={}
		self._pp['_TABLE']=[]
		self._pp['_OUTPUT_FILE']={}
		from_file = self.get_latest_output_files()[tab]
		self.confirm(len(from_file)>0, 'INPUT_FILE name is undefined.')
		print from_file
		
		logger.info('#### START adj2nested of %s.' % tab)		
		
		#pprint(ttn)
		#print from_file
		#sys.exit(1)
		#pprint(self._pp)
		root = None
		if 1:
			confirm(self.is_set('ROOT_NODE_VALUE'),'ROOT_NODE_VALUE is not set')
			root=self._pp['ROOT_NODE_VALUE']
			prnt =None
			child_col ='CHILD'
			if 'CHILD_COLUMN' in self._pp:
				child_col =self._pp['CHILD_COLUMN']

			parent_col ='PARENT'
			if 'PARENT_COLUMN' in self._pp:
				parent_col =self._pp['PARENT_COLUMN']
			column_term='|'
			prnt = load_hier(root, from_file, ttn, (child_col,parent_col), column_term)
			
			#print prnt
			#sys.exit(1)
			#set_delta(ttn[root],1)
			(left,right)=set_interval(ttn[root])
			#ttn[root][5]=right+1
			
			ttn[root][1]=prnt
			#pprint(tnt)
			left_col ='LEFT'
			if 'LEFT_COLUMN' in self._pp:
				left_col =self._pp['LEFT_COLUMN']

			right_col ='RIGHT'
			if 'RIGHT_COLUMN' in self._pp:
				right_col =self._pp['RIGHT_COLUMN']
			
			#out_fn= 'export_hier_small_nn_10.log'
			out_fn=self.get_log_fn('data','hier',tab)
			print out_fn
			#export_hier_old()
			out_header=export_hier(out_fn,from_file, ttn, (child_col,parent_col),(left_col,right_col),column_term)
			if 1: # show tree
				prev_lev=1
				for n in traverse(root,prev_lev, ''):
					#pprint(n[0])
					print '--'* n[1], n[0][0], '(', n[0][4],',', n[0][5],')'
		sys.exit(1)
		logger.info('#### END adj2nested of %s.' % tab)
		
		confirm( tab,'Table name is undefined')
		if '_OUTPUT_FILE' not in self._pp:
			self._pp['_OUTPUT_FILE']={}
		if '_COLUMNS' not in self._pp:				
			self._pp['_COLUMNS']={}
		if '_TABLE' not in self._pp:
			self._pp['_TABLE']=[]
		self._pp['_OUTPUT_FILE'][tab]=out_fn
		self._pp['_COLUMNS'][tab]=out_header
		self._pp['_TABLE'].append(tab)
		self._gwc['LATEST']={'COLUMNS':self._pp['_COLUMNS'],
							 'FLAGS':self._FLAGS, 
							 'TABLE':self._pp['_TABLE'],
							 'OUTPUT_FILE':self._pp['_OUTPUT_FILE']}
		#pprint(self._gwc['LATEST'])
			
		#sys.exit(1)
		self.cleanup()
		if 'EMAIL_TO' in self._pp and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0			


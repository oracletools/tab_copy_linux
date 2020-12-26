#!/usr/bin/python2.4
#
# Copyright 2012 .  All Rights Reserved.
# 
# Original author alex_buz@gmail.com  (Alex Buzunov)

"""This module contains all index maintenance routines
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from lib.app_utils import app_utils

STACKTRACE_MAX_DEPTH = 2



class index_utils(app_utils):
	"""A class for index maintenance."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes metadata collector.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def rebuild_tab_indexes(self,to_db,tt,options):
		(tab, to_tab)=tt
		#print tab, to_tab
		regexp=re.compile(r'INDEX:([\w\d\_]+)')
		#self._pp['FROM_DB'] =self._pp['TO_DB']
		assert to_db, 'TO_DB is not set.'
		
		
		q="""set heading off pagesize 0
		select 'INDEX:'||index_name from 
		user_indexes where status='UNUSABLE' and table_name='%s';""" %to_tab[1]
		
		pt = options.get('_PARTITION')
		
		if pt:
			q="""set heading off pagesize 0
			select 'INDEX:'||index_name from 
				all_ind_partitions where index_name in
				(select index_name from all_indexes where table_name='%s')
				and status='UNUSABLE' and partition_name='%s';""" % (to_tab[1],pt)
		
		#print q
		(r, status) = self.do_query(to_db, q,0,regexp)
		pprint(r)
		#sys.exit(1)
		
		part=''
		if pt:
			part = ' PARTITION %s ' %  pt
		if len(r):
			self._logger.info('### Found %d unusable indexes for table %s.' % (len(r), tab))
			for index in r:
				idx=index[0].strip()
				if len(idx):
					self._logger.info('### START Rebuilding index %s.' % idx)
					q = "ALTER INDEX %s REBUILD %s PARALLEL 12;" % (idx,part)
					print q 
					#sys.exit(1)
					regexp=re.compile(r'.*')
					(r, status) = self.do_query(to_db, q,0,regexp)
					self._logger.info('### DONE Rebuilding index %s.' % idx)
		else:
			self._logger.info('### Passing, no unusable indexes for table %s.' % ( tab))
		
		
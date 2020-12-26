#!/usr/bin/python2.4
#
# Copyright 2012 .  All Rights Reserved.
# 
# Original author alex_buz@gmail.com  (Alex Buzunov)

"""This module contains all table partition routines
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from lib.common_utils import sql_utils

STACKTRACE_MAX_DEPTH = 2



class partition_utils(sql_utils):
	"""A class for table metadata."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes table patition utils.  See also app_utils.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def exchange_partitions(self, etl_object, logger):
		""" Does partition exchange for 2 tables in the same DB."""
		self.set_params(etl_object, logger)
		(r, status) = (None, 1)
		to_db = self.get_connector(self._p['TO_DB'])
		assert to_db, 'Cannot set TO_DB.'
		part_name = self._pp.get('PARTITION')
		assert part_name, 'Cannot set PARTITION.'
		from_tab = self._pp.get('FROM_TABLE')
		assert from_tab, 'Cannot set FROM_TABLE.'
		to_tab = self._pp.get('TO_TABLE')
		assert to_tab, 'Cannot set TO_TABLE.'
		assert from_tab!=to_table, 'TO_TABLE cannot be FROM_TABLE.'
		#def_conn=self.get_connector(self._p['FROM_DB'])
		status=0
		#pprint(template)
		if 1:
			#self._default_login=to_db #self.get_ora_login(def_conn)
			#assert len(self._default_login)>0, 'Cannot set default login.'
			from_db = self._pp['FROM_DB']
			workn =self._pp['WORKER_NAME'].strip()
			if 1:
				status=0
				logger.info('#### START part exch of %s[%s] part %s.' % (workn,to_tab,part_name))												
				(r, status) = self.do_query(to_db, t,0)
				logger.info('#### END part exch of %s[%s] part %s.' % (workn,to_tab,part_name))												

				if status==0:
					logger.info('#### SUCCESS Part exch of %s[%s] part %s.' % (workn,to_tab,part_name))	
			else:
				logger.warning('#### Skipping part exchange of %s[%s] part %s.' % (workn,to_tab,part_name))	
				
		else:
			logger.warning('#### Skipping part exchange of %s[%s] part %s.' % (workn,to_tab,part_name))	
							
		self.cleanup()
		(r, status)
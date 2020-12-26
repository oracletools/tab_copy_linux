#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all TABLE utils for Oracle db.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from subprocess import Popen, PIPE
from lib.common_utils import sql_utils
from lib.publish_utils import publish_utils
from lib.ddl_spool_utils import ddl_spool_utils
from lib.data_spool_utils import data_spool_utils
from lib.copy_utils import copy_utils
from lib.meta_utils import meta_utils
from lib.export_utils import export_utils



STACKTRACE_MAX_DEPTH = 2
	

class sqlp(sql_utils, publish_utils, ddl_spool_utils,data_spool_utils, copy_utils, meta_utils, export_utils):
	"""A class for table data copy."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the table_utils.  See also sql_utils.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		sql_utils.__init__(self, pipelinemeta, extract_logger, environment)
	def clone_table(self, etl_object, logger):
		print 'Cloning table..'
		self.spool_ddl(etl_object, logger)
		
		assert self._pp.get('TO_TABLE'), 'Temp table name for safe copy is not defined'
		
		self.publish_ddl(etl_object, logger)
		#pprint(self._pp)
	def safe_copy(self, etl_object, logger):
		print 'Starting safe copy...'
		#self.spool_ddl(etl_object, logger)
		assert self._pp.get('TO_TABLE')==self._pp.get('FROM_TABLE'), 'Target cannot be destination.'
		(out, status) = (None, None)
		if 0:
			tmp_tbl = self._pp.get('TO_TABLE')
			if tmp_tbl is None:
				tmp_tbl = "TEMP_LOAD_%s" % self._logger.timestamp_string
				self.set_p('TO_TABLE', tmp_tbl)
			
			self.clone_table(etl_object, logger)
		if 1:
			(out,status) = self.copy_table(etl_object, logger)
			#pprint(out)
			assert status==0, 'Load failed (%s).' % status
			self.exchange_partitions(etl_object, logger)
				
		pprint(self._pp)		






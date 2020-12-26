#!/usr/bin/python2.4

"""This module contains PL/SQL exception class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint

from lib.pl_sql_exception import PL_SQL_Exception

class PL_SQL_ExceptionBlock:
	"""A class for defining PL/SQL exception section."""
	def __init__(self,  stub,logger):
		"""PL/SQL exception"""
		self._type='EXCEPTION_SECTION'
		self._logger=logger
		self._stub=stub
		self._src=None
		if self._stub.has_key('block_exception'):
			self._src=self._stub['block_exception']
		self._el={} #exception list
	def parse_src(self):
		"""Parse: EXCEPTION section source"""
		if self._src:
			self._src="""EXCEPTION
WHEN NO_DATA_FOUND THEN
v_cob_flg := 0;
WHEN NO_DATA_FOUND1 THEN
v_cob_flg2 := 0;
			"""
			print self._src
			m = re.findall(r'WHEN(?P<ex_name>(?:(?!WHEN).)*)THEN(?P<ex_body>(?:(?!WHEN).)*)',self._src, re.S)
			#pprint(m)
			for _e in m:
				print _e
				self.parse_exception(_e)
			if len(m)>0:
				self._logger.debug('Got %d exceptions.' % len(m))
			else:
				self._logger.debug('Got 0 exceptions.')
			
		else:
			self._logger.debug('%s: Could not parse src for %s.' % (self.__class__.__name__, self._type))
			
	def parse_exception(self, stub):
		"""Parse: WHEN ... THEN exception"""
		en= stub[0].strip()
		if self._el.has_key(en):
			self._logger.error('Exception %s already processed.')
			sys.exit(1)
		else:
			ex= PL_SQL_Exception(stub,self._logger)
			ex.parse_src()
			self._el[en] =ex 	
		


		
			

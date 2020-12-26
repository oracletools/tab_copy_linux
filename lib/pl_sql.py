#!/usr/bin/python2.4
# 
# Original author alex_buz@gmail.com 

"""This module contains PL/SQL classes.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
#from lib.pl_sql_exception import PL_SQL_ExceptionBlock 
from lib.pl_sql_block import PL_SQL_Block

class PL_SQL_Procedure:
	"""A class for defining genericPL/SQL method."""

	def __init__(self, stub, logger):
		"""Generic PL/SQL method
		"""
		self._logger=logger
		self._declare={}	
		self._exception={}	
		self._stub=stub
		self._src=None
		if self._stub.has_key('body'):
			self._src=self._stub['body']
		#self.parse_src(self._src)
		self._type='PROCEDURE'
		self._params={}	
		self._block={} #block
	def add_param(self,dict):
		self._params[dict['name']] = dict
	def parse_params(self, input):
		i_params=input
		#print i_params
		
		m = re.findall(r'([\w\d]+\s+(IN|OUT|IN\s+OUT|NOCOPY)?\s+[\w\d]+\s?\,|[\w\d]+\s+(IN|OUT|IN\s+OUT|NOCOPY)?\s+[\w\d]+)',i_params)
		#parse: input param name and type
		#pprint(m)
		for _p in m:
			#print _p
			mp = re.match(r'(?P<name>[\w\d]+)\s+(?P<access>IN|OUT|IN\s+OUT|NOCOPY)?\s+(?P<type>[\w\d]+)\s?',_p[0])
			#pprint(m.groupdict())
			self.add_param(mp.groupdict())
		if len(m)>0:
			self._logger.debug('Got %d params.' % len(m))
		else:
			self._logger.debug('Got 0 params.')	
	def parse_declare(self,declare):
		#declare=s_body['declare']
		#print i_params
		#print declare
		m = re.findall(r'([\w\d]+\s+[\w\d]+\s?[\(\)\d\s]+\;|[\w\d]+\s+[\w\d]+[\(\)\d\s]+\:\=\s?[\w\d\s]+;)',declare)
		#parse: declare vars name, type and length
		#pprint(m)
		for _d in m:
			#print _d
			md = re.match(r'(?P<name>[\w\d]+)\s+(?P<type>[\w\d]+)\s?(?P<length>\(\d+\))?(?P<operation>\s+\:\=\s?)?(?P<assignment>[\w\d]+)?\s?\;',_d)
			#pprint(m.groupdict())
			#pprint( md.groupdict())
			self.add_declaration(md.groupdict())
		if len(m)>0:
			self._logger.debug('Got %d declarations.' % len(m))
		else:
			self._logger.debug('Got 0 declarations.')			
			
		
	def parse_src(self):
		self._logger.debug('Parsing %s source' % self._type)
		#parse: input, declaration, exception and block
		if self._src:
			body=self._src
			m = re.match(r'\s?(?P<input>\([\w\s\d\_\,\.]+\))?(?P<declare>\s?AS(?:(?!BEGIN).)*)BEGIN(?P<block>.*)(?P<exception>EXCEPTION.*\;\s?)',body,re.S)

			s_body=m.groupdict()
			#pprint(s_body)
			#sys.exit(1)
			if s_body.has_key('input'): 
				self.parse_params(s_body['input'])
			else:
				self._logger.debug('This src doesn''t have input section.')
			pprint(self._params)

			#parse: declared vars param name and type
			if s_body.has_key('declare'): 
				self.parse_declare(s_body['declare'])
			else:
				self._logger.debug('This src doesn''t have declare section.')
			#pprint(pl._declare)	

			#parse: block body and exceptions
			#pprint(s_body)
			if s_body.has_key('block'): 
				#block=s_body['block']
				self._block=PL_SQL_Block(s_body,self._logger)
				#print i_params
				self._block.parse_src()
				#print self._block
				#parse_block(s_body['block'],pl)
			else:
				self._logger.debug('This src doesn''t have block section.')
			#pprint(pl._declare)	
		else:
			self._logger.debug('Body src is not defined for this %s.' % self._type)
			
	def add_declaration(self,dict):
		self._declare[dict['name']] = dict	
	def add_exception(self,dict):
		self._exception[dict['type']] = dict
		
	def confirm(self,test, testname = "Test"):
		if not test:
			msg=  "Failed: " + testname
			if self._logger:
				self._logger.error('%s (%s)' % (msg, test) )
			else:
				self._logger.error('%s (%s)' % (msg, test) )
			sys.exit(1)

		

class PL_SQL_OuterBlock(PL_SQL_Block):
	"""A class for defining PL/SQL block."""
	def __init__(self,  *args, **kwargs):
		"""PL/SQL Outer block
		"""
		PL_SQL_Block.__init__(self, *args, **kwargs)
		self._type='OUTERBLOCK'
		self._src={}
		
		


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
import lib.config as config
from lib.config import confirm

class PL_SQL_Procedure(PL_SQL_Block):
	"""A class for defining genericPL/SQL method."""

	def __init__(self, stub, logger):
		"""Generic PL/SQL method
		"""
		PL_SQL_Block.__init__(self, stub, logger)

		self._name=self._stub['method_name']
		self._method_block=None
		if self._stub.has_key('method_block'):
			self._method_block=self._stub['method_block']
		self._type='PROCEDURE'
		confirm (self._type == self._stub['method_type'], 'It''s not a procedure.')
		self._params={}	
		self._block_obj={} #block
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
	def src2stub_ex(self, method_block):
		stub = None
		m = re.match(r'\s?(?P<input>\([\w\s\d\_\,\.]+\))?(?P<declare>\s?AS(?:(?!BEGIN).)*)BEGIN(?P<block_body>.*)(?P<exception>EXCEPTION.*\;\s?)',method_block,re.S)
		if m:
			stub=m.groupdict() #[block_body,declare,exception,input]
		
		pprint (stub)
		sys.exit(1)
		return (method_block, stub)

	def src2stub(self, method_block):
		stub = None
		m = re.match(r'\s?(?P<input>\([\w\s\d\_\,\.]+\))?(?P<declare>\s?AS(?:(?!BEGIN).)*)BEGIN(?P<named_block>.*END\s?[\w\d]?\;\s?)',method_block,re.S)
		if m:
			stub=m.groupdict() #[block_body,declare,exception,input]
		
		#pprint (stub)
		#sys.exit(1)
		return (method_block, stub)
		
	def parse_src(self, depth=0):
		self._logger.debug('Parsing %s source' % self._type)
		self._depth=depth
		#parse: input, declaration, exception and block
		if self._method_block:
			method_block,mb_stub = self.src2stub(self._method_block)
			pprint(mb_stub)
			
			if 'input' in mb_stub: 
				self.parse_params(mb_stub['input'])
			else:
				self._logger.debug('This procedure src doesn''t have input section.')
			pprint(self._params)
			
			#parse: declared vars param name and type
			if 'declare' in mb_stub: 
				self.parse_declare(mb_stub['declare'])
			else:
				self._logger.debug('This procedure src doesn''t have declare section.')
			pprint(self._declare)	
			
			if 'named_block' in mb_stub: 
				mb_stub['exception']='' #dummy
				self._block_obj = PL_SQL_Block(mb_stub,self._logger)
				
				self._block_obj.parse_src(self._depth)
			else:
				self._logger.debug('This procedure src doesn''t have block_body section.')
			
			#sys.exit(1)
			if 'exception' in mb_stub and 0: 
				self._exc_obj = PL_SQL_ExceptionBlock(mb_stub, self._logger)
				self._exc_obj.parse_src()
			else:
				self._logger.debug('This procedure doesn''t have exception section.')			
		else:
			self._logger.debug('Body src is not defined for this %s.' % self._type)

	def export_src(self,args):
		(lang)=(args['lang'])
		print args
		if lang.upper()  == 'PLSQL':
			return self.spool_src()	
		#if lang.upper() == 'NZPLSQL':
		#	nzp= NZ_PL_SQL_Procedure(self,self._logger)
		#	return nzp.spool_src()
		#	#return self.spool_src()	

	def spool_src(self,timestamp=None):
		print conf.spool_dir
		outfn= "%s/%s_%s.plsql" % (conf.spool_dir,self._name, conf.timestamp)
		if timestamp:
			outfn= "%s/%s_%s.plsql" % (conf.spool_dir,self._name, timestamp)
		
		return (0, outfn)

		

		
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

		

		


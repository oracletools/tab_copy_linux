#!/usr/bin/python2.4

"""This module contains PL/SQL exception class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
import lib.config as conf
#from lib.pl_sql_exception_block import PL_SQL_ExceptionBlock 
from pl_sql_anon_block import PL_SQL_AnonBlock
from lib.config import confirm
from pl_sql_statement import PL_SQL_IF_Statement


class PL_SQL_Block(PL_SQL_AnonBlock):
	"""A class for defining PL/SQL block."""
	def __init__(self,  stub,logger):
		"""Generic PL/SQL block
		"""
		PL_SQL_AnonBlock.__init__(self, stub,logger)
		self._type='NAMED_BLOCK'
		self._block=None
		self._block_body=None
		self._declare={}	
		self._exception=None # 0- src, 1- obj
		self._exc_obj=None
		self._exc_src=None
		#self._logger=logger
		self._block_stub=None
		self._unnested_block=None
		if self._stub.has_key('named_block'):
			self._src=self._stub['named_block']
		#self.__nb=[] #nested block objects
		#self._obj={} #nested blocks
		#self._map={} #parsed objects' map
	
		self._preblock=None
		self._postblock=None
		self._eq ={} #execution queue
		self._seg=None

	def add_map(self, args):
		(map_id, obj) = args
		confirm(map_id not in self._map, 'Object %s has already mapped.')
		self._map[map_id]=obj
	def get_block_stub(self, src):
		stub = None
		status=False
		m = re.match(r'(?P<nested_block_body>(?:(?!EXCEPTION).)*)(?P<exception>EXCEPTION.*\;\s?)',src,re.S)
		if m:
			stub=m.groupdict() #[block_body,declare,exception,input]
		#
		#pprint (stub)
		#sys.exit(1)
		if stub['exception']:
			status=True
		return (status, stub)		
	def unnest_block(self, block, depth=0):
		ln=0
		#depth= self._depth
		m = re.findall(r'(BEGIN(?:(?!BEGIN|END\;).)*END\;)',block, re.S)
		if m:
			ln=len(m)
			if ln>0:
				self._logger.debug('Got %d nested blocks.' % len(m))
				if depth not in self._obj.keys():
					self._obj[depth] = {}
				bid=0
				for nb in m:					
					if nb in block:
						pos = block.find(nb)
						self._logger.debug('Confirmed nested block at position %d.' % pos )
						#marker = 'NESTED_BLOCK[%d:%d]' % (depth,bid)
						map_id = self.get_map_id('NESTED_BLOCK',depth,bid)
						print map_id
						block = block[:pos] + map_id + block[(pos+len(nb)):]
						(status, nb_stub) = self.get_block_stub(nb)
						pprint(nb_stub)
						#sys.exit(1)
						#nbo=PL_SQL_AnonBlock({'nested_block':nb,'block':block},self._logger)
						nbo=PL_SQL_AnonBlock(nb_stub,self._logger)
						nbo.parse_src(depth+1)
						self._obj[depth][map_id]=(pos,nb,nbo)
						self.add_map((map_id,nbo))
						bid +=1
					else:
						self._logger.debug('Cannot find match nested block %s found in %s.' % (nb,self._type))
						sys.exit(1)
				#print block
		else:
			self._logger.debug('No nested blocks found for depth %d.' % depth)
		return (ln,block)		
	def parse_declare(self,declare):
		m = re.findall(r'([\w\d]+\s+[\w\d]+\s?[\(\)\d\s]+\;|[\w\d]+\s+[\w\d]+[\(\)\d\s]+\:\=\s?[\w\d\s]+;)',declare)
		for _d in m:
			md = re.match(r'(?P<name>[\w\d]+)\s+(?P<type>[\w\d]+)\s?(?P<length>\(\d+\))?(?P<operation>\s+\:\=\s?)?(?P<assignment>[\w\d]+)?\s?\;',_d)
			self.add_declaration(md.groupdict())
		if len(m)>0:
			self._logger.debug('Got %d declarations.' % len(m))
		else:
			self._logger.debug('Got 0 declarations.')	
	def unnest_blocks(self,src):
		self._logger.debug('Unnesting blocks in %s.' % self._type)
		confirm(src, 'Src is not set.')
		block=self._src		
		#check for sub-blocks
		bid=0
		cnt=0
		depth=self._depth
		(cnt,block) = self.unnest_block(block,depth)
		pprint(self._obj)
		#sys.exit(1)
		while cnt:
			bid +=1
			#print block
			(cnt,block) = self.unnest_block(block,depth+bid)
			
		self._logger.debug('Done un-nesting.')
		#pprint(self._obj)
		#print(block)
		#sys.exit(1)

		return (cnt, block)
		
	def parse_src(self, depth=0):
		self._logger.debug('Parsing src of %s.' % self._type)
		self._depth=depth
		if self._src:
			(cnt,map) = self.unnest_blocks(self._src)
			self._unnested_block=map

			(cnt, map) = self.unnest_ifs( map)
			self._map_src = map
		else:
			self._logger.debug('%s source is not set.' % self._type)	
		self._exception= self.parse_exception(self._stub)
		print self._map_src
		#sys.exit(1)






		

				
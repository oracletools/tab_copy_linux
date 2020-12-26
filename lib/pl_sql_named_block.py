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


class PL_SQL_NamedBlock(PL_SQL_AnonBlock):
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
		self.__nb=[] #nested block objects
		self._obj={} #nested blocks
		self._map={} #parsed objects' map
		self._map_src = None
		self._preblock=None
		self._postblock=None
		self._eq ={} #execution queue
		self._seg=None
			
	def parse_exception(self, stub):
		exc_src = exc_obj= None
		if 'exception' in stub: 			
			exc_src=stub['exception'];
			#print self._exception
			exc_obj = PL_SQL_ExceptionBlock(stub, self._logger)
			exc_obj.parse_src()
		else:
			self._logger.debug('Exception is not defined for this %s.' % self._type)
		return (exc_src, exc_obj)
	def block2stub (self, block_src):
		stub = None
		m = re.match(r'(?P<anonymous_block>(?:(?!EXCEPTION).)*)(?P<exception_block>EXCEPTION(?:(?!EXCEPTION).)*)?',block_src, re.S)
		if m:
			stub=m.groupdict()
			#pprint(stub)
			#sys.exit(1)
		return (block_src, stub)
	
	def parse_block(self, block):
		"""parse basic PL/SQL block"""
		self._logger.debug('Parsing basic block of %s.' % self._type)
		print block	
		self._block=block
		#parse: exception
		block2stub()
		if len(s_bblock):
			self.parse_block_body(s_bblock['block_body'])
			self._exception = self.parse_exception(s_bblock['exception']) # 0-src 1-obj
		else:
			self._logger.debug('Could not parse basic block of %s.' % self._type)
	def add_map(self, args):
		(map_id, obj) = args
		confirm(map_id not in self._map, 'Object %s has already mapped.')
		self._map[map_id]=obj
	def unnest_block(self, block, depth=0):
		ln=0
		
		m = re.findall(r'(BEGIN(?:(?!BEGIN).)*END\;)',block, re.S)
		if m:
			ln=len(m)
			if ln>0:
				self._logger.debug('Got %d nested blocks.' % len(m))
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
						nbo=PL_SQL_AnonBlock({'nested_block':nb,'block':block},self._logger)
						nbo.parse_src()
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
		if src:
			block=self._src		
			#check for sub-blocks
			depth=cnt=0
			(cnt,block) = self.unnest_block(block,depth)
			pprint(self._obj)
			#sys.exit(1)
			while cnt:
				depth +=1
				#print block
				(cnt,block) = self.unnest_block(block,depth)
			self._logger.debug('Done un-nesting.')
		return (cnt, block)
	def parse_src(self):
		self._logger.debug('Parsing src of %s.' % self._type)
		if self._src:
			(cnt,map) = self.unnest_blocks(self._src)
			self._unnested_block=map
			#(block_src, self._block_stub) = self.block2stub(block)
			#print(self._block_stub)
			#sys.exit(1)
			#sb=PL_SQL_AnonBlock(self._block_stub, self._logger)
			#sb.parse_src()
			#self._anon_block_obj=sb
			(cnt, map) = self.unnest_ifs( map)
			self._map_src = map
		else:
			self._logger.debug('%s source is not set.' % self._type)	
		self._exception= self.parse_exception(self._stub)
	def get_map_(self):
		return "--%s map\n\t%s" % (self._type, self._anon_block_obj.get_map())	
	def get_map(self):
		return "--%s map\n%s" % (self._type,self._map_src) 		
	def get_map2src(self):
		map2src={}
		for id in range(len(self._obj),0,-1):
			d= id-1
			t=self._obj[d]
			print 'block depth =', d
			for map_id, bt in t.iteritems():
				
				#confirm(bt[2]._type =='NESTED_BLOCK', 'Expected nested block, got %s instead.' % bt[2]._type)
				nbo=bt[2]
				map2src[map_id]= nbo.get_map()
		return map2src
	def get_src(self):
		self._logger.debug('Nesting for source output.')
		pprint(self._obj)
		#sys.exit(1)
		map = self.get_map()
		map2src = self.get_map2src()
		for map_id, block_src in map2src.iteritems():
			src= "--[[[ Start of %s \n\t%s\n\t--]]] End of %s" % (map_id, block_src,map_id)
			map = map.replace(map_id,src)
		print map
		sys.exit(1)
		return self.get_map()
	def get_map_id(self,type,depth,id):
		return "%s:%s[%s:%s]" % (self._type,type,depth,id)
	def unnest_ifs(self, block):
		self._logger.debug('Parsing src of %s.' % self._type)
		if block:
			#self._obj['IF']={}
			self._logger.debug('Parsing control statements in %s.' % self._type)
			#block=src		
			#check for IFs
			depth=0
			(cnt,block) = self.unnest_if_cs(block,depth)
			#pprint(self._obj)
			print cnt, block
			#sys.exit(1)
			while cnt:
				depth +=1
				#print block
				(cnt,block) = self.unnest_if_cs(block,depth)
			self._logger.debug('Done un-nesting IFs.')
			#self._anon_block_map=anon_block
		return (cnt,block)
			
	def unnest_if_cs(self, block, depth=0):
		ln=0
		
		m = re.findall(r'(IF(?:(?!IF|THEN|ELSE).)*THEN(?:(?!END IF|THEN).)*END IF\;)',block, re.S)
		if m:
			ln=len(m)
			pprint(m)
			#sys.exit(1)
			if ln>0:
				self._logger.debug('Got %d nested IF statements.' % len(m))
				self._obj[depth] = {}
				bid=0
				for nif in m:					
					print nif
					#if nif in block:
					confirm (nif in block,'Cannot find match nested IF found in %s.' % (self._type))
					pos = block.find(nif)
					self._logger.debug('Confirmed nested block at position %d.' % pos )
					map_id = self.get_map_id('I_F_CS',depth,bid) 
					print map_id
					block = block[:pos] + map_id + block[(pos+len(nif)):]
					ifcs= PL_SQL_IF_Statement({'if_statement':nif,'anonymous_block':block},self._logger)
					ifcs.parse_src()
					#sys.exit(1)
					self.add_map((map_id,ifcs))
					self._obj[depth][map_id]=(pos,nif,ifcs) #.append((pos,nif,ifcs))
					print self._obj
					bid +=1
					#else:
						#self._logger.debug('Cannot find match nested IF found in %s.' % (nif,self._type))
						#sys.exit(1)						
				#print block
				#sys.exit(1)
		else:
			self._logger.debug('No nested IFs found for depth %d.' % depth)
		return (ln,block)		

				
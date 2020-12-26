#!/usr/bin/python2.4

"""This module contains PL/SQL anonymous block class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm
from pl_sql_statement import PL_SQL_IF_Statement


class PL_SQL_AnonBlock:
	"""A class for defining PL/SQL anon block."""
	def __init__(self,  stub, logger):
		"""PL/SQL anon block
		"""
		self._type='ANONYMOUS_BLOCK'
		self._src=None
		self._stub=stub
		self._logger=logger
		pprint(stub)
		#sys.exit(1)
		if 'anonymous_block' in self._stub:
			self._src=self._stub['anonymous_block']
		else:
			if 'nested_block' in self._stub:
				self._src=self._stub['nested_block']
				self._nested=True
				self._type='NESTED_BLOCK'
			#self._statement_block = self._stub['statement_block']
		self._anon_block_map = None
		self._obj={} #control statements
		self._map={} #parsed objects' map
	def get_statement_type(self,stub):
		st=stub['statement'] 
		return "Statement: /* %s */" %st
	def get_map(self):
		return "--%s map\n%s" % (self._type,self._anon_block_map) 

	def parse_src(self):
		self._logger.debug('Parsing src of %s.' % self._type)
		if self._src:
			#self._obj['IF']={}
			self._logger.debug('Parsing control statements in %s.' % self._type)
			anon_block=self._src		
			#check for IFs
			depth=0
			(cnt,anon_block) = self.unnest_if_cs(anon_block,depth)
			pprint(self._obj)
			print cnt, anon_block
			#sys.exit(1)
			while cnt:
				depth +=1
				#print block
				(cnt,anon_block) = self.unnest_if_cs(anon_block,depth)
			self._logger.debug('Done un-nesting IFs.')
			self._anon_block_map=anon_block
			#print cnt, statement_block
			#pprint(self._obj)
			#sys.exit(1)
			#sb=PL_SQL_StatementBlock({'block_body':self._block }, self._logger)
			#sb.parse_src()
			
		else:
			self._logger.debug('%s source is not set.' % self._type)
	def get_map_id(self,type,depth,id):
		return "%s:%s[%s:%s]" % (self._type,type,depth,id)		
	def add_map(self, args):
		(map_id, obj) = args
		confirm(map_id not in self._map, 'Object %s has already mapped.')
		self._map[map_id]=obj		
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
		


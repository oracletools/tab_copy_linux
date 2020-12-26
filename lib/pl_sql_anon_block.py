#!/usr/bin/python2.4

"""This module contains PL/SQL anonymous block class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm
from pl_sql_statement import PL_SQL_IF_Statement, PL_SQL_ControlStatement
from pl_sql_exception import PL_SQL_Exception

class PL_SQL_AnonBlock(PL_SQL_ControlStatement):
	"""A class for defining PL/SQL anon block."""
	def __init__(self,  stub, logger):
		"""PL/SQL anon block
		"""
		PL_SQL_ControlStatement.__init__(self, stub,logger)
		self._type='ANONYMOUS_BLOCK'
		self._src=None
		self._nested = False
		self._stub=stub
		self._logger=logger
		self._super=PL_SQL_ControlStatement
		pprint(stub)
		#sys.exit(1)
		if 'anonymous_block_body' in self._stub:
			self._src=self._stub['anonymous_block_body']
		else:
			if 'nested_block_body' in self._stub:
				self._src=self._stub['nested_block_body']
				self._nested=True
				self._type='NESTED_BLOCK'
			#self._statement_block = self._stub['statement_block']
		self._anon_block_map = None
		self._obj={} #control statements
		self._map={} #parsed objects' map
		self._map_src = None
		self._mvar={} #maintenance variable
		self._maint_var=''
		self._exc_map_src=None
		self._exc_obj=None
		self._exc_src=None
		self._has_exception=False
		if self._stub['exception']:
			self._has_exception=True
		self._exc_stub={}
		self._depth=None
	def get_statement_type(self,stub):
		st=stub['statement'] 
		return "Statement: /* %s */" %st

	def get_src(self):
		self._logger.debug('%s source.' %self._type)
		decl=exc=''
		if self._nested:

			self.add_mvar(('v_rc','NUMERIC',8, '-1', 'DML row count'))
			decl = 'DECLARE\n\t/*Exception constants*/\n\t%s\n\t/*Variables*/\n\t%s\n\t' % (self.get_ex_constants(), self.get_mvars())
		if self._has_exception:
			exc=self._exc_obj.get_src()
		return '%s%s%s' % (decl, self._super.get_src(self),exc )
		
	def parse_src(self, depth):
		self._logger.debug('Parsing src of %s.' % self._type)
		self._depth=depth
		if self._src:
			#(cnt,map) = self.unnest_blocks(self._src)
			#self._unnested_block=map
			#map=self._src
			(cnt, self._map_src) = self.unnest_ifs( self._src)
			#print map
			#sys.exit(1)
			#self._map_src = map
			(cnt, self._map_src)=self.parse_delete_dml(self._src, self._depth)
			#print self._map_src
			(cnt, self._map_src)=self.parse_select(self._src, self._depth)
			print self._map_src
			#(self._has_exception,self._exc_stub)=self.get_exception_src(self._src)
			if self._has_exception:
				print self._has_exception
				(self._exc_map_src, self._exc_obj)= self.parse_exception(self._stub)
			#pprint(self._exc_map_src)
		else:
			self._logger.debug('%s source is not set.' % self._type)	

		#sys.exit(1)
	def parse_exception(self, stub):
		exc_map = None
		exc_obj= None
		if 'exception' in stub: 			
			
			#print self._exception
			exc_obj = PL_SQL_Exception(stub, self._logger)
			print exc_obj
			(cnt,exc_map) = exc_obj.parse_src(self._depth+1)
		else:
			self._logger.debug('Exception is not defined for this %s.' % self._type)
		return (exc_map, exc_obj)		
	def get_ex_constants(self):
		if not self._constant:
			self._constant=''
			if self._has_exception:
				print self._exc_obj._obj
				for ex_name in self._exc_obj._el:
					#ex_name=
					#print ex_name
					self.add_const((ex_name,'VARCHAR',32, "'%s'" % ex_name,'Exception'))
				#sys.exit(1)
			
			for pid in self._const:
				decl= "%s(%s):=%s;  /*%s*/"  % self._const[pid]
				self._constant = '%s\n\t%s %s' % (self._constant, pid, decl)
		return self._constant
	def get_mvars(self):
		if not self._maint_var:
			self._constant=''
			for pid in self._mvar:
				decl= "%s(%s):=%s;  /*%s*/"  % self._mvar[pid]
				self._maint_var = '%s\n\t%s %s' % (self._maint_var, pid, decl)
		return self._maint_var		
	def add_const(self, decl):
		(name, type, size, val, cmnts) = decl
		if not name in self._const:
			#confirm(name not in self._const, 'Constant %s already defined.' % name)
			self._const[name]=(type, size, val,cmnts)		
	def add_mvar(self, decl):
		"""add maintenance variable"""
		(name, type, size, val, cmnts) = decl
		confirm(name not in self._const, 'Mvariable %s already defined.' % name)
		self._mvar[name]=(type, size, val, cmnts)	
	
	def add_map(self, args):
		(map_id, obj) = args
		confirm(map_id not in self._map, 'Object %s has already mapped.')
		self._map[map_id]=obj	
		
	def unnest_ifs(self, block):
		self._logger.debug('Parsing src of %s.' % self._type)
		depth=self._depth
		bid=0
		if block:
			#self._obj['IF']={}
			self._logger.debug('Parsing control statements in %s.' % self._type)
			#block=src		
			#check for IFs
			#depth=0
			(cnt,block) = self.unnest_if_cs(block,depth+bid)
			#pprint(self._obj)
			#print cnt, block
			#sys.exit(1)
			while cnt:
				bid +=1
				#print block
				(cnt,block) = self.unnest_if_cs(block,depth+bid)
			self._logger.debug('Done un-nesting IFs.')
			#self._anon_block_map=anon_block
		return (cnt,block)
			
	def unnest_if_cs(self, block, depth):
		ln=0
		
		m = re.findall(r'(IF(?:(?!IF|THEN|ELSE).)*THEN(?:(?!END IF|THEN).)*END IF\;)',block, re.S)
		if m:
			ln=len(m)
			pprint(m)
			#sys.exit(1)
			if ln>0:
				self._logger.debug('Got %d nested IF statements.' % len(m))
				if depth not in self._obj.keys():
					self._obj[depth] = {}
				bid=0
				for nif in m:					
					print nif
					#if nif in block:
					confirm (nif in block,'Cannot find match nested IF found in %s.' % (self._type))
					pos = block.find(nif)
					self._logger.debug('Confirmed nested IF at position %d.' % pos )
					map_id = self.get_map_id('I_F_CS',depth,bid) 
					print map_id
					block = block[:pos] + map_id + block[(pos+len(nif)):]
					ifcs= PL_SQL_IF_Statement({'if_statement':nif,'anonymous_block':block},self._logger)
					ifcs.parse_src(self._obj, depth+1)
					#sys.exit(1)
					self.add_map((map_id,ifcs))
					self._obj[depth][map_id]=(pos,nif,ifcs) #.append((pos,nif,ifcs))
					#print self._obj
					bid +=1
					#else:
						#self._logger.debug('Cannot find match nested IF found in %s.' % (nif,self._type))
						#sys.exit(1)						
				#print block
				#sys.exit(1)
		else:
			self._logger.debug('No nested IFs found for depth %d.' % depth)
		return (ln,block)
		


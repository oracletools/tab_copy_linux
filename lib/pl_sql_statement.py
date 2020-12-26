#!/usr/bin/python2.4

"""This module contains PL/SQL exception class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm
from sql_statement import SQL_Delete_Statement, SQL_Select_Statement

from statement import PL_SQL_Statement

class PL_SQL_ControlStatement(PL_SQL_Statement):
	"""A class for defining PL/SQL statement."""
	def __init__(self,  *args, **kwargs):
		"""PL/SQL statement"""
		PL_SQL_Statement.__init__(self, *args, **kwargs)
		self._type='CONTROL_STATEMENT'
		self._src=None
		self._const={}
		self._constant=''
	def parse_delete_dml(self, map, depth):
		ln=0		
		#DELETE FROM CSMARTBSER.FAILS_REPORTS WHERE cob_date = v_cob_dt AND sourcesystem =v_sourcesystem;
		m = re.findall(r'(DELETE FROM(?:(?!DELETE FROM|WHERE).)*(WHERE(?:(?!WHERE|DELETE FROM|COMMIT|ROLLBACK).)*)?\;)\s+(COMMIT\;|ROLLBACK\;)?',map, re.S)
		#sys.exit(1) 
		if m:
			ln=len(m)
			pprint(m)
			#sys.exit(1)
			if ln>0:
				self._logger.debug('Got %d %s.' % (len(m), self._type))
				if depth not in self._obj.keys():
					self._obj[depth] = {}
				bid=0
				for dml in m:					
					print dml
					(delete,where,trans)=dml
					if trans:
						print delete,where,trans
					#if nif in block:
					#sys.exit(1)
					confirm (delete in map,'Cannot find %s in map.' % (self._type))
					pos = map.find(delete)
					self._logger.debug('Confirmed DELETE at position %d.' % pos )
					map_id = self.get_map_id('DML_DEL',depth,bid) 
					print map_id
					map = map[:pos] + map_id + map[(pos+len(delete)):]
					ifcs= SQL_Delete_Statement({'delete_statement':delete,'where': where, 'transaction':trans,'control_statement':map},self._logger)
					ifcs.parse_src()
					#sys.exit(1)
					#self.add_map((map_id,ifcs))
					self._obj[depth][map_id]=(pos,delete,ifcs) #.append((pos,nif,ifcs))
					#print self._obj
					bid +=1
		else:
			self._logger.debug('No DELETEs found for depth %d.' % depth)
		pprint(self._obj)
		return (ln,map)	
	def parse_select(self, map, depth):
		ln=0		
		#DELETE FROM CSMARTBSER.FAILS_REPORTS WHERE cob_date = v_cob_dt AND sourcesystem =v_sourcesystem;
		m = re.findall(r'(SELECT(?P<select>(?:(?!SELECT|INTO).)*)(?P<into>INTO[\w\_\d\s]+)?FROM\s+(?P<from_>(?:(?!FROM|WHERE).)*)(?P<where>(?:(?!\;).)*)\;)',map, re.S)
		#sys.exit(1) 
		if m:
			ln=len(m)
			pprint(m)
			#sys.exit(1)
			if ln>0:
				self._logger.debug('Got %d %s.' % (len(m), self._type))
				if depth not in self._obj.keys():
					self._obj[depth] = {}
				bid=0
				for dml in m:					
					#print dml
					(select, columns, into, from_, where)=dml
					#if into:
					#	print select ,into,from_,where
					#if nif in block:
					#sys.exit(1)
					confirm (select in map,'Cannot find %s in map.' % (self._type))
					pos = map.find(select)
					self._logger.debug('Confirmed %s at position %d.' % (self._type, pos ))
					map_id = self.get_map_id('SEL_STM',depth,bid) 
					print map_id
					map = map[:pos] + map_id + map[(pos+len(select)):]
					selst= SQL_Select_Statement({'select_statement':select,'where': where, 'into':into,'from':from_,'control_statement':map},self._logger)
					selst.parse_src()
					self._obj[depth][map_id]=(pos,select,selst) 
					bid +=1
		else:
			self._logger.debug('No DELETEs found for depth %d.' % depth)
		#pprint(self._obj)
		return (ln,map)

class PL_SQL_IF_Statement(PL_SQL_ControlStatement):
	"""A class for defining PL/SQL statement."""
	def __init__(self,  stub, logger):
		"""PL/SQL statement"""
		PL_SQL_ControlStatement.__init__(self, stub, logger)
		self._type='IF_STATEMENT'
		self._src=None
		self._obj={}
		self._depth=None
		#self._stub=stub
		#self._logger=logger
		if self._stub.has_key('if_statement'):
			self._src=self._stub['if_statement']			
		self._s={} #statements
		self._map_src=None
	def parse_src(self, gobj, depth):
		"""parse: control statement"""
		self._logger.debug('Parsing %s.' % self._type)
		self._gobj = gobj
		self._depth = depth
		
		#print "IF Statement: /* %s */" % self._src	
		(cnt, self._map_src)=self.parse_delete_dml(self._src, self._depth)
		print self._map_src
		#sys.exit(1)
	
		


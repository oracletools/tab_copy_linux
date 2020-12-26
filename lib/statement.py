#!/usr/bin/python2.4

"""This module contains Statement class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm

class Statement:
	"""A class for defining statement."""
	def __init__(self,  stub, logger):
		"""SQL statement"""
		self._type='STATEMENT'
		self._src=None
		self._map_src=None
		self._stub=stub
		self._gobj={}
		self._obj={}
		self._depth=0
		self._logger=logger
		self._depth=None
		self._map_id=None
		self._has_exception=False
		
	def parse_src(self):
		"""parse: statement"""
		self._logger.debug('Parsing %s.' % self._type)
		print "Statement: /* %s */" % self._src
	def get_map(self):
		return self._map_src 

	def get_map_id(self,type,depth,id):
		#if not self._map_id:
		map_id="%s[%s:%s]" % (type,depth,id)
		return map_id
	def translate_control(self, map):
		#cannot rollback in NZ exception section
		map = re.sub('(ROLLBACK\s?\;|COMMIT\s?\;)','/*\\1*/',map)
		
		return map		
	def get_src(self):
		self._logger.debug('%s source1.' %self._type)
		if 'COMMIT' in self._map_src:
			print self._map_src
			sys.exit(1)
		out_src=self._map_src
		print self._type
		if self._obj:
			depth=max(self._obj)+1
			#pprint (self._obj)
			#sys.exit(1)
			print min(self._obj)
			for id in range(depth,0,-1):
				d= id-1
				print d
				if d in self._obj:
					
					t=self._obj[d]
					print 'block depth =', d
					for map_id, bt in t.iteritems():
						print depth,id, map_id
						if map_id in out_src:
							print 'Found %s in map_src' %map_id
							obj=self.get_obj(bt)

							obj_src= obj.get_src()
							ex_trigger=''
							if self._has_exception:
								ex_trigger=self.get_exc_trigger(obj)
							out_src= out_src.replace(map_id,"%s /*<-%s*/%s" % ( obj_src,map_id,ex_trigger))
							
				else:
					self._logger.debug('Depth %s is not set.' % d)
		else:
			self._logger.debug('Object map is empty for %s.' % self._type)

		return translate_control(out_src)
	def get_exc_trigger(self, obj):
		out_src=''
		print obj._type
		if self._has_exception:
			for (exn, eobj) in self._exc_obj._el.items():
				rewrite= eobj.get_trigger(obj._type)
				if rewrite:
					out_src='%s\n\t%s' % (out_src, rewrite)

		return out_src
	def tab(self, depth):
		return '\t'*depth
	def get_obj_map(self, bt):
		return bt[1]
	def get_obj(self,bt):
		return bt[2]
	def get_obj_loc(self, bt):
		return bt[0]		
class PL_SQL_Statement(Statement):
	"""A class for defining PL/SQL statement."""
	def __init__(self,  stub, logger):
		"""PL/SQL statement"""
		Statement.__init__(self, stub, logger)
		self._type='PL_SQL_STATEMENT'
		self._src=None
		self._stub=stub
		self._logger=logger		

class SQL_Statement(Statement):
	"""A class for defining PL/SQL statement."""
	def __init__(self,  stub, logger):
		"""SQL statement"""
		Statement.__init__(self, stub,logger)
		self._type='SQL_STATEMENT'
		self._src=None
		self._map_src=None
		self._stub=stub
		self._logger=logger
		
		
class SQL_DML_Statement(SQL_Statement):
	"""A class for defining DML statement."""
	def __init__(self,  stub, logger):
		"""SQL DML statement"""
		SQL_Statement.__init__(self, stub,logger)
		self._type='DML_STATEMENT'
		self._src=None
		self._stub=stub
		self._logger=logger
		
class SQL_DDL_Statement:
	"""A class for defining DDL statement."""
	def __init__(self,  stub, logger):
		"""SQL DDL statement"""
		SQL_Statement.__init__(self, stub,logger)
		self._type='DDL_STATEMENT'
		self._src=None
		self._stub=stub
		self._logger=logger	
#!/usr/bin/python2.4

"""This module contains SQL DML/DDL statements class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm
from statement import SQL_Statement, SQL_DML_Statement


class SQL_Delete_Statement(SQL_DML_Statement):
	"""A class for defining DML statement."""
	def __init__(self,  stub, logger):
		"""Delete statement"""
		SQL_DML_Statement.__init__(self, stub,logger)
		self._type='DELETE_STATEMENT'
		self._schema_name=None
		self._table_name=None
		self._where=None
		if 'delete_statement' in stub.keys():
			self._src=stub['delete_statement']
	def parse_src(self):
		"""parse: statement"""
		self._logger.debug('Parsing %s.' % self._type)
		#print self._src
		m = re.match(r'(DELETE FROM (?P<schema_name>[\w\_\d]+)?\.?(?P<table_name>[\w\_\d]+)(?P<where>(?:(?!\;).)*)\;)',self._src,re.S)
		if m:
			stub=m.groupdict()
			pprint(stub)
			self._schema_name = stub['schema_name']
			self._table_name = stub['table_name']
			self._where = stub['where']
			#print self._schema_name,self._table_name,self._where
		confirm(len(stub)>0, 'Cannot parse %s.' % self._type)		
		confirm(stub.has_key('table_name'),'Table name is undefined.')
		#sys.exit(1)
	def get_src(self):
		debug= "v_rc:=ROW_COUNT; RAISE NOTICE '% records deleted.',v_rc;"
		out = "DELETE FROM /*%s*/ %s %s;" % ( self._schema_name,self._table_name,self._where) 
		return '%s\n\t\t%s' % (out, debug)

class SQL_Select_Statement(SQL_Statement):
	"""A class for defining Select statement."""
	def __init__(self,  stub, logger):
		"""Select statement"""
		SQL_Statement.__init__(self, stub,logger)
		self._type='SELECT_STATEMENT'
		self._select=None
		self._schema_name=None
		self._table_name=None
		self._into=None
		self._where=None
		self._hint=None
		if 'select_statement' in stub.keys():
			self._src=stub['select_statement']
	def parse_src(self):
		"""parse: SQL statement"""
		self._logger.debug('Parsing %s.' % self._type)
		#print self._src
		
		#SELECT  /*+ FIRST_ROWS(1) */  1 INTO v_cob_flg FROM CSMARTBSER.FAILS_REPORTS_HISTORY
		#WHERE cob_date = v_cob_dt  AND sourcesystem =v_sourcesystem AND rownum < 2;
		
		m = re.match(r'(?P<query>SELECT\s+(?P<hint>\/\*\+.*\*\/)?(?P<select>(?:(?!SELECT|INTO|\/\*\+).)*)(?P<into>INTO[\w\_\d\s]+)?FROM\s+(?P<schema_name>[\w\_\d]+)?\.?(?P<table_name>[\w\_\d]+)(?P<where>(?:(?!\;).)*)\;)',self._src,re.S)
		if m:
			stub=m.groupdict()
			pprint(stub)
			self._select = stub['select']
			self._into = stub['into'].strip('INTO').strip()
			self._schema_name = stub['schema_name']
			self._table_name = stub['table_name']
			self._where = stub['where']
			self._hint = stub['hint']
			print self._schema_name,self._table_name,self._where
			self._map_src=stub['query']
		confirm(len(stub)>0, 'Cannot parse %s.' % self._type)		
		confirm(stub.has_key('into'),'Into is undefined.')
		confirm(stub.has_key('table_name'),'Table name is undefined.')
		#sys.exit(1)
	def get_limit_value(self,sign, value):
		if sign.strip()=='<':
			return '%d' % (int(value)-1)
		return value
	def fix_rownum(self, where):
		print where
		m = re.findall(r'((?P<rownum>AND\s+ROWNUM|ROWNUM)([ ><=]+)([\d]+))',where,re.S|re.I)
		cnt = 0
		if m:
			stub=m
			pprint(stub)
			(predicate,rownum, sign, value) = m[0]
			#print predicate,rownum, sign, value
			cnt +=1
			pos = where.find(predicate)
			newp = "LIMIT %s" % self.get_limit_value(sign, value)
			where = where[:pos] + newp + where[(pos+len(predicate)):]
		return (cnt, where)
		
	def get_src(self):
		out=None
		if self._where:
			(status, self._where) = self.fix_rownum(self._where)
			#sys.exit(1)
		debug= "v_rc:=ROW_COUNT; RAISE NOTICE '% records selected.',v_rc;"
		out= "SELECT %s INTO %s FROM /*%s*/ %s %s;" % ( self._select,  self._into,self._schema_name,self._table_name,self._where) 
		#print out
		#sys.exit(1)
		return '%s\n\t\t%s' % (out, debug)

		
	
		
		
		
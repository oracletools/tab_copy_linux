#!/usr/bin/python2.4

"""This module contains PL/SQL exception class.
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
from lib.config import confirm
from pl_sql_statement import  PL_SQL_ControlStatement
from statement import  Statement


		
class PL_SQL_Exception(Statement):
	"""A class for defining PL/SQL exception section."""
	def __init__(self,  stub,logger):
		"""PL/SQL exception"""
		Statement.__init__(self, stub, logger)
		self._type='EXCEPTION_SECTION'
		self._logger=logger
		self._stub=stub
		self._src=None
		if self._stub.has_key('exception'):
			self._src=self._stub['exception']
		self._el={} #exception list
		#self._ex_rewrite =('NO_DATA_FOUND')
	def parse_src(self, depth):
		"""Parse: EXCEPTION section source"""
		self._depth=depth
		out_map=self._src
		ln=None
		if out_map:
			#print self._src
			m = re.findall(r'(WHEN(?P<ex_name>(?:(?!WHEN).)*)THEN(?P<ex_body>(?:(?!WHEN|\s+END\;).)*))',out_map, re.S)
			ln=len(m)
			bid=0
			if depth not in self._obj.keys():
				self._obj[depth] = {}
			for (ex_case,ex_name,ex_body) in m:
				ex_name=ex_name.strip().upper()
				#print b
				#sys.exit(1)
				#ex=_e
				#en= _e[1].strip()
				if self._el.has_key(ex_name):
					self._logger.error('Exception %s already processed.' % ex_name)
					
				else:
					confirm (ex_case in out_map,'Cannot find exception %s in %s.' % (ex_name, self._type))
					pos = out_map.find(ex_case)
					self._logger.debug('Confirmed exception case %s at position %d.' % (ex_name,pos) )
					map_id = self.get_map_id('EXC_CS',depth,bid) 
					print map_id
					out_map = out_map[:pos] + map_id + out_map[(pos+len(ex_case)):]
					ex= PL_SQL_ExceptionCase({'exception_name':ex_name,'exception_body':ex_body},self._logger)
					ex.parse_src()
					self._el[ex_name] =ex 	
					self._obj[depth][map_id]=(pos,ex_case,ex) 
					bid +=1
			#sys.exit(1)
			if len(m)>0:
				self._logger.debug('Got %d exceptions.' % len(m))
			else:
				self._logger.debug('Got 0 exceptions.')
			
		else:
			self._logger.debug('%s: %s does not exists for block.' % (self.__class__.__name__, self._type))
		self._map_src=out_map
		return (ln,out_map)
		
	def get_src(self):
		self._map_src = self._map_src.strip('EXCEPTION').strip('END;').strip()
		#sys.exit(1)
		out_src="""
		EXCEPTION
		WHEN OTHERS THEN
		%s
	END;""" % Statement.get_src(self)
		
		return out_src
		
class PL_SQL_ExceptionCase(PL_SQL_ControlStatement):
	"""A class for defining PL/SQL exception case."""
	def __init__(self,  stub,logger):
		"""PL/SQL exception case"""
		PL_SQL_ControlStatement.__init__(self, stub,logger)
		self._type='EXCEPTION_CASE'
		#self._logger=logger
		#self._stub={}
		self._name=None
		self._others=False # if it's OTHERS exception
		#pprint(dir(self._stub))
		if 'exception_name' in stub:
			self._name = stub['exception_name'].strip()
			if self._name.upper() == 'OTHERS':
				self._others=True
		self._src=None
		if 'exception_body' in stub:
			self._src=stub['exception_body'].strip()
		self._converted=False # if converted to others
		
	def parse_src(self):
		"""Parse: WHEN ... THEN exception block"""
		self._logger.debug('Parsing %s.' % self._type)
		self._map_src=self._src
	def get_src(self):
		out_src = """
		IF %s=SQLERRM THEN
				RAISE NOTICE 'EXCEPTION:  %s, %%',v_rc;
				%s
		END IF;
		""" % (self._name,self._name,self._map_src)
		return out_src
	def get_trigger(self, obj_type):
		out_src=''
		
		if obj_type=='SELECT_STATEMENT' and self._name=='NO_DATA_FOUND':
			out_src="""
		/*Exception trigger*/
		IF v_rc=0 THEN
			RAISE EXCEPTION '%%', %s;
		END IF;""" % self._name
		return out_src

	
			
				
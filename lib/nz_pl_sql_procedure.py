#!/usr/bin/python2.4
# 

"""This module contains NZ PL/SQL classes.
"""

__author__ = 'Alex Buzunov'

import sys, os
import string
import re
from pprint import pprint
import lib.config as conf



class NZ_PL_SQL_Procedure:
	"""A class for defining generic NZ PL/SQL method."""

	def __init__(self, donor_obj, logger):
		"""Generic NZ PL/SQL method
		"""
		self._logger=logger
		#self._donor=from_obj
		self._exception={}	
		self._do=donor_obj
		self._src=None
		self._stub=None
		self._type='NZ PROCEDURE'
		self._params={}	
		self._block={} 
		self._name=None
		self._header=None
		self._footer=None
		self._esception=None
		self._body=None
		self._declare=None
		self._block=None
		self._lang='NZPLSQL'
		self._exec_as='OWNER'
		self._default_return='INTEGER'
		self._ext='nzsql'
		self._param=''
		self.__param=None
		self.__declare_var=None
		self._param_declare=''
		self.__const=self._do._const
		self._constant=''
		self._declare_var=''
		self._declare_init='/*Param-to-Var init*/'
		self.process_do()

	def	process_do(self):
		self._name=self._do._name
		self.set__param()
		self.set__declare_var()
	def set__param(self):
		if self._do:
			self.__param=self._do._params
			#pprint(self._do._params)
	def set__declare_var(self):
		if self._do:
			self.__declare_var=self._do._declare
			#pprint(self._do._declare)


		
	def set_declare_var(self):
		if not self._declare_var:
			self._declare_var=''
			#pprint(self.__declare_var)
			#pprint(self.__param)
			#sys.exit(1)
			for pid in self.__declare_var:
				#pprint (self.__declare_var[pid])
				dtype=self.fix_type(self.__declare_var[pid]['type'])
				dname= self.__declare_var[pid]['name']
				dlen = self.fix_length(self.__declare_var[pid]['length'])
				print dtype
				asgn =''
				if 'assignment' in self.__declare_var[pid]:
					if not self.__declare_var[pid]['assignment']:
						self.__declare_var[pid]['assignment']="''"
					asgn = ':=%s' % self.__declare_var[pid]['assignment']
					if self.__declare_var[pid]['assignment'] in self.__param: #bypass early init
						self._declare_init = '%s\n\t%s %s;' % (self._declare_init, dname,asgn)
						self._declare_var = '%s\n\t%s %s%s;' % (self._declare_var, dname, dtype,dlen)
					else:
						self._declare_var = '%s\n\t%s %s%s%s;' % (self._declare_var, dname, dtype,dlen,asgn)
				else:
					self._declare_var = '%s\n\t%s %s%s;' % (self._declare_var, dname, dtype,dlen)
				
			#self._declare_var = string.strip(self._declare_var, '; ')
	def get_declare_var(self):
		if not self._declare_var:
			if not self.__declare_var:
				self.set__declare_var()
			self.set_declare_var()
		return	self._declare_var
	def set_param(self):
		if not self._param:
			for pid in self.__param:
				ptype=self.fix_param_type(self.__param[pid]['type'])
				self._param = string.strip('%s, %s' % (self._param, ptype), ', ')			
	def get_param(self):
		if not self._param:
			if not self.__param:
				self.set__param()
			self.set_param()
		return self._param 
	def fix_length(self, in_len):
		if not in_len:
			return ''
		else:
			return in_len		
	def fix_type(self, in_type):
		if in_type.upper().strip() in 'VARCHAR2':
			return 'VARCHAR'
		if in_type.upper().strip() in 'NUMBER':
			return 'NUMERIC'			
		return in_type
	def fix_param_type(self, in_type):
		if in_type.upper() == 'VARCHAR2':
			return 'VARCHAR(ANY)'
		else:
			return in_type			
	def set_param_declare(self):
		if not self._param_declare:
			i=1
			self._param_declare=''
			for pid in self.__param:
				pname=self.__param[pid]['name']
				ptype=self.__param[pid]['type']
				paccess = self.__param[pid]['access']
				self._param_declare = '%s\n\t%s ALIAS FOR $%d; /*%s, %s*/' % (self._param_declare, pname, i, ptype ,paccess)		
				i +=1
			#self._param_declare = string.strip(self._param_declare, '; ')

	def get_param_declare(self):
		if not self._param_declare:
			if not self.__param:
				self.set__param()
			self.set_param_declare()
		return self._param_declare
		
	def get_src(self):	
		#out ="%s\n%s\n%s" % (self.get_header(),self.get_body(),self.get_footer())
		header= self.get_header()
		declare= self.get_declare()
		declare_init=self.get_declare_init() 
		exception = '' #self.get_exception()
		print exception
		#sys.exit(1)
		block_body = self.get_block_src()
		
		block="""BEGIN
	%s
	%s
%s
END;""" % (declare_init, block_body, exception)
		
		body="""%s\n%s""" % (declare, block)
		footer=self.get_footer()
		return "%s\n%s\n%s" % (header,body,footer)

	def spool_src(self, timestamp=None):
		print conf.spool_dir
		outfn= "%s/%s_%s.%s" % (conf.spool_dir,self._name, conf.timestamp,self._ext)
		if timestamp:
			outfn= "%s/%s_%s.%s" % (conf.spool_dir,self._name, timestamp,self._ext)
		f=open(outfn,'w')
		out=self.get_src()
		print(out)
		status=f.write(out)
		f.close()
		return (outfn, status)
	def get_header(self):
		if not self._header:
			self.set_header()
		return self._header 
	def get_constants(self):
		if not self._constant:
			self._constant=''
			#pprint(self.__declare_var)
			#pprint(self.__param)
			#sys.exit(1)
			
			for pid in self.__const:
				decl= "%s%s:=%s"  % self.__const[pid]
				self._constant = '%s\n\t%s %s;' % (self._constant, pid, decl)
		
		return self._constant
	def set_header(self):
		header="""CREATE OR REPLACE PROCEDURE "%s"(%s)
	RETURNS %s
	EXECUTE AS %s 
	LANGUAGE %s 
	AS
BEGIN_PROC""" % (self._name, self.get_param(), self._default_return, self._exec_as, self._lang)
		self._header=header
		
	def get_declare(self):
		if not self._declare:
			declare="""DECLARE\n\t/*Parameters*/%s\n\t/*Constants*/\n\t%s\n\t/*Declarations*/%s""" % (self.get_param_declare(), self.get_constants(), self.get_declare_var())
			self._declare=declare
		return self._declare	
		
	def get_declare_init(self):
		return self._declare_init
		
	def get_block(self):
		out="""BEGIN
	%s
%s
END;""" % (self.get_block_src(), self.get_exception())
		return out
	def get_block_src(self):
		self._logger.debug('Nesting for source output.')
		if self._do._block:
			self._logger.debug('Found donor object %s, type %s.' % (self._do._block.__class__.__name__,self._do._block._type)) 
		#_statement_block
		
		block_map= "/*%s\n\t*/" % self.get_block_map()
		block_src=self._do._block_obj.get_src()
		return  block_src

	def get_block_map(self):
		self._logger.debug('Nesting for source output.')
		if self._do._block:
			self._logger.debug('Found donor object %s, type %s.' % (self._do._block.__class__.__name__,self._do._block._type)) 
		#_statement_block
		return "--%s map\n\t%s" % (self._type, self._do._block_obj.get_map())		 


	def get_exception(self):
		
		#sys.exit(1)
		exception=self._do._block_obj._block_stub['exception_block']
		print(exception)
		#self._exception=exception
		return exception
	def get_footer(self):
		if not self._footer:			
			footer="END_PROC; /*%s*/" % self._name
			self._footer=footer
		return self._footer 




		


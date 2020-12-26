#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all data load routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from subprocess import Popen, PIPE
from app_utils import app_utils

STACKTRACE_MAX_DEPTH = 2



class publish_utils(app_utils):
	"""A class for data load (publishing)."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def publish_ddl(self, etl_object, logger):
		"""Executing DDL publisher"""
		self.set_params(etl_object, logger)
		assert len(self._gwc['DDL_LOC'])>0, 'There''s nothing to publish';
		
		for dfn in self._gwc['DDL_LOC']:
			logger.info('#### START of publish for %s.' % dfn)
			#print dfn
			assert os.path.exists(dfn),"File does not exsits."
			assert os.access(dfn, os.R_OK), "Cannot read file."
			f=open(dfn,"r")
			tmpl=f.read()
			f.close()
			#remove ALTER INDEX UNUSABLE
 			rx= re.compile( r'(ALTER\sINDEX\s[\w\d\.\"\_]+\s+UNUSABLE)')		
			atmpl = rx.sub( ' ', tmpl)
			if atmpl==tmpl:
				logger.info('There''s no ALTER statement.')
			#remove ALTER INDEX UNUSABLE
			if self.p_if('IF_CLONE_UNCOMPRESSED'):
				atmpl = atmpl.replace(' COMPRESS ', ' ')
			
			#fix PK name	
			atmpl = re.sub( r'CONSTRAINT \"([\w\d\_\.]+)\" PRIMARY KEY', 'CONSTRAINT "\\1_2" PRIMARY KEY', atmpl)
				
				 
			
			#print tmpl
			#fetch object name from log file name
			m = re.match( r'.*\.([\w]+)\.([\w]+)\.ddl',dfn)		
			objn=None
			objt=to_obj=btmpl=None
			pprint(m.groups())
			if m:
				objt=m.groups()[0]
				objn=m.groups()[1]
				print 'Object type: %s' % objt
				print 'Object name: %s' % objn
			#print dfn
			assert objn,'Could not identify object name.'
			assert objt,'Could not identify object type.'
			#sys.exit(1)
			rx= re.compile( r'(\.ddl)$')		
			out_dfn = rx.sub( '.to_ddl', dfn)
			if objt=='TABLE':				
				#out_dfn =out_dfn.replace(self._pp['FROM_TABLE'],self._pp['TO_TABLE'])
				print out_dfn
				out_dfn =out_dfn.replace("TABLE.%s.to_ddl" %self._pp['FROM_TABLE'],"TABLE.%s.%s.to_ddl" % (self._pp.get('SCHEMA_NAME'),self._pp['TO_TABLE']))
				print out_dfn
				#sys.exit(1)
				btmpl = "%s\n/\n" % atmpl.replace('"%s"' % self._pp['FROM_TABLE'],'"%s"' % self._pp['TO_TABLE'])
				
			if objt=='INDEX':
				
				btmpl = atmpl.replace(self._pp['FROM_TABLE'],self._pp['TO_TABLE'])
				out_dfn =out_dfn.replace(self._pp['FROM_TABLE'],self._pp['TO_TABLE'])
				#fix index names which do not contain table names
				suff=''
				
				m= re.match( r'.*(\_[A-Z\d]+)$', objn)
				if m:
					suff=m.groups()[0]
				to_obj= "IDX_%s%s" % (logger.get_ts() , suff)
				print 'New index name: %s' % objn
				out_dfn =out_dfn.replace(objn,to_obj)
				btmpl = "%s\n/\n" % btmpl.replace(objn,to_obj)
				assert to_obj,'Could not create out object name.'
			assert out_dfn,'Could not create out file name.'
			
			#print atmpl
			print atmpl[:100]
			print self._pp.get('SCHEMA_NAME')
			print '---------------------------------'
			print btmpl[:100]
			pprint(self._pp)
			#sys.exit(1)
			assert btmpl[:100]!=atmpl[:100] ,'Name replace failed.'
			assert ".%s" % self._pp['FROM_TABLE'] not in btmpl ,'Name replace failed.'
			
			#pprint(out_dfn)
			#out_dfn =out_dfn.replace("TABLE.%s.to_ddl" %self._pp['FROM_TABLE'],"TABLE.%s.to_ddl" % self._pp['TO_TABLE'])
			#print out_dfn
			#sys.exit(1)
			fout=open(out_dfn,"w")
			fout.write(btmpl)
			fout.close()
			#print(out_dfn)
			#fout=open(dfn,"r")
			#tmpl=f.read()
			self.set_p('TEMPLATE_LOC',out_dfn)
			self.set_template(etl_object,None)
			#pprint(etl_object)
			#sys.exit(1)
			
			#self.dml(etl_object, logger)
			
			to_db = self._pp.get('TO_DB')
			assert to_db, 'Target db is not set'
			(out,status) = self.do_query(to_db, None, out_dfn, re.compile(r'.*'))
			print out
			print status
			logger.info('#### END of publish')
		return 0

		

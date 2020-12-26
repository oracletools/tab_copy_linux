#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all hierarchy transformation routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re
import timeit
import traceback,time
#import StringIO
from pprint import pprint
from copy import Copy
#import fcntl, shlex, subprocess
from subprocess import Popen, PIPE
import shlex
import threading
from datetime import date, timedelta
import types, pickle
import Queue
#import threading
#import urllib2
import time
import subprocess

STACKTRACE_MAX_DEPTH = 2
	
class app_utils:
	"""A class for hierarchy maintenance."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		#Copy.__init__(self, pipelinemeta, None, extract_logger)
		self._result=[]
		self._gwc={} # global worker cache
		self._wc={} # worker cache
		#self._global_result=[]
		self._process_meta= pipelinemeta["process_spec"]
		self._pipeline_flags=environment._pipeline_flags
		self._FLAGS=environment._FLAGS
		self._connector= pipelinemeta["connector"]
		self._output_files = {}
		self._environment=environment
		self._logger = extract_logger
		self._pipeline= self._environment.pipeline()

		self._globals=self._pipeline['globals']
		self._env_default=self._environment.env_default()

		self._etl_object=None
		self._pp={} #parsed params
		self._p ={} #unparsed params
		self._ci={} #column index
		self._ci_nots={} #column index, no timestamps
		self._cci={} #common column index
		self._cci_nots={} #common column index, no timestamps	
		self._default_df ='DD-MON-RR'
		self._default_login=None
	def p(self,pname):
		out = self._pp.get(pname)
		assert out,'Parameter %s is not set' % pname
		return out		
	def set_p(self, key, val):
		self._p[key]=val
		self._pp[key]=val
	def get_p(self, key, default=None):
		out = default
		if self.is_set(key):
			out = self._pp[key]
		return out			
	def get_latest_output_files(self):
		assert 'LATEST' in self._gwc, 'LATEST is not set.'
		assert 'OUTPUT_FILE' in self._gwc['LATEST'], 'COLUMNS are not set in LATEST.'
		return self._gwc['LATEST']['OUTPUT_FILE']

	def get_latest_tables(self):
		assert 'LATEST' in self._gwc, 'LATEST is not set.'
		assert 'TABLE' in self._gwc['LATEST'], 'COLUMNS are not set in LATEST.'
		return self._gwc['LATEST']['TABLE']
	
	def getPassword(self,pwordString):
		if not pwordString or pwordString.isspace() or not 'pwpl' in pwordString:
			return pwordString
		else:
			p = subprocess.Popen(pwordString, stdout=subprocess.PIPE,shell=True)
			password, err = p.communicate()
			print 'password created through pwpl'
			print password.strip()
			assert password
			return password.strip()	
	
	
	def get_inline_ora_login_child(self, connector):
		assert connector.has_key('type'), 'Connector has no <type> attribute'
		assert connector['type']=='inline', 'Undefined connector type "%s".  Expected "inline".' % connector['type']
		assert connector.has_key('pword'), 'Inline Connector has no <pword> attribute'
		assert connector.has_key('schema'), 'Inline Connector has no <schema> attribute'
		assert connector.has_key('sid'), 'Inline Connector has no <sid> attribute'
		assert connector.has_key('HOST'), 'Inline Connector has no <HOST> attribute'
		assert connector.has_key('PORT'), 'Inline Connector has no <PORT> attribute'
		print connector['pword']
		return "%s/%s@(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST =%s)(PORT = %s)))(CONNECT_DATA=(SID = %s)))" %(connector['schema'], self.getPassword(connector['pword']), connector['HOST'], connector['PORT'], connector['sid'])


	def get_ora_login(self, connector):
		if connector.has_key('type'):
			if connector['type']=='inline':
				return self.get_inline_ora_login(connector)
			else:
				pass
				#self._logger.warning('Unknown connector type - assuming regular connect type.')	
		assert connector.has_key('pword'), 'Connector has no <pword> attribute'
		assert connector.has_key('schema'), 'Connector has no <schema> attribute'
		assert connector.has_key('sid'), 'Connector has no <sid> attribute'
		print connector['pword']
		print connector['schema']
		print connector['sid']
		return "%s/%s@%s" %(connector['schema'], self.getPassword(connector['pword']), connector['sid'])
	

	def set_params(self, etl_object, logger):
		""" Parse parameters """
		#reset for new worker
		#pprint(etl_object)
		if not self._p:
			self._p={}
		if not self._pp:
			self._pp={}
		#if not self._pd:
		#	self._pd={}
		#set shell params
		self._p['TIMESTAMP'] = logger.timestamp_string
		self._pp['TIMESTAMP'] = logger.timestamp_string
		
		#pprint(self._env_default)
		for key in self._env_default['param']:
			val=self._env_default['param'][key]
			self._pp[key]=val
			self._p[key]=val	
			#self._pd[key]=val			
		#sys.exit()
		
		#set defaults
		#pprint(self._pipeline)
		#sys.exit(1)
		self._pp['PIPELINE_NAME']=self._pipeline['name']
		self._p['PIPELINE_NAME']=self._pipeline['name']

		
		#set pipeline global params
		for key in self._globals['param']:
			val=self._globals['param'][key]
			self._pp[key]=val
			self._p[key]=val
			#print key,val
		#set local params
		if etl_object['node'].has_key('param'):
			for param in etl_object['node']['param']:
				self._pp[param] = etl_object['node']['param'][param]['value']
				self._p[param] = etl_object['node']['param'][param]['value']
				#print param, etl_object['node']['param'][param]['value']

		#parse ref params
		regexp=re.compile(r'((%)([\w\_]+)(%))')		
		for param in self._p:

			m = re.match(regexp, self._p[param])
			if m:
				assert not(self._process_meta.has_key(m.groups()[2]) and self._connector.has_key(m.groups()[2])), 'EXCEPTION: process_spec and connectors has the same key %s' % m.groups()[2]
				if (self._process_meta.has_key(m.groups()[2])):
					self._pp[param]=self._pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
					
				if (self._connector.has_key(m.groups()[2])):
					#print m.groups()[2]
					self._pp[param]= self.get_ora_login(self._connector[m.groups()[2]]) 
		#pprint(self._FLAGS)
		for flag in self._FLAGS:
			if self._pp.has_key(flag):
				self._pp[flag] = self._FLAGS[flag].strip()
		#pprint(self._FLAGS)
		##pprint(self._pp)
		#sys.exit(1)
		#self._pipeline
		#self._pp['WORKER_NAME']=self.get_wn()
		#self._p['WORKER_NAME']=
		regexp=re.compile(r'(%[\w\_]+\%)')		
		#print self._pipeline
		if 0:
			assert self._pipeline.get('name'), 'Pipeline name is not set'
			pn = self._pipeline['name']
			m = re.findall(regexp,pn)
			if m:
				print m
				for arg in m:
					#argarg.strip('%')
					assert self._pp.get(arg.strip('%')), 'PARAMETER %s is not defined but used in PIPELINE_NAME.' % arg
					pn=pn.replace(arg,self._pp.get(arg.strip('%')))
			print pn
			self._pp['PIPELINE_NAME']=pn
			self._p['PIPELINE_NAME']=self._pp.get('PIPELINE_NAME')
			#pprint(self._pp)
			print dir(self._environment._pipeline_flags)
			m=None

		#sys.exit(1)
		wn = etl_object['name']
		
		m = re.findall(regexp,wn)
		if m:
			print m
			for arg in m:
				#argarg.strip('%')
				assert self._pp.get(arg.strip('%')), 'PARAMETER %s is not defined but used in WORKER_NAME.' % arg
				wn=wn.replace(arg,self._pp.get(arg.strip('%')))
		print wn
		self._pp['WORKER_NAME']=wn
		self._p['WORKER_NAME']=self._pp.get('WORKER_NAME')
		#sys.exit(1)
	def p_if(self, key):
		if key in self._pp:
			return int(self._p[key])>0
		return False
	def is_set(self, key):
		if key in self._pp:
			return self._pp[key].strip()
		return None	
	def p_attr(self, key, attr=None):
		assert self.is_set(key),'Parameter "%s" does not exists.' % key
		if not attr:
			attr = 'VALUE'
		assert self.is_set(key, attr),'Parameter "%s" does not have attribute "%s".' % (key, attr)
		return self._p[key][attr]
	def get_log_fn(self,dir,ext,tab):
		fexists=0
		if self.is_set('OUTPUT_FILE'):
			outf = self._pp['OUTPUT_FILE']
			if os.path.isfile(outf):
				fexists=1
				#self._logger.warn('OUTPUT_FILE does not exists.')
			return (outf	,fexists)
				
			
		datdir= '%s/%s' % (self._logger.get_logdir(),dir)
		gzfn=None
		if not os.path.isdir(datdir):
			os.mkdir(datdir) 	
		#if self.p_if('IF_COMPRESSED_SPOOL'):
		#	ext='gz'
		gzfn = '%s/%s.%s.%s' % (datdir,self._pp['WORKER_NAME'],tab,ext)
		if self.is_set('PARTITION'):
			gzfn = '%s/%s.%s.%s.%s' % (datdir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'],ext)
		return (gzfn,fexists)
	def set_template(self,etl_object, template):
		""" Sets sql_template """
		assert etl_object, "etl_object is not set."
		etl_object['node']['sql_template']={}
		etl_object['node']['sql_template']['data']=template			
	def cleanup(self):
		if 0:
			self._ci={} #column index
			self._ci_nots={} #column index, no timestamps
			self._cci={} #common column index
			self._cci_nots={} #common column index, no timestamps		
			self._pp={} #parsed params
			self._p ={} #unparsed params	
		else:
			pass

	def get_template(self, etl_object, logger):
		""" Get sql template from worker. """
		#pprint(etl_object)
		#pprint(type(etl_object['node']['param']))
		#pprint(self._connector)
		regexp=re.compile(r'((%)([\w\_\.]+)(%))')
		pp=self._pp
		"""for param in etl_object['node']['param']:
			pp[param] = etl_object['node']['param'][param]['value']
			#print pp[param] 
			#print int(self._environment._pipeline_flags.release)
			if int(self._environment._pipeline_flags.release):
				if etl_object['node']['param'][param].has_key('release'):
					pp[param] = etl_object['node']['param'][param]['release']

			m = re.match(regexp, etl_object['node']['param'][param]['value'])
			if m:
				#test = etl_object['node']['param'][param]['value'].replace(conf,self._process_meta[conf])
				#pprint(m.groups()[2])
				if (self._process_meta.has_key(m.groups()[2])):
					pp[param]=pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
				if (self._connector.has_key(m.groups()[2])):
					pp[param]= pp[param].replace(m.groups()[0],'%s/%s@%s' % 
												 (self._connector[m.groups()[2]]['schema'],self._connector[m.groups()[2]]['pword'],self._connector[m.groups()[2]]['sid']))
		"""
		template= etl_object['node']['sql_template']['data']
		if template:
			m = re.findall(regexp, template)
			if m:
				#pprint(m)
				for t in m:
					if pp.has_key(t[2]):
						template=template.replace(t[0],'%s' % pp[t[2]])
					else:
						if self._process_meta.has_key(t[2]):
							template=template.replace(t[0],'%s' % self._process_meta[t[2]])
			#self._logger.info(template)
			#pprint(pp)
			#sys.exit(1)
		self._pp=pp
		#pprint(template)
		#sys.exit(1)
		return template 
	def get_connector(self, key):
		#print key
		clean = str.strip(str(key),'%')
		assert  self._connector.has_key(clean), 'Connector %s does not exists.' % clean
		return self._connector[clean]
	def gt(self, tab_t):
		return '%s.%s' % (tab_t[0].strip(),tab_t[1].strip())		
	def get_cc_key (self, db_tab_t):
		(db, tab_t) =db_tab_t
		return "%s|%s" % (db, self.gt(tab_t))
	def get_common_cols(self, from_db, from_t, to_db, to_t):
		from_key = self.get_cc_key((from_db, from_t))
		#print 'from_key=%s' % from_key
		to_key = self.get_cc_key( (to_db, to_t))
		#print 'to_key= %s'% to_key
		#pprint (self._cci.keys())
		#sys.exit(1)
		if not self._cci.has_key(from_key):
			self._cci[from_key]={}
			self._cci[from_key][to_key]={}
		if not self._cci.has_key(to_key):
			self._cci[to_key]={}	
			self._cci[to_key][from_key]={}
		#pprint (self._cci.keys())
		if len(self._cci[to_key][from_key])==0:	
			#print 'getting columns for:',from_db, from_t
			(r_from,s_from) = self.get_columns(from_db, from_t)
			#print r_from
			#sys.exit(1)
			#print 'getting columns for:',to_db, to_t
			(r_to,s_to) = self.get_columns(to_db, to_t)
			
			
			if not s_from and not s_to:
				r_int = list(set(r_from) & set(r_to))
				r_int.sort() 
				self._cci[to_key][from_key]=r_int
				self._cci[from_key][to_key]=r_int
				return (r_int, 0)
			else:
				self._logger.error('Cannot get column lists.')
			return (None, 1)	
		else:
			#print 'cc exists'
			return (self._cci[to_key][from_key], 0)	
	def get_default_conn(self,from_conn,to_conn):
		if self.is_inline(from_conn) &  self.is_inline(to_conn):
			return (None, 1)
		if self.is_inline(to_conn):
			return (to_conn,0)
		if self.is_inline(from_conn):
			return (from_conn,0)
		return (to_conn,0)
	def is_inline(self, conn):
		#pprint(conn)
		if conn.has_key('type'):
			if conn['type']=='inline':
				return 1
		return 0	
	def ckey2cols(self, col_key):
		return map(lambda x: x.split(':')[0],col_key)
	




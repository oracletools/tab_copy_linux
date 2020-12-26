#!/usr/bin/python2.4
#
# Copyright 2011 .  All Rights Reserved.
# 
#

"""This module contains worker list class.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os
import string
import re
from pprint import pprint
import threading



STACKTRACE_MAX_DEPTH = 2

def confirm(test, testname = "Test", logger=None):
	if not test:
		msg=  "Failed: " + testname
		if logger:
			logger.error('%s (%s)' % (msg, test) )
		else:
			self._logger.error('%s (%s)' % (msg, test) )
			#raise Exception( '%s (%s)' % (msg, test) )	

class Worker(threading.Thread):
	"""A class for defining worker."""

	def __init__(self, environment, extract_logger):
		"""Worker List
		"""
		self._gwc={} #global worker cache
		self.wl={}
		self._pp={} #parsed params
		self._p ={} #unparsed params
		self._logger=extract_logger
		self._etl_object={}
		self._FLAGS=environment._FLAGS
		self._env_default=environment.env_default()
		self._environment=environment
		self._pipeline= self._environment.pipeline()
		self._globals=self._pipeline['globals']
		self._process_meta=self._environment._pipeline_spec["process_spec"]
		self._connector= self._environment._pipeline_spec["connector"]
		threading.Thread.__init__ ( self )	

	def add(self,worker):
		self.wl[len(self.wl)]=worker
		
	def append(self,worker):
		self.wl.append(worker)
	def run(self):
		"""Start the worker job.
		Args:
		  etl_object: table XML object from etlmeta
		"""
		#pprint(self._etl_object)
		#sys.exit(1)
		self._logger.info('#### START of workerflow.')
		#pprint(type(self.wl))
		for wid,wo in self.wl.iteritems():
			#print wid
			#wo=swo[0]
			#etl_object
			#pprint(wo._etl_object)	
			wo._gwc=self._gwc			
			assert wo._etl_object['attr'].has_key('method'),\
					'copy method is not defined in %s.%s' %( __name__,wo.__class__.__name__)
			method = wo._environment.get_env_attr(string.strip(wo._etl_object['attr']['method'], '%'))
			#method = self._environment.get_env_attr(self._etl_object['attr']['method'])
			#pprint(method)
			#wo._global_result=self._result
			_exec = 'wo.%s(wo._etl_object,wo._logger)' % (method)
			#print 'before exec'
			#print _exec
			#try:
			if 1:
				print '------------------------'
				pprint(wo._p)
				print _exec
				exec _exec	
				#pprint(wo._wc)
				#self._import(wo._wc)
				print '------------------------'
				#pprint(wo._p)
				#print '---------GLOBAL RESULT-------------'
				##pprint(self._gwc)				
				#print '---------RESULT-------------'
				#pprint(wo._wc)				
			else:
				print _exec
			#self._import(wo.export())
		self._logger.info('#### END of workerflow.')
		
	def _import(self,wc):
		""" import subworker results """
		#self._result[exp[0]] = exp[1]
		for c in wc:
			self._gwc[c]=wc[c]
		
	def set_p(self, key, val):
		self._p[key]=val
		self._pp[key]=val
	def get_p(self, key, default=None):
		out = default
		if self.is_set(key):
			out = self._pp[key]
		return out
	def p_if(self, key):
		return self._p.has_key(key) and int(self._p[key])>0
	def is_set(self, key):
		return self._p.has_key(key)	
	def set(self, etl_object):
		#print 'setting params'
		self._etl_object=etl_object
		if len(self._pp)==0:
			self.set_params(etl_object, self._logger)		
	def set_params(self, etl_object, logger):
		""" Parse parameters """
		#reset for new worker
		#pprint(etl_object)
		if 1:
			if not self._p:
				self._p={}
			if not self._pp:
				self._pp={}	
		else: 
			self._p={}
			self._pp={}
		self._pd={}

		#pprint(self._env_default)
		for key in self._env_default['param']:
			val=self._env_default['param'][key]
			self._pp[key]=val
			self._p[key]=val	
			self._pd[key]=val			
		#sys.exit()
		
		#set defaults
		#pprint(self._pipeline)
		#sys.exit(1)
		self._pp['PIPELINE_NAME']=self._pipeline['name']
		self._p['PIPELINE_NAME']=self._pipeline['name']
		self._pipeline
		self._pp['WORKER_NAME']=etl_object['attr']['name']
		self._p['WORKER_NAME']=etl_object['attr']['name']
		
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
				self.confirm(not(self._process_meta.has_key(m.groups()[2]) and self._connector.has_key(m.groups()[2])), 'EXCEPTION: process_spec and connectors has the same key %s' % m.groups()[2])
				if (self._process_meta.has_key(m.groups()[2])):
					self._pp[param]=self._pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
		#pprint(self._FLAGS)
		for flag in self._FLAGS:
			if self._pp.has_key(flag):
				self._pp[flag] = self._FLAGS[flag].strip()
	def confirm(self,test, testname = "Test", logger=None):
		if not test:
			msg=  "Failed: " + testname
			if logger:
				logger.error('%s (%s)' % (msg, test) )
			else:
				self._logger.error('%s (%s)' % (msg, test) )
				#raise Exception( '%s (%s)' % (msg, test) )						

#!/usr/bin/python2.4
#
# Copyright 2011 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all data access/extraction routines for PADB db.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os
if os.name == 'nt':
	import clr
	from ctypes import * 
import string
import re
import timeit
import datetime
import traceback,time
import StringIO
from pprint import pprint
from copy import Copy
#import fcntl, shlex, subprocess
from subprocess import Popen, PIPE
import shlex
import threading
import types


STACKTRACE_MAX_DEPTH = 2

def confirm2(test, testname = "Test"):
    if not test:
        msg=  "Failed: " + testname
        raise Exception( '%s (%s)' % (msg, test) )
		
def confirm(test, testname = "Test", logger=None):
    if not test:
		msg=  "Failed: " + testname
		if logger:
			logger.fatal('%s (%s)' % (msg, test) )
		else:
			raise Exception( '%s (%s)' % (msg, test) )		

class bash(threading.Thread):
	"""A class for extracting dimension data from csv file."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		#Copy.__init__(self, pipelinemeta, None, extract_logger)
		self._process_meta= pipelinemeta["process_spec"]
		self._connector= pipelinemeta["connector"]
		self._output_files = {}
		self._environment=environment
		self._logger = extract_logger
		self._pipeline= self._environment.pipeline()
		self.pipeline_name=self._environment._pipeline['etldataflow']['name']
		#pprint (self._pipeline)
		#sys.exit(1)		
		self._globals=self._pipeline['globals']
		self._env_default=self._environment.env_default()
		#sys.exit(1)
		#if self._pipeline.has_key('FIELD_TERMINATOR'):

		self._ci={} #column index
		self._ci_nots={} #column index, no timestamps
		self._cci={} #common column index
		self._cci_nots={} #common column index, no timestamps		
		self._etl_object=None
		self._pp={} #parsed params
		self._p ={} #unparsed params
		self._default_login =''
		if os.name == 'nt':
			self.dllh = cdll.LoadLibrary(self.dllPath) 
		else:
			#self._logger.warning("cdll.LoadLibrary is not supported")
			pass
		#read shell template
		f=open("%s/sh_template.txt" % self._process_meta['template_path'],"r")
		self.sh_tmpl=f.read()
		#pprint(pipelinemeta)
		#sys.exit(0)
		self._padb="map"
		threading.Thread.__init__ ( self )	
	def get_cmd_template(self, etl_object):
		confirm(etl_object.has_key('node'), 'Missing worker <node>.')
		confirm(etl_object['node'].has_key('cmd_template'), 'Missing <cmd_template> for worker %s.' % etl_object['name'])
		confirm(etl_object['node']['cmd_template'].has_key('data'), 'Missing <data> in %s for worker %s.' % ('cmd_template',etl_object['name']))
		return self.get_bash_template(etl_object)

	def bash_cmd(self, etl_object, logger):
		self.set(etl_object)
		cmd = self.get_cmd_template(etl_object)
		pprint(cmd)
		logger.info('Executing bash cmd %s' % etl_object['name'])
		logger.info('#### START of bash_cmd %s.' % etl_object['name'])
		a_t = datetime.datetime.now()
		(out,status,elapsed) = self.do_bash_cmd(cmd)
		worker_sec = datetime.datetime.now()-a_t
		logger.info('#### END of bash_cmd %s.' % etl_object['name'])
		#pprint(out)
		if status==0:
			self.save_pa_log(etl_object, cmd, elapsed,status, worker_sec,logger)
		else:
			self.save_pa_log(etl_object, cmd, elapsed,status, worker_sec,logger)	
		if status==0:
				logger.info("#### bash_cmd of %s finished successfully." % etl_object['name'])
		else:
			logger.warning('bash_cmd failed for %s.' % etl_object['name'])			
		
	def do_bash_cmd(self, cmd):
		f = ""
		out=[]
		elapsed=[]
		errpos=-1

		if 1:			
		
			p1 = Popen(['echo', cmd], stdout=PIPE)

			p2 = Popen([ '/bin/bash'], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
			output=' '
			while output:
				output = p2.stdout.readline()
				out.append([output])
				#print output.strip()
				#sys.stdout.write(output)
				#sys.stdout.flush()
				self._logger.info( output.strip())	
				tm=' '
				if 0:
					while tm:
						tm = p2.stderr.readline()
						if tm.strip():
							elapsed.append(tm)
							out.append(tm)
							#print tm.strip()
							self._logger.info( 'ELAPSED:', tm.strip())	
					#pprint(tm)
					if len(elapsed):
						#status=0
						self._logger.log(string.join(elapsed,'\n'))	
					
			status=p2.wait()
			print 'do_bash_cmd status= ', status
			if status>0:
				if len(out):
					self._logger.error(string.join(out,''))	
					self._logger.error(string.join(elapsed,''))	
		return (out,status,elapsed)		
		
	def set(self, etl_object):
		#print 'setting params'
		self._etl_object=etl_object
		if len(self._pp)==0:
			self.set_params(etl_object, self._logger)
	def set_params(self, etl_object, logger):
		""" Parse parameters """
		#reset for new worker
		#pprint(etl_object)
		self._p={}
		self._pp={}

		#pprint(self._env_default)
		for key in self._env_default['param']:
			val=self._env_default['param'][key]
			self._pp[key]=val
			self._p[key]=val		
		#sys.exit()
		
		#set defaults
		#pprint(self._pipeline)
		#sys.exit(1)
		self._pp['PIPELINE_NAME']=self._pipeline['name']
		self._p['PIPELINE_NAME']=self._pipeline['name']
		self._pipeline
		self._pp['WORKER_NAME']=etl_object['name']
		self._p['WORKER_NAME']=etl_object['name']
		
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
				confirm(not(self._process_meta.has_key(m.groups()[2]) and self._connector.has_key(m.groups()[2])), 'EXCEPTION: process_spec and connectors has the same key %s' % m.groups()[2])
				if (self._process_meta.has_key(m.groups()[2])):
					self._pp[param]=self._pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
					
				if (self._connector.has_key(m.groups()[2])):
					#print m.groups()[2]
					self._pp[param]= self.get_pa_login(self._connector[m.groups()[2]]) 			
			
	def get_bash_template(self, etl_object):
		""" Runs mist tool """
		#pprint(etl_object)
		#pprint(type(etl_object['node']['param']))
		#pprint(self._connector)
		regexp=re.compile(r'((%)([\w\_]+)(%))')
		pp=self._pp
		template= etl_object['node']['cmd_template']['data']
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
		
		#sys.exit(1)
		return template.strip()
	def confirm(self,test, testname = "Test"):
		if not test:
			msg=  "Failed: " + testname
			raise Exception( '%s (%s)' % (msg, test) )			
	def get_spec(self, key):
		return self._environment.get_process_spec(key)
	def run(self):
		"""Start the extraction job.

		Note that this class requires that we had already set the
		output_pipe attribute via the set_output_pipe simple setter.
		The output_pipe attribute is inherited from the Worker class
		via the Extracter class.

		Args:
		  etl_object: table XML object from etlmeta
		"""
		#pprint(self._etl_object)
		#sys.exit(1)
		confirm(self._etl_object['attr'].has_key('method'),
				'copy method is not defined in %s.%s' %( __name__,self.__class__.__name__))
		pprint(self._etl_object)
		method = self._environment.get_env_attr(string.strip(self._etl_object['attr']['method'], '%'))
		#method = self._environment.get_env_attr(self._etl_object['attr']['method'])

		_exec = 'self.%s(self._etl_object,self._logger)' % (method)
		#print 'before exec'
		#print _exec
		#try:
		if 1:
			exec _exec


		#except Exception, e:
			#pprint(dir(e))
			#print e.strerror
			#self._logger.error(dir(e))
			#self._logger.error(sys.exc_info())
			#self.PrintException(self._logger) 
			#print 'worker exception=',e
			#print sys.exc_info()
		#			raise e

	def PrintException(self,logger, email=0):
		tb = sys.exc_info()[2]
		stack = []

		while tb:
				stack.append(tb.tb_frame)
				tb = tb.tb_next

		output = None
		try:
				try:
						output = StringIO.StringIO()
						traceback.print_exc(STACKTRACE_MAX_DEPTH, output)
						output.write("Locals by frame, innermost last\n")
						for frame in stack:
								output.write("\n")
								output.write("Frame %s in %s at line %s\n" % (frame.f_code.co_name,
																			  frame.f_code.co_filename,
																			  frame.f_lineno))
								for key, value in frame.f_locals.items():
										try:
											#print key
											if key=='conn':
												#val=str(value)
												for key in value.keys():
													value[key]['pword']='***'
											if key=='to_db' or key=='from_db' or key=='login' or key=='args' or key=='pp' or key=='to_key' or key=='col_key' or key=='from_key':
												#val=str(value)
												value= re.sub("\/(.*)\@","/***@",str(value))
										
											output.write('\t%s=%s\r\n' % (key, str(value)))
										except:
												
												output.write('[UNPRINTABLE VALUE]\n')
				except Exception:
						traceback.print_exc()

		finally:
				if output:
						#sys.stderr.write(output.getvalue())
						if logger:
							logger.error(output.getvalue())
						output.close()
	def p_if(self, key):
		return self._p.has_key(key) and int(self._p[key])>0
	def is_set(self, key):
		return self._p.has_key(key)	
	def p_attr(self, key, attr=None):
		self.confirm(self.is_set(key),'Parameter "%s" does not exists.' % key)
		if not attr:
			attr = 'VALUE'
		self.confirm(self.is_set(key, attr),'Parameter "%s" does not have attribute "%s".' % (key, attr))
		return self._p[key][attr]

	def set_p(self, key, val):
		self._p[key]=val
		self._pp[key]=val
	def get_p(self, key, default=None):
		out = default
		if self.is_set(key):
			out = self._pp[key]
		return out		
		
	def mail(self, email, table):
		SENDMAIL = "/usr/sbin/sendmail" # sendmail location
		import os
		p = os.popen("%s -t" % SENDMAIL, "w")
		p.write("From: %s\n" % email)
		p.write("To: %s\n" % email)
		p.write("Subject: Copy log: %s\n" % table)
		p.write("\n") # blank line separating headers from body
		#p.write("Please, find log file attached.\n")
		p.write("%s" % '#'*80)
		p.write(" \n")
		p.write("# %s\n" % self._logger.logfile_name())
		p.write("%s" % '#'*80)
		p.write(" \n")
		f = open(self._logger.logfile_name(), "r")
		p.write("%s\n" % f.read())
		sts = p.close()
		if sts != 0:
		  print "Sendmail exit status", sts

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

	def  p(self,pname):
		confirm(self._pp.has_key(pname),'Parameter %s is not set' % pname)
		return self._pp[pname]


	def get_source_path(self, etl_object, logger):
		""" Gets path to a source csv file """
		regexp=re.compile(r'((%)([\w\_]+)(%))')
		source_file =''
		pp={}
		for param in etl_object['node']['param']:
			pp[param] = etl_object['node']['param'][param]['value']
			m = re.match(regexp, etl_object['node']['param'][param]['value'])
			if m:
				if (self._process_meta.has_key(m.groups()[2])):
					pp[param]=pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
				if (self._connector.has_key(m.groups()[2])):
					pp[param]= pp[param].replace(m.groups()[0],'%s/%s@%s' % 
												 (self._connector[m.groups()[2]]['schema'],self._connector[m.groups()[2]]['pword'],self._connector[m.groups()[2]]['sid']))
		if pp.has_key('SOURCE_PATH'):
		  source_file = pp['SOURCE_PATH']
		#self._logger.info(source_file)
		#sys.exit(1)
		return source_file 


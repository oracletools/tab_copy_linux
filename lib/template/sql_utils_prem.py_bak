#!/usr/bin/python2.4
#
# Copyright 2009 . All Rights Reserved.

"""This module contains all data access/extraction routines for CSV files
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os
if os.name == 'nt':
	import clr
	from ctypes import * 
import string
import re
import timeit
import traceback,time
import StringIO
from pprint import pprint
from copy import Copy
#import fcntl, shlex, subprocess
from subprocess import Popen, PIPE
import shlex
import threading

STACKTRACE_MAX_DEPTH = 2

#from google3.dbutils.datawarehouse.etlv2.driver.utils import fileutil_wrapper
def confirm(test, testname = "Test"):
    if not test:
        msg=  "Failed: " + testname
        raise Exception( '%s (%s)' % (msg, test) )
class sqlp(threading.Thread):
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
		self._ci={} #column index
		self._ci_nts={} #column index, no timestamps
		self._cci={} #common column index
		self._cci_nts={} #common column index, no timestamps		
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
		threading.Thread.__init__ ( self )	
	def set(self, etl_object):
		self._etl_object=etl_object
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
				'method is not defined in %s.%s' %( __name__,self.__class__.__name__))
		method = self._etl_object['attr']['method']  
		_exec = 'self.%s(self._etl_object,self._logger)' % (method)
		#print 'before exec'
		#try:
		if 1:
			exec _exec


		#except Exception, e:
			#pprint(dir(e))
			#print e.strerror

			#self.PrintException(self._logger) 
			#print 'worker exception=',e
			#print sys.exc_info()
			#raise e

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
											if key=='to_db' or key=='from_db' or key=='login' or key=='args':
												#val=str(value)
												value= re.sub("\/(.*)\@","/***@",str(value))
										
											output.write('\t%s=%s\r\n' % (key, str(value)))
										except:
												
												output.write('[UNPRINTABLE VALUE]\n')
				except Exception:
						traceback.print_exc()

		finally:
				if output:
						sys.stderr.write(output.getvalue())
						if logger:
							logger.error(output.getvalue())
						output.close()
	def dml(self, etl_object, logger):
		""" Runs mist tool """
		template = self.get_template(etl_object, logger)
		if not self._default_login:
			#pprint(self._pp)
			if self._pp.has_key('DB_CONNECTOR'):
				self._default_login=self.get_ora_login(self.get_connector(self._p['DB_CONNECTOR']))
			else: 
				if self._pp.has_key('DB_INLINE_CONNECTOR'):
					self._default_login=self.get_ora_login(self.get_connector(self._p['DB_INLINE_CONNECTOR']))
		if template:
			#print self._default_login, template
			self.do_query(self._default_login, template,0)
			pass
		#relative_path=''
		#file_location = "%s%s" % (self._process_meta['LOG_ROOT'], relative_path)
		#dump_file = '%s/%s.%s' % (self._process_meta['LOG_ROOT'] , self.__class__.__name__, 'txt')
		self._logger.info("DML finished .")
		#self.get_code(etl_object)
		#pprint(etl_object)
		return 1
	def ddl(self, etl_object, logger):
		""" Runs mist tool """
		template = self.get_template(etl_object, logger)
		
		if template:
			self.do_query(template,0)
			pass
		relative_path=''
		file_location = "%s%s" % (self._process_meta['LOG_ROOT'], relative_path)
		dump_file = '%s/%s.%s' % (self._process_meta['LOG_ROOT'] , self.__class__.__name__, 'txt')
		self._logger.info("DDL finished .")
		return dump_file
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

	def validate_tab_struct(self, etl_object, logger):
		""" Parse template to list of tables """
		tmpl = self.get_template(etl_object, logger)

		regexp=re.compile(r'([\w\_]+)\.([\w\_]+)')
		template={}
		trunc_batch ={}
		m = re.findall(regexp, tmpl)
		#pprint(self._connector)
		conn=self._connector
		pp=self._pp
		confirm(pp.has_key('FROM_DB'),'FROM_DB is not defined')
		confirm(pp.has_key('TO_DB'),'TO_DB is not defined')
		if m:
			#pprint(m)
			for t in m:
				#print t
				from_db = self.get_ora_login(conn[pp['FROM_DB']])
				to_db= self.get_ora_login(conn[pp['TO_DB']]) 
				to_tab= string.join(t,'.')
				from_tab=string.join(t,'.')
				(q,status)=self.get_select_nots(from_db,t)
				#pprint(q)
		return template	
	def ok_to_copy(self, cfrom, cto, tab, logger):
		out = 1
		if len(cfrom)!=len(cto):
			#s= cto.difference(cfrom)
			#pprint(string.join(s,', '))
			logger.warning('Number of columns differ in source and target databases for table %s.' % tab)
		s= cto.difference(cfrom)
		if len(s)>0:
			#out=0
			logger.warning('Column(s) %s missing in source table.' % string.join(s,', '))
		s= cfrom.difference(cto)
		if len(s)>0:
			#out=0
			logger.warning('Column(s) %s missing in target table.' % string.join(s,', '))			
		return out
	def get_to_tab(self,t):
		if self._pp.has_key('TO_SCHEMA'):
			t[0]=self._pp['TO_SCHEMA']
		else:
			
			#sys.exit(1)
			if self._pipeline.has_key('TO_SCHEMA'):
				t[0]=self._pipeline['TO_SCHEMA']
			else:
				#print 'no TO_SCHEMA key'
				pass
				#pprint(self._pipeline)
		#print 'returning ', t
		if self._pp.has_key('TO_TABLE'):
			t[1]=self._pp['TO_TABLE']
		else:
			
			#sys.exit(1)
			if self._pipeline.has_key('TO_TABLE'):
				t[1]=self._pipeline['TO_TABLE']
			else:
				#print 'no TO_TABLE key'
				pass		
		
		
		return t
	def get_from_tab(self,t):
		if self._pp.has_key('FROM_SCHEMA'):
			t[0]=self._pp['FROM_SCHEMA']
		else:
			if self._pipeline.has_key('FROM_SCHEMA'):
				t[0]=self._pipeline['FROM_SCHEMA']			
		return t

				
				
	def is_inline(self, conn):
		#pprint(conn)
		if conn.has_key('type'):
			if conn['type']=='inline':
				return 1
		return 0
	def get_default_conn(self,from_conn,to_conn):
		if self.is_inline(from_conn) &  self.is_inline(to_conn):
			return (None, 1)
		if self.is_inline(to_conn):
			return (to_conn,0)
		if self.is_inline(from_conn):
			return (from_conn,0)
		return (to_conn,0)
	def sql_plus_copy(self, etl_object, logger):
		""" Runs copy """
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch(etl_object, logger)

		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		#pprint(etl_object)
		#sys.exit(0)
		if status:
			logger.warning('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')

			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			to_db= self._pp['TO_DB'] 
			for tab in tmpl_batch:

				if 1:

					to_tab= self.get_to_tab(string.split(tab,'.'))
					from_tab=self.get_from_tab(string.split(tab,'.'))
					#print tab, to_tab
					#print to_db,to_tab
					#(cto, tostatus)=self.get_columns(to_db,to_tab)
					#print from_db,from_tab
					#(cfrom, fromstatus)=self.get_columns(from_db,from_tab)

					#if (not tostatus) and (not fromstatus) and self.ok_to_copy(set(cfrom), set(cto), tab, logger):
					if 1:
						#fix
						logger.info('#### START copy of %s.' % etl_object['name'])
						self.do_query(to_db, tmpl_batch[tab]['VIEW'],0)
						self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
						#pprint(self._default_login)
						self.do_query(self._default_login, tmpl_batch[tab]['INSERT'],0)
						logger.info('#### END copy of %s.' % etl_object['name'])
						#logger.info("COPY finished successfully.")
					else:
						logger.warning('#### Skipping %s.' % etl_object['name'])
						logger.info("COPY of table %s failed." % etl_object['name'])
			#sys.exit(0)
		if self._pp.has_key('EMAIL_TO'):
			confirm(self._process_meta[self._pp['EMAIL_TO']], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			#print self._process_meta[self._pp['EMAIL_TO']]
			self.mail(self._process_meta[self._pp['EMAIL_TO']],etl_object['name'] )
		
		#self.get_code(etl_object)
		#pprint(etl_object)
		return 0
	def get_line_length(self, r):
		l=0
		regexp=re.compile(r'\:(\d+)\)')
		m = re.findall(regexp, r[len(r)-1])
		return int(m[0])+20
		
	def do_load_fixed(self, from_db, from_t, to_db, to_t,tmpl):
		f = ""
		out=[]
		err=[]
		confirm(len(from_db)>0, 'Source login is not set.')
		confirm(len(to_db)>0, 'Target login is not set.')
		(r_cc, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print 'common cols'
		r_cc.sort()
		#pprint(r_cc)
		#sys.exit(1)
		cl =  string.join(r_cc,",")
		(r_cp, status)=self.get_col_position(((from_db, from_t),(to_db, to_t)))
		#pprint(r_int)
		#sys.exit(1) 
		llen=6316 
		if not status:
			llen = self.get_line_length(r_cp)
			to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			
			ctl=self.get_ctl_fixed(string.join(self.get_to_tab(to_t),'.'),r_cp)
			pprint(ctl)
			fname= 'sqlloader/%s.ctl' % to_tab
			f = open(fname, 'w')
			status = f.write(ctl)
			if status!= None:
				self._logger.error('Cannot write to %s.' % fname)
			f.close()
	
			# get col formats
			(r, status) =self.get_col_format(((from_db,from_t),(to_db, to_t)))
			#pprint(r)
			#sys.exit(1)
			col_format = string.join(r,'\n')
			q= "%s\nset head off line %s pages 0 num 2 echo off feedback off space 0 tab off\nSELECT %s FROM %s %s;" % (col_format, llen, cl , string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			self._logger.info(q)
			#sys.exit(1)
			p1 = Popen(['echo', q], stdout=PIPE)
			p2 = Popen([ 'sqlplus', '-S',from_db], stdin=p1.stdout, stdout=PIPE)
			if 1:
				p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, 'rows=50000',
				'COLUMNARRAYROWS=50000','STREAMSIZE=500000','readsize=2512000',' parallel=false','bindsize=512000','direct=true', 
				#"data=\'-\'",
				'LOG=sqlloader/%s.log' % to_tab, 'BAD=sqlloader/%s.bad' % to_tab,'DISCARD=sqlloader/%s.dsc' % to_tab,'ERRORS=100'], stdin=p2.stdout, stdout=PIPE)
				output=' '
				while output:
					output = p3.stdout.readline()
					err.append(output)
					print output
					self._logger.info(output.rstrip())
				status=p3.wait()
			else:
				output=' '
				while output:
					output = p2.stdout.readline()
					err.append(output)
					print output
					self._logger.info(output.rstrip())
				status=p2.wait()			
			print ' sql status =%s' % status
			if status==1:
				self._logger.warning(string.join(err,'\n'))
			else: 
				self._logger.info(string.join(err,'\n'))
		else:
			self._logger.warning('Cannot fetch common columns.')
		return (out,status)	
		
	def sql_echo_loader(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)

		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		if status:
			logger.warning('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')
			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			to_db= self._pp['TO_DB']
			for tab in tmpl_batch:
				if 1:
					to_tab= self.get_to_tab(string.split(tab,'.'))
					from_tab=self.get_from_tab(string.split(tab,'.'))
					if 1:
						logger.info('#### START copy of %s.' % tab)
						self.do_load(from_db, from_tab, to_db, to_tab)
						logger.info('#### END copy of %s.' % tab)
					else:
						logger.warning('#### Skipping %s.' % tab)
						logger.info("COPY of table %s failed." % tab)
		if self._pp.has_key('EMAIL_TO'):
			confirm(self._process_meta[self._pp['EMAIL_TO']], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._process_meta[self._pp['EMAIL_TO']],tab )
		return 0
	def sql_echo_loader_fixed(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)

		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		
		if status:
			logger.warning('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')
			#pprint(etl_object)
			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			to_db= self._pp['TO_DB']
			for tab in tmpl_batch:
				if 1:
					to_tab= self.get_to_tab(string.split(tab,'.'))
					from_tab=self.get_from_tab(string.split(tab,'.'))
					if 1:
						logger.info('#### START copy of %s.' % tab)
						self.do_load_fixed(from_db, from_tab, to_db, to_tab,tmpl_batch[tab])
						logger.info('#### END copy of %s.' % tab)
					else:
						logger.warning('#### Skipping %s.' % tab)
						logger.info("COPY of table %s failed." % tab)
		if self._pp.has_key('EMAIL_TO'):
			confirm(self._process_meta[self._pp['EMAIL_TO']], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._process_meta[self._pp['EMAIL_TO']],tab )
		return 0		
	def do_query(self, login, query, analyze=1, regexp=None, grp=None):
		f = ""
		out=[]
		err=[]
		confirm(len(login)>0, 'Default login is not set.')
		if 1:			
			#from subprocess import Popen, PIPE
			q=''
			if analyze:
				q = "%s\nset autotrace on timing on echo on serveroutput on\n%s\n%s" % ('-'*20, query,'-'*20)
			else:
				q = "%s" % (query)
			
			self._logger.info(login)
			self._logger.info(q)
			p1 = Popen(['echo', q], stdout=PIPE)
			p2 = Popen([ 'sqlplus', login], stdin=p1.stdout, stdout=PIPE)
			output=' '
			while output:
				output = string.replace(p2.stdout.readline(),'SQL>','')
				err.append(output)
				print output
				if regexp:
					#print regexp
					m = re.match(regexp, output) 
					if m:
						out.append(m.group(grp))
				else:
					self._logger.info(output.rstrip())
					

			p2out=p2.wait()
			#print ' sql status =%s' % p2out
			if p2out:
				self._logger.warning(string.join(err,'\n'))
		return (out,p2out)
	def get_ctl(self, to_tab, r_int):
		#TRAILING NULLCOLS
		#UNRECOVERABLE
		tmpl="""
OPTIONS (READSIZE=200000, ROWS=5000, BINDSIZE=200000, PARALLEL=false, direct=true, columnarrayrows=5000)
LOAD DATA
	INFILE *
	APPEND
	INTO TABLE %s
	FIELDS TERMINATED BY "|"
	TRAILING NULLCOLS
	(%s)
BEGINDATA
10-DEC-10 04.17.57.102789 PM    			|0|Dangot,Persio""" % (to_tab, string.join(r_int,','))
		return tmpl
	def get_ctl_fixed_manual(self, to_tab, r_int):
		#TRAILING NULLCOLS
		#UNRECOVERABLE
		#FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
		#INFILE '-'
		tmpl="""UNRECOVERABLE
LOAD DATA
INFILE *
APPEND
INTO TABLE MDW.DELETE_REF_PRSNL_MGR_HIER
(CRTD_TS POSITION(1:28),
FTE_DIR_RPTS POSITION(29:40),
NAM POSITION(41:219))
BEGINDATA 
10-DEC-10 04.17.57.102789 PM           0Dangot,Persio
10-DEC-10 04.17.57.102789 PM           0Dangot,Persio
10-DEC-10 04.17.57.102789 PM           0Manterola Rencher,Cristy
10-DEC-10 04.17.57.102789 PM           0Manterola Rencher,Cristy
10-DEC-10 04.17.57.102789 PM           0Devine,Dorothy K
10-DEC-10 04.17.57.102789 PM           0Devine,Dorothy K""" #% (to_tab, string.join(r_int,',\n'))
		return tmpl	
	def get_ctl_fixed(self, to_tab, r_int):
		#TRAILING NULLCOLS
		#UNRECOVERABLE
		#FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
		#INFILE '-'
		tmpl="""OPTIONS (READSIZE=200000, ROWS=5000, BINDSIZE=200000, PARALLEL=true, direct=true, columnarrayrows=5000)
UNRECOVERABLE
LOAD DATA
INFILE '-'
APPEND
INTO TABLE %s
(%s)""" % (to_tab, string.join(r_int,',\n'))
		return tmpl
	def get_q_options(self,pp):
		lame_duck=''
		if pp.has_key('LAME_DUCK') and int(pp['LAME_DUCK'])>0:
			lame_duck = "WHERE ROWNUM <= %s " % pp['LAME_DUCK']
		part=''
		if pp.has_key('PARTITION'):
			part = " PARTITION (%s) " % pp['PARTITION']
		else:
			if pp.has_key('SUBPARTITION'):
				part = " SUBPARTITION (%s) " % pp['SUBPARTITION']
		return " %s %s" % (part, lame_duck)
	def do_load(self, from_db, from_t, to_db, to_t):
		f = ""
		out=[]
		err=[]
		confirm(len(from_db)>0, 'Source login is not set.')
		confirm(len(to_db)>0, 'Target login is not set.')
			
		(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)

		if not status:
			to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			#cl =  "%s||'' " % string.join(r_int,"||'',")
			cl = "%s||'|'" % string.join(r_int,",")
			ctl=self.get_ctl(string.join(self.get_to_tab(to_t),'.'),r_int)
			#print(ctl)
			fname= 'sqlloader/%s.ctl' % to_tab
			f = open(fname, 'w')
			status = f.write(ctl)
			if status!= None:
				self._logger.error('Cannot write to %s.' % fname)
			f.close()
			q= "set head off line 7000 pages 0 echo off feedback off termout off colsep '|' feed off newpage 0 num 2\nSELECT %s FROM %s %s;" % (cl , string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			print q
			p1 = Popen(['echo', q], stdout=PIPE)
			p2 = Popen([ 'sqlplus', 'S',from_db], stdin=p1.stdout, stdout=PIPE)
			#cmd= "sqlldr control=sqlloader/ins.ctl userid=mdw/DEPOTbank@gmail.com data=\\'-\\' %s" % to_db
			#print cmd
			#args=shlex.split(cmd)
			#pprint(args)
			p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, 'rows=5000',
			'COLUMNARRAYROWS=5000','STREAMSIZE=500000','readsize=200000',' parallel=false','bindsize=200000','direct=true', #"data=\'-\'",
			'LOG=sqlloader/%s.log' % to_tab, 'BAD=sqlloader/%s.bad' % to_tab,'DISCARD=sqlloader/%s.dsc' % to_tab,'ERRORS=100'], stdin=p2.stdout, stdout=PIPE)
			output=' '
			while output:
				output = p3.stdout.readline()
				err.append(output)
				#print output
				self._logger.info(output.rstrip())
					

			status=p3.wait()
			print ' sql status =%s' % status
			if status==1:
				self._logger.warning(string.join(err,'\n'))
			else: 
				self._logger.info(string.join(err,'\n'))
		else:
			self._logger.warning('Cannot fetch common columns.')
		return (out,status)		

	def get_code(self,etl_object):
		pass
		

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
		self._logger.info(source_file)
		#sys.exit(1)
		return source_file 
	def get_template(self, etl_object, logger):
		""" Runs mist tool """
		#pprint(etl_object)
		#pprint(type(etl_object['node']['param']))
		#pprint(self._connector)
		regexp=re.compile(r'((%)([\w\_]+)(%))')
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
		#print template
		#sys.exit(1)
		return template 

	def set_params(self, etl_object, logger):
		""" Gets parameters """
		if len(self._pp)==0:
			regexp=re.compile(r'((%)([\w\_]+)(%))')
			#self._pp={}
			for param in etl_object['node']['param']:
				self._pp[param] = etl_object['node']['param'][param]['value']
				self._p[param] = etl_object['node']['param'][param]['value']
				m = re.match(regexp, etl_object['node']['param'][param]['value'])
				if m:
					confirm(not(self._process_meta.has_key(m.groups()[2]) and self._connector.has_key(m.groups()[2])), 'EXCEPTION: process_spec and connectors has the same key %s' % m.groups()[2])
					if (self._process_meta.has_key(m.groups()[2])):
						self._pp[param]=self._pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
						
					if (self._connector.has_key(m.groups()[2])):
						#print m.groups()[2]
						self._pp[param]= self.get_ora_login(self._connector[m.groups()[2]]) 
						if 0: 
							self._pp[param]= self._pp[param].replace(m.groups()[0],'%s/%s@%s' % 
													 (self._connector[m.groups()[2]]['schema'],self._connector[m.groups()[2]]['pword'],self._connector[m.groups()[2]]['sid']))
		#return self._pp
		#pprint(self._pp)
		#pprint(self._p)
	def get_ora_login(self, connector):
		if connector.has_key('type'):
			if connector['type']=='inline':
				return self.get_inline_ora_login(connector)
			else:
				self._logger.warning('Unknown connector type - assuming regular connect type.')	
		confirm(connector.has_key('pword'), 'Connector has no <pword> attribute')
		confirm(connector.has_key('schema'), 'Connector has no <schema> attribute')
		confirm(connector.has_key('sid'), 'Connector has no <sid> attribute')
		return "%s/%s@%s" %(connector['schema'], connector['pword'], connector['sid'])
		
	def get_inline_ora_login(self, connector):
		confirm(connector.has_key('type'), 'Connector has no <type> attribute')
		confirm(connector['type']=='inline', 'Undefined connector type "%s".  Expected "inline".' % connector['type'])
		confirm(connector.has_key('pword'), 'Inline Connector has no <pword> attribute')
		confirm(connector.has_key('schema'), 'Inline Connector has no <schema> attribute')
		confirm(connector.has_key('sid'), 'Inline Connector has no <sid> attribute')
		confirm(connector.has_key('HOST'), 'Inline Connector has no <HOST> attribute')
		confirm(connector.has_key('PORT'), 'Inline Connector has no <PORT> attribute')
		return "%s/%s@(DESCRIPTION = (ADDRESS_LIST = (ADDRESS = (PROTOCOL = TCP)(HOST =%s)(PORT = %s)))(CONNECT_DATA=(SID = %s)))" %(connector['schema'], connector['pword'], connector['HOST'], connector['PORT'], connector['sid'])	
				 
	def get_columns_nots(self, login, t):
		if not self._ci_nots.has_key(login):
			self._ci_nots[login]={}
			
		if len(self._ci_nots[login])==0:
			q="select  'COLUMN.'||column_name from all_tab_columns t where table_name ='%s' and owner='%s' AND data_type IN ('VARCHAR2','CHAR','DATE','LONG','NUMBER') order by column_name;" % (t[1],t[0])

			regexp=re.compile(r'.*\.([\w\_]+)\n')
			(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off\n%s" % q,0,regexp,1)

			if not status:
				if len(r)==0:
					status=2
					self._logger.warning('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*)\@', '/***@', login)))
			self._ci_nots[login]=r				
			return (r,status)
		else:
			return (self._ci_nots[login],0)

	def get_columns(self, login, t):
		if not self._ci.has_key(login):
			self._ci[login]={}
		if len(self._ci[login])==0:
			#AND data_type IN ('VARCHAR2','CHAR','DATE','LONG','NUMBER')
			q="select  'COLUMN.'||column_name from all_tab_columns t where table_name ='%s' and owner='%s'  order by column_name;" % (t[1],t[0])

			regexp=re.compile(r'.*\.([\w\_]+)\n')
			(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off\n%s" % q,0,regexp,1)
			if not status:
				if len(r)==0:
					status=2
					self._logger.warning('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*)\@', '/***@', login)))
			self._ci[login]=r	
			return (r,status)
		else:
			return (self._ci[login],0)
	def get_col_format(self, tab_tt):
		#pprint(self._cci.keys())
		#pprint(tab_tt)
		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		#pprint(tab_key)
		#login = tab_tt[0][0]
		#t=tab_tt[0][1]
		(login, t) = tab_tt[0]
		ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"','")
		#print ci
		q="select 'COL '||column_name||' FORMAT '||DECODE(data_type, 'VARCHAR2','a'||DATA_LENGTH, 'CHAR','a'||DATA_LENGTH, 'NUMBER','9999999999999999999999999999999','DATE','DATE', 'TIMESTAMP(6)','a28',  'UNDEFINED') fmt from all_tab_columns where table_name ='%s' and owner='%s' %s order by column_name;" % (t[1],t[0],ci)
		#pprint(q)
		#sys.exit(1)
		regexp=re.compile(r'[\ ]*(COL [\w \d\_]+)')
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		pprint(r)
		if not status:
			if len(r)==0:
				status=2
				self._logger.warning('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*),\@', '/***@', login)))
		return (r,status)

	def get_col_position(self, tab_tt):
		(login, t) = tab_tt[0]
		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		#column index
		ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"','")
		q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') ' q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',32,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from all_tab_columns) where table_name ='%s' and owner='%s' %s order by column_name);" % (t[1],t[0], ci)		
		#q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') '||DECODE(data_type,'VARCHAR2','CHAR', 'INTEGER','CHAR','NUMBER','INTEGER EXTERNAL','TIMESTAMP(6)','TIMESTAMP(6)', data_type) q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',11,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from all_tab_columns) where table_name ='%s' and owner='%s' %s order by column_name);" % (t[1],t[0], ci)
		self._logger.info(q)
		regexp=re.compile(r'[\ ]*([\w\d\_]+\ POSITION\(\d+\:\d+\) [\w\d\(\)]+)')
		regexp=re.compile(r'[\ ]*([\w\d\_]+\ POSITION\(\d+\:\d+\))')
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		pprint(r)
		if not status:
			if len(r)==0:
				status=2
				self._logger.warning('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*),\@', '/***@', login)))
		return (r,status)
		
	def get_select(self, login, from_t):
		(r,status) = self.get_columns(login, from_t)
		select_from = from_t
		#if to_t:
			#select_from=to_t
		out="SELECT %s FROM %s " % (string.join(r,','), string.join(select_from,'.'))
		return (out, status)
	def get_select_nots(self, login, from_t):
		(r,status) = self.get_columns_nots(login, from_t)
		select_from = from_t
		#if to_t:
			#select_from=to_t
		out="SELECT %s FROM %s " % (string.join(r,','), string.join(select_from,'.'))
		return (out, status)		
	def gt(self, tab_t):
		return string.join(tab_t, '.')
	def get_common_cols_nots(self, from_db, from_t, to_db, to_t):
		from_key = self.get_cc_key((from_db, from_t))
		to_key = self.get_cc_key( (to_db, to_t))
		if not self._cci_nots.has_key(from_key):
			self._cci_nots[from_key]={}
			self._cci_nots[from_key][to_key]={}
		if not self._cci_nots.has_key(to_key):
			self._cci_nots[to_key]={}
			self._cci_nots[to_key][from_key]={}			
		if len(self._cci_nots[to_key][from_key])==0:
			(r_from,s_from) = self.get_columns_nots(from_db, from_t)
			(r_to,s_to) = self.get_columns_nots(to_db, to_t)
			if not s_from and not s_to:
				r_int = list(set(r_from) & set(r_to))
				r_int.sort()
				self._cci_nots[to_key][from_key]=r_int
				self._cci_nots[from_key][to_key]=r_int
				return (r_int, 0)
			else:
				self._logger.warning('Cannot get column lists.')
			return (None, 1)
		else:
			return (self._cci_nots[to_key][from_key], 0)
	def get_cc_key (self, db_tab_t):
		(db, tab_t) =db_tab_t
		return "%s|%s" % (db, self.gt(tab_t))
	def get_common_cols(self, from_db, from_t, to_db, to_t):
		from_key = self.get_cc_key((from_db, from_t))
		to_key = self.get_cc_key( (to_db, to_t))
		if not self._cci.has_key(from_key):
			self._cci[from_key]={}
			self._cci[from_key][to_key]={}
		if not self._cci.has_key(to_key):
			self._cci[to_key]={}	
			self._cci[to_key][from_key]={}
		if len(self._cci[to_key][from_key])==0:	
			(r_from,s_from) = self.get_columns(from_db, from_t)
			(r_to,s_to) = self.get_columns(to_db, to_t)
			if not s_from and not s_to:
				r_int = list(set(r_from) & set(r_to))
				r_int.sort()
				self._cci[to_key][from_key]=r_int
				self._cci[from_key][to_key]=r_int
				return (r_int, 0)
			else:
				self._logger.warning('Cannot get column lists.')
			return (None, 1)	
		else:
			return (self._cci[to_key][from_key], 0)			
	def get_select_from_cols(self, l_cols, t_tab):
		out="SELECT %s FROM %s " % (string.join(l_cols,','), string.join(t_tab,'.'))
		return out	

	def get_select_p(self, login, from_t, to_t=None):
		(r,status) = self.get_columns_nots(login, from_t)
		select_from = from_t
		if to_t:
			select_from=to_t
		out="SELECT %s FROM %s " % (string.join(r,','), string.join(select_from,'.'))
		return (out, status)
	def get_connector(self, key):
		#print key
		clean = str.strip(str(key),'%')
		confirm(self._connector.has_key(clean), 'Connector %s does not exists.' % clean)
		return self._connector[clean]

	def get_tmpl_batch(self, etl_object, logger):
		""" Parse template to list of tables """
		
		tmpl = self.get_template(etl_object, logger)
		#pprint(self._pp)
		#pprint(tmpl)
		regexp=re.compile(r'([\w\_]+)\.([\w\_]+)')
		template={}
		trunc_batch ={}
		m = re.findall(regexp, tmpl)
		#pprint(self._connector)
		conn=self._connector
		pp=self._pp
		confirm(pp.has_key('FROM_DB'),'FROM_DB is not defined')
		confirm(pp.has_key('TO_DB'),'TO_DB is not defined')
		
		#sys.exit(1)
		if m:
			#pprint(m)
			for t in m:
				from_t=list(t)
				to_t=list(t)
				to_t=self.get_to_tab(to_t)
				from_t=self.get_from_tab(from_t)
				#print to_t, from_t
				
				#pprint(pp)
				#print(t)
				#sys.exit(1)
				from_db = pp['FROM_DB']
				#pprint(from_db)
				to_db= pp['TO_DB']
				#print from_db, to_db
				to_tab= string.join(to_t,'.')
				to_view= string.join(to_t,'.v_')				
				from_tab=string.join(from_t,'.')

				if 0:
					#(q_to,to_status)=self.get_select(to_db,from_t, to_t)
					(q_to,to_status)=self.get_select_nots(to_db, to_t)
					#print 'to ', q_to,to_status
					(q_from,from_status)=self.get_select_nots(from_db,from_t)
					#print 'from ', q_from,from_status
				if 1:
					(r_int, status)=self.get_common_cols_nots(from_db, from_t, to_db, to_t)

					
				if not status:
					q_to = self.get_select_from_cols( r_int, to_t)
					q_from = self.get_select_from_cols( r_int, from_t)
					lame_duck=''
					if pp.has_key('LAME_DUCK') and int(pp['LAME_DUCK'])>0:
						lame_duck = "WHERE ROWNUM <= %s " % pp['LAME_DUCK']
					part=''
					if pp.has_key('PARTITION'):
						part = " PARTITION (%s) " % pp['PARTITION']
					else:
						if pp.has_key('SUBPARTITION'):
							part = " SUBPARTITION (%s) " % pp['SUBPARTITION']
					bucket=''
					if pp.has_key('BUCKET_ID'):
						bucket = " AND ora_hash(GFCID||CUST_NAM,2)=%s " % pp['BUCKET_ID']							
					cp_tmpl=  'set timing on echo on arraysize %s copycommit %s\nCOPY %s INSERT %s USING %s %s %s\n exit;' % (pp['ARRAYSIZE'],pp['COPYCOMMIT'],self.get_copy_q(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB'])), to_view, q_from, part,lame_duck )
					#cp_tmpl=  'set timing on echo on arraysize %s copycommit %s\nCOPY %s INSERT %s USING %s WHERE 1=1 %s \n exit;' % (pp['ARRAYSIZE'],pp['COPYCOMMIT'],self.get_copy_q(conn[pp['FROM_DB']],conn[pp['TO_DB']]), to_view, q_from, bucket)
					
					#print re.sub('\/(.*)\@', '/***@', cp_tmpl)
					template[from_tab]={}
					template[from_tab]['INSERT'] = cp_tmpl
					template[from_tab]['TRUNCATE'] ="TRUNCATE TABLE %s;\nexit;" % to_tab
					template[from_tab]['VIEW'] ="CREATE OR REPLACE VIEW %s.v_%s AS %s;\nexit;" % (to_t[0],to_t[1], q_to)
				else:
					logger.warning('Failed to create code templates.')

		return (template, status)

	def get_tmpl_batch_fixed(self, etl_object, logger):
		""" Parse template to list of tables """
		
		tmpl = self.get_template(etl_object, logger)
		#pprint(self._pp)
		#pprint(tmpl)
		regexp=re.compile(r'([\w\_]+)\.([\w\_]+)')
		template={}
		trunc_batch ={}
		m = re.findall(regexp, tmpl)
		#pprint(self._connector)
		conn=self._connector
		pp=self._pp
		confirm(pp.has_key('FROM_DB'),'FROM_DB is not defined')
		confirm(pp.has_key('TO_DB'),'TO_DB is not defined')
		
		#sys.exit(1)
		if m:
			#pprint(m)
			for t in m:
				from_t=list(t)
				to_t=list(t)
				to_t=self.get_to_tab(to_t)
				from_t=self.get_from_tab(from_t)
				#print to_t, from_t
				
				#pprint(pp)
				#print(t)
				#sys.exit(1)
				from_db = pp['FROM_DB']
				#pprint(from_db)
				to_db= pp['TO_DB']
				#print from_db, to_db
				to_tab= string.join(to_t,'.')
				to_view= string.join(to_t,'.v_')				
				from_tab=string.join(from_t,'.')

				if 0:
					#(q_to,to_status)=self.get_select(to_db,from_t, to_t)
					(q_to,to_status)=self.get_select(to_db, to_t)
					#print 'to ', q_to,to_status
					(q_from,from_status)=self.get_select(from_db,from_t)
					#print 'from ', q_from,from_status
				if 1:
					(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)

					
				if not status:
					q_to = self.get_select_from_cols( r_int, to_t)
					q_from = self.get_select_from_cols( r_int, from_t)
					lame_duck=''
					if pp.has_key('LAME_DUCK') and int(pp['LAME_DUCK'])>0:
						lame_duck = "WHERE ROWNUM <= %s " % pp['LAME_DUCK']
					part=''
					if pp.has_key('PARTITION'):
						part = " PARTITION (%s) " % pp['PARTITION']
					else:
						if pp.has_key('SUBPARTITION'):
							part = " SUBPARTITION (%s) " % pp['SUBPARTITION']
					bucket=''
					if pp.has_key('BUCKET_ID'):
						bucket = " AND ora_hash(GFCID||CUST_NAM,2)=%s " % pp['BUCKET_ID']							
					cp_tmpl=  'set timing on echo on arraysize %s copycommit %s\n %s %s %s\n exit;' % (pp['ARRAYSIZE'],pp['COPYCOMMIT'], q_from, part,lame_duck )
					#cp_tmpl=  'set timing on echo on arraysize %s copycommit %s\nCOPY %s INSERT %s USING %s WHERE 1=1 %s \n exit;' % (pp['ARRAYSIZE'],pp['COPYCOMMIT'],self.get_copy_q(conn[pp['FROM_DB']],conn[pp['TO_DB']]), to_view, q_from, bucket)
					
					#print re.sub('\/(.*)\@', '/***@', cp_tmpl)
					template[from_tab]={}
					template[from_tab]['SELECT'] = cp_tmpl
					template[from_tab]['TRUNCATE'] ="TRUNCATE TABLE %s;\nexit;" % to_tab
					#template[from_tab]['VIEW'] ="CREATE OR REPLACE VIEW %s.v_%s AS %s;\nexit;" % (to_t[0],to_t[1], q_to)
				else:
					logger.warning('Failed to create fixed code templates.')

		return (template, status)		
	def get_copy_q(self, from_db, to_db):
		if self.is_inline(to_db):
			return 'FROM %s ' % (self.get_ora_login(from_db))
		if self.is_inline(from_db):
			return 'TO %s ' % (self.get_ora_login(to_db))
		return 'FROM %s TO %s' % (self.get_ora_login(from_db),self.get_ora_login(to_db))
	def save_sh_template(path):
		f = open(path, 'w')
	def get_sh_template(self, tmpl):
		#pprint(tmpl)
		for sql_tmpl_key in tmpl:
			self.sh_tmpl=self.sh_tmpl.replace("$%s$" % sql_tmpl_key, tmpl[sql_tmpl_key])
		return self.sh_tmpl
	def save_sh_code(self,tmpl):
		sh_path=tmpl['SH_PATH']
		#print sh_path
		f=open(sh_path,"w");
		f.write(tmpl['SH_CODE'])
		f.close()
		


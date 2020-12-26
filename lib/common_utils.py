#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all hierarchy transformation routines
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
from datetime import date, timedelta
import types, pickle
import Queue
#import threading
#import urllib2
import time
import tempfile
from app_utils import app_utils

STACKTRACE_MAX_DEPTH = 2



class sql_utils(app_utils):
	"""A class for hierarchy maintenance."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)



	def do_query(self, login, query, query_file=None, regexp=None, grp=None, spset=''):
		f = ""
		out=[]
		err=[]
		ora_err =False
		errpos=-1
		pstatus=0
		status=0
		#errreg=re.compile(r'.*(ERROR).*')
		assert  len(login)>0, 'Default login is not set.'
		show=False
		if type(login) == types.TupleType:
			to_tab=login[1]
			login=login[0]
			#query = string.replace ()
			#sys.exit(1)
		else:
			pass
		if 1:			
			#from subprocess import Popen, PIPE
			q=''
			opt=''
			if self.p_if('IF_SHOW_SERVEROUTPUT'):
				opt='set serveroutput on echo on termout on feedback on'
				show =True
			if query_file:
				q = "%s\n%s\n@%s" % ( spset,opt,query_file)
				#q = "%s\nset autotrace on page 3 timing on echo on serveroutput on\n%s\n%s" % ('-'*20, query,'-'*20) 
			else:		

				q = "%s\n%s\n%s" % ( spset,opt,query)
			
			#self._logger.info(login)
			self._logger.sql(q)
			#print q
			p1 = Popen(['echo', q], stdout=PIPE,stderr=PIPE)
			p2 = Popen([ 'sqlplus', "-s", login], stdin=p1.stdout, stdout=PIPE,stderr=PIPE)
			output=' '
			status=0
			while output:
				output = string.replace(p2.stdout.readline(),'SQL>','')
				#print output
				#err.append(output)
				if regexp:
					#print regexp
					m = re.match(regexp, output) 
					if m:
						if grp:
							out.append(m.group(grp))
						else:
							groups=m.groups()
							if groups:
								if groups[0]:
									out.append(groups)
							self._logger.info(output.rstrip())
						#else out.append(m.group(grp))
				else:
					out.append(output)
					if show:
						#print output,
						self._logger.info(output.rstrip())	
				if errpos>-1:
					self._logger.error(output.rstrip())	
					status=1					
				#errpos=output.find('ERROR') 
				#print  output.find('2COLUMN.')
				if output.find('COLUMN.')==-1:
					errpos=output.find('ERROR ')
					#print "%s, %s ,%s" % (errpos, output, output.find('COLUMN.'))
					if errpos>-1:
						status=1
						
						#self._logger.error(output.rstrip())	
					
			pstatus=p2.wait()
			er='none.'
			if pstatus:
				while er:
					er = p2.stderr.readline()
					if er:
						print 'P2-ERROR: ',er
				
			if int(status)+int(pstatus)>0:
				print 'error', status,pstatus
				self._logger.error(string.join(err,'\n'))	
			if status!=0:
				return (err,status)
		#print "====================", out,status
		return (out,status+pstatus)		
	def dml(self, etl_object, logger):
		""" Runs mist tool """
		self.set_params(etl_object, logger)
		template = self.get_template(etl_object, logger)
		if not self._default_login:
			#print "================="
			#pprint(self._pp)
			#sys.exit(1)
			if self._pp.has_key('DB_CONNECTOR'):
				self._default_login=self.get_ora_login(self.get_connector(self._p['DB_CONNECTOR']))
			else: 
				if self._pp.has_key('DB_INLINE_CONNECTOR'):
					self._default_login=self.get_ora_login(self.get_connector(self._p['DB_INLINE_CONNECTOR']))
		assert self._default_login, 'DB_CONNECTOR is not set.'		
		status=1
		if template:
			#print self._default_login, template
			
			regexp=re.compile(r'.*')
			(r,status) = self.do_query(self._default_login, template,0,regexp)
			
		else:
			
			assert self.is_set('TEMPLATE_LOC'),'Template file is not set'
			(r,status) = self.do_query(self._default_login, None, self._pp['TEMPLATE_LOC'])
			
		self._logger.info("DML [%s] finished with status=%s." % (etl_object['name'],status))
		return status	
		

	def get_q_stats(self,etl_object, q, out,status, worker_sec=None,logger=None):
		""" Get query stats depending on type 
		select slice, col, num_values, minvalue, maxvalue from diskusage where name = 'test_log3' and col=0 order by slice, col;

drop table smart_test_log;
create table smart_test_log(id int IDENTITY distkey, etlflow varchar(128),etlflow_descr varchar(256),worker varchar(64), elapsed_sec numeric(19,8), 
psql_status int,descr varchar(128),log_id varcahr(32), query varchar(4000),pipeline_spec varchar(256),client varchar(256),created_dt timestamp default getdate());

CREATE TABLE smart_test_log (
    id int IDENTITY distkey,
    etlflow character varying(128),
    etlflow_descr character varying(256),
    worker character varying(64),
    elapsed_sec numeric(19,8),
    psql_status integer,
    descr character varying(128),
    query character varying(65535),
    pipeline_spec character varying(256),
    client character varying(256),
    created_dt timestamp without time zone default getdate(),
    log_id character varying(64),
    num_rows integer,
    count_star bigint
)
DISTSTYLE KEY
SORTKEY ( id );

insert into smart_test_log (test_name) VALUES ( 'DUMMY');

SELECT etlflow,worker,elapsed_sec,etlflow_sec,worker_sec, num_rows,count_star,created_dt, log_id from public.smart_test_log order by log_id  desc, etlflow,worker desc

		"""
		t_r=None
		#pprint(out)
		elt=0
		rows='null'
		cs='null'
		err_msg=''
		stts='OK'
		oln=''
		if status==0:
			if q.strip().upper().startswith('SELECT COUNT(*)'):
				oln= string.join(map(lambda x: x[0], out),'|')
				#pprint(oln)
				t_r =  re.findall(r'(\d+)\|cnt|Time\: (\d+\.\d+) ms', oln)
				#pprint(t_r)
				#sys.exit(1)
				if len(t_r)>1:
					elt=round(float(t_r[2][1])/1000,2)
					if t_r[1][0]:
						cs=t_r[1][0]
					rows=1
					msg ="######## Rows: 1, Elapsed: %s sec, count: %s ######## " %(elt,cs)
					#print msg
					print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))
					self._logger.sql(msg)
					#ins = "insert into smart_test_log (pipelne,worker) VALUES ( '%s','%s');" % (self.pipeline_name,etl_object['name'])
					#print ins
				#return t_r
			else:		
				if q.strip().upper().startswith('SELECT'):
					#pprint (out)
					oln= string.join(map(lambda x: x[0], out),'|')
					#pprint(oln)
					t_r =  re.findall(r'\((\d+) rows?\)|Time\: (\d+\.\d+) ms', oln)
					#pprint(t_r)
					#sys.exit(1)
					if len(t_r)>1:
						elt=round(float(t_r[2][1])/1000,2)
						if t_r[1][0]:
							rows =t_r[1][0]
						msg ="######## Rows: %s, Elapsed: %s sec ######## " %(rows,elt)
						#print msg
						print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))
						self._logger.sql(msg)
						#ins = "insert into smart_test_log (pipelne,worker) VALUES ( '%s','%s');" % (self.pipeline_name,etl_object['name'])
						#print ins
					#return t_r
				else:
					if q.strip().upper().startswith('UNLOAD') or q.strip().upper().startswith('COPY') or q.strip().upper().startswith('--UNLOAD') or q.strip().upper().startswith('--COPY'):
						#pprint(q)
						#pprint(out)
						oln= string.join(map(lambda x: x[0], out),'|')
						#pprint(oln)
						t_r =  map(lambda x: float(x),re.findall(r'Time\: (\d+\.\d+) ms', oln))
						if len(t_r)>1:
							elt = self.get_max_time(t_r)
							msg ="######## Elapsed: %s sec ######## " %(elt)
							self._logger.sql(msg)
							print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))		
							#ins = "insert into smart_test_log (pipelne,worker, elapsed_sec) VALUES ( '%s','%s',%s);" % (self.pipeline_name,etl_object['name'],elt)
							#print ins
						#return t_r
					else:
						if q.strip().upper().startswith('DROP') or q.strip().upper().startswith('CREATE') or q.strip().upper().startswith('TRUNCATE') or q.strip().upper().startswith('--ELAPSED_SUM') :
							
							oln= string.join(map(lambda x: x[0], out),'|')
							#pprint(oln)
							t_r =  map(lambda x: float(x),re.findall(r'Time\: (\d+\.\d+) ms', oln))
							if len(t_r)>1:
								elt = round(sum(t_r)/1000,2)
								msg ="######## Elapsed: %s sec or %s min ######## " %(elt, round(elt/60,2))
								self._logger.sql(msg)
								print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))		
								#ins = "insert into smart_test_log (pipelne,worker, elapsed_sec) VALUES ( '%s','%s',%s);" % (self.pipeline_name,etl_object['name'],elt)
								#print ins
							#return t_r
				
						else:
							#pprint(q)
							oln= string.join(map(lambda x: x[0], out),'|')
							#pprint(oln)
							t_r =  map(lambda x: float(x),re.findall(r'Time\: (\d+\.\d+) ms', oln))
							#pprint(t_r)
							if len(t_r)>1:
								elt = self.get_max_time(t_r)
								msg ="######## Elapsed: %s sec ######## " %(elt)
								self._logger.sql(msg)
								print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))
		else:
			if len(out)>0:
				err_msg = out[0]
				stts='ERROR'
		descr = self.get_p('DESCR')
		etl_descr = self.get_p('ETLFLOW_DESCR')
		efsec =self._logger.getElapsedSec()
		#err_msg = out[0]
		#sys.exit(1)
		wsec= float(worker_sec.seconds)+ float(worker_sec.microseconds/1000)/1000
		ins = """insert into smart_test_log (etlflow,etlflow_descr,worker, elapsed_sec,psql_status,descr,log_id,query,
				pipeline_spec,client, num_rows, count_star, etlflow_sec, worker_sec, err_msg, status, shell_log2) 
				VALUES ( '%s','%s','%s',%s,%s,'%s','%s','%s','%s','%s',%s,%s, %s,%s,'%s','%s','%s');\n""" % (self.pipeline_name,etl_descr,etl_object['name'],elt,status,descr,logger.timestamp_string,q.replace("'","''"),self._environment._pipeline_flags.pipeline,self._environment._pipeline_flags.pipeline_spec, rows, cs,efsec, wsec,err_msg, stts, oln.replace("'","''"))
		#print ins		
		return (t_r, ins)	

		

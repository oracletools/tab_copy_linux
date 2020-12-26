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
from core_utils import utils

STACKTRACE_MAX_DEPTH = 2



class log_utils(utils):
	"""A class for hierarchy maintenance."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def save_exec_log(self,etl_object, template, out,status, worker_sec=None,logger=None):
		if not logger:
			logger=self._logger
		t_r, ins =self.get_q_stats(etl_object, template, out,status,worker_sec, logger)
		if not self.p_if('IF_ASYNC_LOG'):

			#print ins
			#log elapsed time

			
			ins_ok = 'INSERT 0 1'
			ins_ok = '.*'
			(out,status,err) = self.do_query(self._default_login, ins,0,('(%s)' % ins_ok,))
			if status>0:
				self._logger.warn('Insert failed for worker %s[%s] with status %s.' %(self.pipeline_name,etl_object['name'],status));
			else: 
				#pprint(out)
				if  len(out)==0 or ( not out[0][0]==ins_ok):
						self._logger.warn('Elapsed time log failed for worker %s[%s]' %(self.pipeline_name,etl_object['name']));
		else:
			#print 'Saving logs.----------------------------'
			#print ins
			self._logger.ins(ins);
			#self._logger.warn(ins);
			self._logger.info('Skipping log insert.');


	

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

		
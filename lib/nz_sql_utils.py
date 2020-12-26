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

#from google3.dbutils.datawarehouse.etlv2.driver.utils import fileutil_wrapper
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

class nzsql(threading.Thread):
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
		self._result=[]
		self._global_result=[]
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
		self._native_client = '/opt/netezzaClient/bin/nzsql'
		threading.Thread.__init__ ( self )	
	def export(self):
		return ('DLL_LOAD_STATUS',self._result)		
	def publish_ddl(self, etl_object, logger):
		print 'Executing NZ publisher'
		#pprint(self._global_result)
		for dfn in self._global_result['DDL_LOC']:
			#print dfn
			confirm(os.path.exists(dfn),"File does not exsits.")
			confirm(os.access(dfn, os.R_OK), "Cannot read file.")
			f=open(dfn,"r")
			tmpl=f.read()
			rx= re.compile( r'(PACKAGE)')		
			tmpl = rx.sub( 'PROCEDURE', tmpl)
			rx= re.compile( r'("CSMARTBSER"\.)')		
			tmpl = rx.sub( ' ', tmpl)
			print tmpl
			self.set_template(etl_object,tmpl)
			#pprint(etl_object)
			#sys.exit(1)
			self.nzsql_dml(etl_object, logger)
		return 0
		
	def set_template(self,etl_object, template):
		""" Sets sql_template """
		confirm(etl_object, "etl_object is not set.")
		etl_object['node']['sql_template']={}
		etl_object['node']['sql_template']['data']=template
		

	def set(self, etl_object):
		self._etl_object=etl_object
		if len(self._pp)==0:
			self.set_params(etl_object, self._logger)
	def get_ora_login(self, connector):
		if connector.has_key('type'):
			if connector['type']=='inline':
				return self.get_inline_ora_login(connector)
			else:
				self._logger.warning('Unknown connector type - assuming regular connect type.')	
		self.confirm(connector.has_key('pword'), 'Connector has no <pword> attribute')
		self.confirm(connector.has_key('schema'), 'Connector has no <schema> attribute')
		self.confirm(connector.has_key('sid'), 'Connector has no <sid> attribute')
		return "%s/%s@%s" %(connector['schema'], connector['pword'], connector['sid'])			
	def confirm(self,test, testname = "Test"):
		if not test:
			msg=  "Failed: " + testname
			raise Exception( '%s (%s)' % (msg, test) )			
	def get_spec(self, key):
		return self._environment.get_process_spec(key)
	def run_depr(self):
		"""deprecated

		Args:
		  etl_object: table XML object from etlmeta
		"""
		#pprint(self._etl_object)
		#sys.exit(1)
		confirm(self._etl_object['attr'].has_key('method'),
				'copy method is not defined in %s.%s' %( __name__,self.__class__.__name__))
		#pprint(self._etl_object)
		method = self._environment.get_env_attr(string.strip(self._etl_object['attr']['method'], '%'))
		#method = self._environment.get_env_attr(self._etl_object['attr']['method'])

		_exec = 'self.%s(self._etl_object,self._logger)' % (method)
		if 1:
			exec _exec


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
	def dml(self, etl_object, logger):
		""" Runs mist tool """
		self.set_params(etl_object, logger)
		template = self.get_template(etl_object, logger)
		#sys.exit(1)
		if not self._default_login:
			#print "================="
			#pprint(self._pp)
			#sys.exit(1)
			if self._pp.has_key('DB_CONNECTOR'):
				self._default_login=self.get_ora_login(self.get_connector(self._p['DB_CONNECTOR']))
			else: 
				if self._pp.has_key('DB_INLINE_CONNECTOR'):
					self._default_login=self.get_ora_login(self.get_connector(self._p['DB_INLINE_CONNECTOR']))
		if template:
			#print self._default_login, template
			(r,status) = self.do_query(self._default_login, template,0)
		self._logger.info("DML finished with status=%s." %s)
		return status
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
		
	def get_dml(self,etl_object):
		return etl_object['node']['sql_template']['data']
	def set_dml(self,etl_object, dml):
		etl_object['node']['sql_template']['data'] =dml
	def get_q_rx(self, q):
		""" Get regexp depending on type of the query """
		#print '>>>>>>>>>>>>>>>>>>  ', q.strip().upper()
		if q.strip().upper().startswith('TRUNCATE'):
			return (r'(TRUNCATE TABLE and COMMIT TRANSACTION|Elapsed time\: (\d+)m([0-9\.]+)s)',)	
		if q.strip().upper().startswith('SELECT COUNT(*)'):
			return (r'(.*)',)		
		if q.strip().upper().startswith('SELECT'):
			return (r'(\(\d+ rows?\)|Elapsed time\: (\d+)m([0-9\.]+)s|ERROR|Server closed the connection unexpectedly\.)',)
		if q.strip().upper().startswith('UNLOAD') or q.strip().upper().startswith('COPY') or q.strip().upper().startswith('--UNLOAD') or q.strip().upper().startswith('--COPY'):
			return (r'(\(\d+ rows?\)|Elapsed time\: (\d+)m([0-9\.]+)s|COPY|UNLOAD)',)
		if q.strip().upper().startswith('DROP') or q.strip().upper().startswith('CREATE'):
			return (r'(.*)',)			
		return (r'(\(\d+ rows?\)|Elapsed time\: (\d+)m([0-9\.]+)s|\w+)',)
	def get_header(self, etl_object, ln):
		eon = etl_object['name']
		pln=(ln-1-len(eon))/2-1
		return '\n%s %s %s\n'% ('#'*int(pln), eon, '#'*int(pln+1))
	def get_max_time(self,l):
		return round(float(max(l))/1000,2)
	def get_q_stats(self,etl_object, q, out,status, worker_sec=None,logger=None):
		""" Get query stats depending on type 
		select slice, col, num_values, minvalue, maxvalue from diskusage where name = 'test_log3' and col=0 order by slice, col;

drop table smart_test_log;
create table smart_test_log(id int IDENTITY distkey, etlflow varchar(128),etlflow_descr varchar(256),worker varchar(64), elapsed_sec numeric(19,8), 
psql_status int,descr varchar(128),log_id varcahr(32), query varchar(4000),pipeline_spec varchar(256),client varchar(256),created_dt timestamp default getdate());

CREATE TABLE smart_test_log (
    id integer  NOT NULL,
    etlflow character varying(128),
    etlflow_descr character varying(256),
    worker character varying(64),
    elapsed_sec numeric(18,2),
    psql_status integer,
    descr character varying(128),
    query character varying(48000),
    pipeline_spec character varying(256),
    client character varying(256),
    created_dt timestamp DEFAULT now(),
    log_id character varying(64),
    num_rows integer,
    count_star bigint,
    etlflow_sec numeric(18,2),
    worker_sec numeric(18,2),
    err_msg character varying(256),
    status character varying(16) DEFAULT 'OK',
    shell_log character varying(10000)
);

insert into smart_test_log (ID) VALUES ( NEXT VALUE FOR s_stl_log);

CREATE TABLE small_int_table (col1 smallint);
CREATE SEQUENCE s_stl_log as bigint;
INSERT INTO small_int_table SELECT NEXT VALUE FOR s_stl_log;

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
				print  '||||||||||'
				oln= string.join(map(lambda x: x[0], out),'|')
				#pprint(oln)
				t_r =  re.findall(r'(\d+)\|cnt|Elapsed time\: (\d+)m([0-9\.]+)s', oln)
				pprint(t_r)
				#sys.exit(1)
				if len(t_r)>1:
					elt=round(float(t_r[1][1])*60+float(t_r[1][2]),2)
					if t_r[0][0]:
						cs=t_r[0][0]
					rows=1
					msg ="######## Rows: 1, Elapsed: %s sec, count: %s ######## " %(elt,cs)
					print msg
					print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))
					self._logger.sql(msg)
					#ins = "insert into smart_test_log (pipelne,worker) VALUES ( '%s','%s');" % (self.pipeline_name,etl_object['name'])
					#print ins
				#return t_r
			else:		
				if q.strip().upper().startswith('SELECT'):
					pprint (out)
					oln= string.join(map(lambda x: x[0], out),'|')
					pprint(oln)
					t_r =  re.findall(r'\((\d+) rows?\)|Elapsed time\: (\d+)m([0-9\.]+)s', oln)
					pprint(t_r)
					#sys.exit(1)
					if len(t_r)>1:
						elt=round(float(t_r[1][1])*60+float(t_r[1][2]),2)
						if t_r[0][0]:
							rows=t_r[0][0]
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
						pprint(oln)
						t_r =  map(lambda x: float(x),re.findall(r'Elapsed time\: (\d+)m([0-9\.]+)s', oln))
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
							t_r =  map(lambda x: float(x),re.findall(r'Elapsed time\: (\d+)m([0-9\.]+)s', oln))
							if len(t_r)>1:
								elt = round(sum(t_r)/1000,2)
								msg ="######## Elapsed: %s sec or %s min ######## " %(elt, round(elt/60,2))
								self._logger.sql(msg)
								print self.get_header(etl_object,len(msg)), '%s\n' % msg, '%s\n'% ('#'*(len(msg)-1))		
								#ins = "insert into smart_test_log (pipelne,worker, elapsed_sec) VALUES ( '%s','%s',%s);" % (self.pipeline_name,etl_object['name'],elt)
								#print ins
							#return t_r
				
						else:
							pprint(q)
							oln= string.join(map(lambda x: x[0], out),'|')
							pprint(oln)
							t_r =  map(lambda x: float(x),re.findall(r'Elapsed time\: (\d+)m([0-9\.]+)s', oln))
							pprint(t_r)
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
		ins = """insert into smart_test_log (id,etlflow,etlflow_descr,worker, elapsed_sec,psql_status,descr,log_id,query,
				pipeline_spec,client, num_rows, count_star, etlflow_sec, worker_sec, err_msg, status, shell_log) 
				VALUES ( NEXT VALUE FOR s_stl_log, '%s','%s','%s',%s,%s,'%s','%s','%s','%s','%s',%s,%s, %s,%s,'%s','%s','%s');\n""" % (self.pipeline_name,etl_descr,etl_object['name'],elt,status,descr,logger.timestamp_string,q.replace("'","''"),self._environment._pipeline_flags.pipeline,self._environment._pipeline_flags.pipeline_spec, rows, cs,efsec, wsec,err_msg, stts, oln.replace("'","''"))
		#print ins		
		return (t_r, ins)	
	def nzsql_dml(self, etl_object, logger):
		""" Executes DML using SQL*Plus """
		self.set_params(etl_object, logger)

		template = self.get_template(etl_object, logger)
		#pprint(template)
		#(tmpl_batch, status) = self.get_tmpl_batch(etl_object, logger)

		#confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		#pprint((self._pp))
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']
		#pprint(etl_object)
		#sys.exit(0)
		err=[]
		out=[]
		if 0:
			pass
		else:
			#self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			schema_name=self._pp['SCHEMA_NAME']
			#to_db= self._pp['TO_DB'] 
			if self.p_if('IF_TOSS_CACHE'):
				pass 
				#(out,status,err) = self.do_nz_query(self._default_login, "xpx 'toss_cache';\n",0,('.*',)) 
			
			logger.info('#### START of PADB dml %s.' % etl_object['name'])
			regexpt= self.get_q_rx(template)
			print regexpt
			a_t = datetime.datetime.now()
			(out,status,err) = self.do_nz_query(self._default_login, template,0,regexpt)
			worker_sec = datetime.datetime.now()-a_t

			#oln= string.join(map(lambda x: x[0], out),'|')
			#t_r =  re.findall(r'\((\d+) rows?\)\|Time\: (\d+\.\d+) ms', oln)
			logger.info('#### END of dml %s.' % etl_object['name'])
					
			if status==0:
				self.save_nz_log(etl_object, template, out,status, worker_sec,logger)
			else:
				self.save_nz_log(etl_object, template, err,status, worker_sec,logger)
				
			if status==0:
				logger.info("#### PADB DML of %s finished successfully." % etl_object['name'])
			else:
				logger.warning('PADB DML failed for %s.' % etl_object['name'])


			self.cleanup()		
			#sys.exit(0)
		if self._pp.has_key('EMAIL_TO') and 0:
			#confirm(self._process_meta[string.strip(self._pp['EMAIL_TO'],'%')], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._pp['EMAIL_TO'],tab )

		return status
	def save_nz_log(self,etl_object, template, out,status, worker_sec=None,logger=None):
		if not logger:
			logger=self._logger
		t_r, ins =self.get_q_stats(etl_object, template, out,status,worker_sec, logger)
		if not self.p_if('IF_ASYNC_LOG'):

			#print ins
			#log elapsed time

			
			ins_ok = 'INSERT 0 1'
			(out,status,err) = self.do_nz_query(self._default_login, ins,0,('(%s)' % ins_ok,))
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
		
	def sql_plus_ddl(self, etl_object, logger):
		""" Executes DML using SQL*Plus """
		self.set_params(etl_object, logger)
		stmpl = self.get_dml(etl_object)
		logger.sql(stmpl)
		regexp=re.compile(r'\;')
		m = re.split(regexp, stmpl.strip())
		sql=[]
		if m:
			#pprint(m)
			for t in m:
				#logger.info(">>%s||%d" % (t, len(t)))
				if len(t):
					sql.append("EXECUTE IMMEDIATE '%s'" % t.strip('\n').strip().replace("'","''"))
		#pprint(sql)

		q="""--%%WORKER_NAME%%
set timing on serveroutput on
DECLARE v_row_cnt INT;	
time1 NUMBER;
v_elapsed NUMBER;
	BEGIN	
	time1:=dbms_utility.get_time;
	BEGIN
	%s;
	v_elapsed:=(dbms_utility.get_time-time1) /100;
	v_row_cnt:=SQL%%ROWCOUNT;
	p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%') ;
	EXCEPTION
	WHEN OTHERS THEN
		v_elapsed:=(dbms_utility.get_time-time1) /100;
		v_row_cnt:=SQL%%ROWCOUNT;
		p('ERROR: '||SQLCODE||'; '||SQLERRM);
		p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%', SQLCODE, SQLERRM) ;
		RAISE;
	END;
p('time elapsed: ' || (dbms_utility.get_time-time1) /100||'; rows updated: ' || v_row_cnt);
COMMIT;
END;
/
			"""	% string.join(sql,';\n')
		self.set_dml(etl_object,q)
		template = self.get_template(etl_object, logger)
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']
		if 0:
			pass
		else:
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			schema_name=self._pp['SCHEMA_NAME']
			logger.info('#### START of dml %s.' % etl_object['name'])
			regexp=re.compile(r'((\d+) rows updated\.)|(Elapsed: (\d+:\d+:\d+\.\d+))')
			(out,status) = self.do_query(self._default_login, template,0,regexp)
			logger.info('#### END of dml %s.' % etl_object['name'])
			if len(out)>1:
				logger.sql("#### Updated: %s, Elapsed: %s #### " %(out[0][1],out[1][3]))
			if status==0:
				logger.info("#### SQL*Plus DML of %s finished successfully." % etl_object['name'])
			else:
				logger.warning('SQL*Plus DML failed for %s.' % etl_object['name'])
			self.cleanup()		
			#sys.exit(0)
		if self._pp.has_key('EMAIL_TO') and 0:
			#confirm(self._process_meta[string.strip(self._pp['EMAIL_TO'],'%')], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._pp['EMAIL_TO'],tab )

		return status

	def show_ddl(self, etl_object, logger):
		""" Executes DML using SQL*Plus """
		#pprint(etl_object)
		#sys.exit(0)
		onerror ='RAISE;'
		if etl_object['attr'].has_key('onerror'):
			if etl_object['attr']['onerror'] !='RAISE':
				onerror ="p(v_worker||'Passing the error.');"
		self.set_params(etl_object, logger)
		stmpl = self.get_dml(etl_object)
		stmpl= re.sub(r'= 2011', '= vyear_num', stmpl, re.IGNORECASE)
		stmpl= re.sub(r'= 2', '= vmnth_num', stmpl, re.IGNORECASE)
		stmpl= re.sub(r'WAIT 100', 'WAIT vwait_sec', stmpl, re.IGNORECASE)
		
		#stmpl=stmpl.replace('proc_year = 2011','proc_year = vyear_num').replace('proc_mnth = 2','proc_mnth = vmnth_num').replace('fisc_yr = 2011','fisc_yr = vyear_num').replace('actg_prd = 2','actg_prd = vmnth_num')
		logger.sql(stmpl)
		if 1:
			#update cva_basel_rules_ab
			qo= etl_object['name'][:3]
			colid = None
			if 'DROP' in etl_object['name'] or 'UPDATE' in etl_object['name']:
				colid ='1'
			if 'CREATE' in etl_object['name']:
				colid = '3'				
			if 'LOCK' in etl_object['name']:
				colid = '4'
			u=""" 
UPDATE CVA_BASEL_RULES_AB SET DML_QUERY_%s='%s' 
 WHERE  proc_year = 2011
		and proc_mnth = 2
		and rule_category like 'BASEL%%'
		and RULE_STATUS = 'A'
		and query_order is not null
		and query_order=%s;
COMMIT;			""" % (colid,stmpl.strip().rstrip('/').replace("'","''"),qo)
			print(u)
			#print('LOCK' in etl_object['name'])
			self.set_dml(etl_object,u)
			status = self.sql_plus_dml(etl_object,logger)
			print "update status: %s" % status
			
		regexp=re.compile(r'\;')
		m = re.split(regexp, stmpl.strip())
		sql=[]
		if m:
			#pprint(m)
			for t in m:
				#logger.info(">>%s||%d" % (t, len(t)))
				if len(t):
					sql.append("EXECUTE IMMEDIATE '%s'" % t.strip('\n').strip().replace("'","''"))	


		plq="""/*%%WORKER_NAME%% test*/
DECLARE v_row_cnt INT;	
time1 NUMBER;
v_elapsed NUMBER;
v_worker VARCHAR2(128):='%%PROJECT_NAME%%:%%PIPELINE_NAME%%:%%WORKER_NAME%%: ';
BEGIN	
	DBMS_OUTPUT.ENABLE(1000);
	p(v_worker||'Started.');
	time1:=dbms_utility.get_time;
	BEGIN
		%s;
		v_elapsed:=(dbms_utility.get_time-time1) /100;
		v_row_cnt:=SQL%%ROWCOUNT;
		p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%') ;
	EXCEPTION
		WHEN OTHERS THEN
			p(lpad('*',60,'*'));
			v_elapsed:=(dbms_utility.get_time-time1) /100;
			v_row_cnt:=SQL%%ROWCOUNT;
			p('ERROR: '||SQLCODE||'; '||SQLERRM);
			p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%', SQLCODE, SQLERRM) ;
			p(lpad('*',60,'*'));
		%s
	END;
	p(v_worker||'elapsed: ' || (dbms_utility.get_time-time1) /100||'; rows: ' || v_row_cnt);
	COMMIT;
	p(v_worker||'Finished.');
END;
/

"""	% (string.join(sql,';\n'),  onerror)
		self.set_dml(etl_object,plq)
		pl_template = self.get_template(etl_object, logger)
		pl_fname= 'log/codelog/pl_%s.sql' % self._environment._pipeline['etldataflow']['name'] #etl_object['name'].replace("/","_")
		print pl_fname
		if 1:
			plf = open(pl_fname, 'a')
			pl_status = plf.write(pl_template)
			if pl_status!= None:
				self._logger.error('Cannot write to %s.' % pl_fname)
			if 0:
				pl_status = plf.write('/*EXEC compatible*/\n%s' % pl_template.replace("'","''"))
				if pl_status!= None:
					self._logger.error('Cannot write to %s.' % pl_fname)
				plf.close()
		if 0:
			#update cva_basel_rules_ab
			qo= etl_object['name'][:3]
			colid = None
			if 'DROP' in etl_object['name'] or 'UPDATE' in etl_object['name']:
				colid ='1'
			if 'CREATE' in etl_object['name']:
				colid = '3'				
			if 'LOCK' in etl_object['name']:
				colid = '4'
			u=""" 
UPDATE CVA_BASEL_RULES_AB SET DML_QUERY_%s='%s' 
 WHERE  proc_year = 2011
		and proc_mnth = 2
		and rule_category like 'BASEL%%'
		and RULE_STATUS = 'A'
		and query_order is not null
		and query_order=%s;
COMMIT;			""" % (colid,pl_template.strip().rstrip('/').replace("'","''"),qo)
			print(u)
			#print('LOCK' in etl_object['name'])
			self.set_dml(etl_object,u)
			status = self.sql_plus_dml(etl_object,logger)
			print "update status: %s" % status
		sql=[]					
		if m:
			#pprint(m)
			for t in m:
				#logger.info(">>%s||%d" % (t, len(t)))
				if len(t):
					sql.append(t)
		if 0:
			q= """/*%s*/

%s;
			
			 
""" % (etl_object['name'],string.join(sql,';\n'))
			#pprint(q)
			#sys.exit(0)
			self.set_dml(etl_object,q)
			template = self.get_template(etl_object, logger)
			#logger.info(template)
			fname= 'log/codelog/%s.sql' % self._environment._pipeline['etldataflow']['name'] #etl_object['name'].replace("/","_")
			print fname
			if 1:
				f = open(fname, 'a')
				status = f.write(template)
				if status!= None:
					self._logger.error('Cannot write to %s.' % fname)
				f.close()			
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']
		self.cleanup()

		return 0
		
	def sql_plus_proc(self, etl_object, logger):
		""" Executes DML using SQL*Plus """
		self.set_params(etl_object, logger)
		stmpl = self.get_dml(etl_object)
		logger.sql(stmpl)


		q="""--%%WORKER_NAME%%
set timing on serveroutput on
DECLARE v_row_cnt INT;	
time1 NUMBER;
v_elapsed NUMBER;
BEGIN	
time1:=dbms_utility.get_time;
BEGIN
%s;
v_elapsed:=(dbms_utility.get_time-time1) /100;
v_row_cnt:=SQL%%ROWCOUNT;
p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%') ;
EXCEPTION
	WHEN OTHERS THEN
		v_elapsed:=(dbms_utility.get_time-time1) /100;
		v_row_cnt:=SQL%%ROWCOUNT;
			p('ERROR: '||SQLCODE||'; '||SQLERRM);
			p_log_stats(v_row_cnt,v_elapsed,'%%PROJECT_NAME%%','%%PIPELINE_NAME%%', '%%WORKER_NAME%%', SQLCODE, SQLERRM) ;
		RAISE;
	END;
DBMS_OUTPUT.PUT_LINE('time elapsed: ' || (dbms_utility.get_time-time1) /100);
DBMS_OUTPUT.PUT_LINE('rows updated: ' || v_row_cnt);
COMMIT;
END;
/
			"""	% ("EXECUTE IMMEDIATE '%s'" % stmpl.replace("'","''").replace("\n"," "))
		#pprint(q)
		#sys.exit(0)
		self.set_dml(etl_object,q)
		template = self.get_template(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch(etl_object, logger)

		#confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		#pprint((self._pp))
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']
		#pprint(etl_object)
		#sys.exit(0)
		if 0:
			pass
		else:
			#self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			schema_name=self._pp['SCHEMA_NAME']
			#to_db= self._pp['TO_DB'] 

			logger.info('#### START of dml %s.' % etl_object['name'])
			regexp=re.compile(r'((\d+) rows updated\.)|(Elapsed: (\d+:\d+:\d+\.\d+))')
			(out,status) = self.do_query(self._default_login, template,0,regexp)
			#pprint(out)
			#print out[0][1],out[1][3]
			logger.info('#### END of dml %s.' % etl_object['name'])
			if len(out)>1:
				logger.sql("#### Updated: %s, Elapsed: %s #### " %(out[0][1],out[1][3]))
			if status==0:
				logger.info("#### SQL*Plus DML of %s finished successfully." % etl_object['name'])
			else:
				logger.warning('SQL*Plus DML failed for %s.' % etl_object['name'])


			self.cleanup()		
			#sys.exit(0)
		if self._pp.has_key('EMAIL_TO') and 0:
			#confirm(self._process_meta[string.strip(self._pp['EMAIL_TO'],'%')], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._pp['EMAIL_TO'],tab )

		return status

		
	def ddl(self, etl_object, logger):
		""" Executes DDL using SQL*Plus """
		#template = self.get_template(etl_object, logger)
		status=-1
		self.set_params(etl_object, logger)
		template = self.get_template(etl_object, logger)
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']

		if 0:
			pass
		else:
			#self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			schema_name=self._pp['SCHEMA_NAME']
			#to_db= self._pp['TO_DB'] 

			logger.info('#### START of DDL %s.' % etl_object['name'])
			regexp=re.compile(r'(Elapsed: (\d+:\d+:\d+\.\d+))')
			(out,status) = self.do_query(self._default_login, template,0,regexp)
			pprint(out)
			#print out[0][1],out[1][3]
			logger.info('#### END of DDL %s.' % etl_object['name'])
			#if len(out)>1:
				#logger.sql("#### Elapsed: %s #### " %(out[0][3]))
			if status==0:
				logger.info("#### SQL*Plus DDL of %s finished successfully." % etl_object['name'])
			else:
				logger.warning('SQL*Plus DDL failed for %s.' % etl_object['name'])
			self.cleanup()
		return status

	def select(self, etl_object, logger):
		""" Executes DDL using SQL*Plus """
		#template = self.get_template(etl_object, logger)
		status=-1
		self.set_params(etl_object, logger)
		template = self.get_template(etl_object, logger)
		confirm(self._pp.has_key('DB_CONNECTOR'),"'DB_CONNECTOR' is not set!")
		self._default_login=self._pp['DB_CONNECTOR']

		if 0:
			pass
		else:
			#self._default_login=self.get_ora_login(def_conn)
			#self._default_login=self.get_ora_login(self._connector[self._pp['TO_DB']])
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			schema_name=self._pp['SCHEMA_NAME']
			#to_db= self._pp['TO_DB'] 

			logger.info('#### START of DDL %s.' % etl_object['name'])
			#regexp=re.compile(r'(Elapsed: (\d+:\d+:\d+\.\d+))')
			regexp=re.compile(r'(\d+) rows selected.')
			(out,status) = self.do_query(self._default_login, template,0,regexp)
			#pprint(out)
			#print out[0][1],out[1][3]
			logger.info('#### END of DDL %s.' % etl_object['name'])
			#if len(out)>1:
				#logger.sql("#### Elapsed: %s #### " %(out[0][3]))
			if status==0:
				logger.info("#### SQL*Plus DDL of %s finished successfully." % etl_object['name'])
			else:
				logger.warning('SQL*Plus DDL failed for %s.' % etl_object['name'])
			self.cleanup()
		return status
		
		
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
			logger.warning('Column(s) %s missing in arget table.' % string.join(s,', '))			
		return out
	def get_to_tab2(self,t):
		if self._pp.has_key('TO_SCHEMA'):
			t[0]=self._pp['TO_SCHEMA']
		else:
			
			#sys.exit(1)
			if self._globals.has_key('TO_SCHEMA'):
				t[0]=self._globals['TO_SCHEMA']
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
	def get_to_tab(self,t):
		if self._pp.has_key('TO_SCHEMA'):
			t[0]=self.p('TO_SCHEMA')
		else:
			pass
			#sys.exit(1)
			#if self._globals.has_key('TO_SCHEMA'):
				#t[0]=self._globals['TO_SCHEMA']
			#else:
				#print 'no TO_SCHEMA key'
				#pass
				#pprint(self._pipeline)
		#print 'returning ', t
		if self._pp.has_key('TO_TABLE'):
			t[1]=self.p('TO_TABLE')
		else:
			pass
			#sys.exit(1)
			#if self._pipeline.has_key('TO_TABLE'):
		#t[1]=self._pipeline['TO_TABLE']
			#else:
				#print 'no TO_TABLE key'
				#pass		
		
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
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
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

					if 1:
						#fix
						logger.info('#### START CREATE VIEW of %s.' % etl_object['name'])
						(out,status) = self.do_query(to_db, tmpl_batch[tab]['VIEW'],0)
						logger.info('#### END CREATE VIEW of %s.' % etl_object['name'])
						if status==0:
							status=0
							if self._p.has_key('IF_TRUNCATE') and self._p['IF_TRUNCATE']>0:
								logger.info('#### START truncate of %s.' % etl_object['name'])
								(out,status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
								logger.info('#### END truncate of %s.' % etl_object['name'])
							#status=0
							if status==0:
								logger.info('#### START copy of %s.' % etl_object['name'])
								(out,status) = self.do_query(self._default_login, tmpl_batch[tab]['INSERT'],0)
								logger.info('#### END copy of %s.' % etl_object['name'])
								if status==0:
									logger.info("#### SQL*Plus COPY of %s finished successfully." % tab)
								else:
									logger.warning('SQL*Plus COPY failed for %s.' % tab)
							else:
								logger.warning('Truncate table failed for %s.' % tab)
						else: 
							logger.warning('CREATE VIEW failed for %s.' % tab ) #etl_object['name']

			self.cleanup()
			#sys.exit(0)
		if self._pp.has_key('EMAIL_TO') and 0:
			#confirm(self._process_meta[string.strip(self._pp['EMAIL_TO'],'%')], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._pp['EMAIL_TO'],tab )

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
		llen=5000
		if not status:
			llen = self.get_line_length(r_cp)
			to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			
			ctl=self.get_ctl_fixed(string.join(self.get_to_tab(to_t),'.'),r_cp)
			#pprint(ctl)
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
			q= "%s\nset head off line %s pages 0 echo off feedback off space 0 tab off arraysize 5000\nSELECT %s FROM %s %s;" % (col_format, llen, cl , string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			self._logger.sql(q)
			#print q
			#sys.exit(1)
			p1 = Popen(['echo', q], stdout=PIPE)
			p2 = Popen([ 'sqlplus', '-S',from_db], stdin=p1.stdout, stdout=PIPE)
			if 1:
				#READSIZE=200000, ROWS=5000, BINDSIZE=200000, PARALLEL=false, direct=false, columnarrayrows=5000
				p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, 'rows=5000',
				'COLUMNARRAYROWS=5000','STREAMSIZE=200000','readsize=200000',' parallel=false','bindsize=200000','direct=true', 
				"data=\'-\'",
				'LOG=sqlloader/%s.log' % to_tab, 'BAD=sqlloader/%s.bad' % to_tab,'DISCARD=sqlloader/%s.dsc' % to_tab,'ERRORS=10'], stdin=p2.stdout, stdout=PIPE)
				output=' '
				while output:
					output = p3.stdout.readline()
					err.append(output)
					#print output
					self._logger.info(output.rstrip())
				status=p3.wait()
			else:
				output=' '
				while output:
					output = p2.stdout.readline()
					err.append(output)
					#print output
					self._logger.info(output.rstrip())
				status=p2.wait()			
			self._logger.info( 'SQL*Loader status =%s' % status)
			if status==1:
				self._logger.error(string.join(err,'\n'))
			#else: 
				#self._logger.info(string.join(err,'\n'))
		else:
			self._logger.error('Cannot fetch common columns.')
		return (out,status)	
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
	def spool(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		template = self.get_template(etl_object, logger)
		#sys.exit(1)
		confirm(len(template)>0, 'Template batch is missing or misconfigured.')
		#(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		def_conn=self.get_connector(self._p['FROM_DB'])
		status=0
		if 1:
			self._default_login=self.get_ora_login(def_conn)
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			#to_db= self._pp['TO_DB']
			#pprint(self._pp)
			#print template
			#sys.exit(1)
			tab=template #self._pp['WORKER_NAME']
			workn =string.strip(self._pp['WORKER_NAME'])
			if template:
			#for tab in template:
				if 1:
					#to_tab= self.get_to_tab(string.split(tab,'.'))
					from_tab=self.get_from_tab(string.split(string.strip(tab),'.'))
					if 1:
						logger.info('#### START spool of %s.' % workn)
						#(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
						if 1:
							(r, status) = self.do_spool(from_db, from_tab)
							logger.info('#### END spool of %s.' % workn)
							if status==0:
								logger.info('Spool of %s completed successfully.' % workn)
						else:
							logger.warning('#### Skipping spool of %s.' % workn)
							#logger.warning("Truncate of table %s failed." % tab)
					else:
						logger.warning('#### Skipping spool of %s.' % workn)
						
				self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0
		
	def ora2nz_pipe(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch(etl_object, logger)
		
		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		if status:
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')
			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			to_db= self._pp['TO_DB']
			for tab in tmpl_batch:
				if 1:
					#print '---------------',tab
					to_tab= self.get_to_tab(string.split(tab,'.'))
					if self.is_set('TO_TABLE'):
						to_tab[1]=self._pp['TO_TABLE'].strip()
					from_tab=self.get_from_tab(string.split(tab,'.'))
					if 1:
						logger.info('#### START ora2pa copy of %s.' % to_tab[1])
						status=0
						if self.p_if('IF_TRUNCATE'):
							logger.info('#### START truncate of %s.' % etl_object['name'])
							#pprint(tmpl_batch[tab]['PA_TRUNCATE'])
							#pprint(tmpl_batch)
							tmpl= 'TRUNCATE %s;\n' % to_tab[1]
							rx= self.get_q_rx(tmpl)
							a_t = datetime.datetime.now()
							(r, status,err) = self.do_nz_query(to_db,tmpl,0,rx)
							worker_sec = datetime.datetime.now()-a_t
							logger.info('#### END truncate of %s.' % etl_object['name'])						
							self.save_nz_log(etl_object, tmpl, r,status, worker_sec, logger)
						if status==0:
							(r, status) = self.do_ora2nz_load(etl_object, from_db,  to_db, from_tab,to_tab)
							logger.info('#### END ora2pa copy of %s.' % to_tab[1])
							
							if status==0:
								logger.info('Load of %s completed successfully.' % to_tab[1])
						else:
							logger.warning('#### Skipping load of %s.' % to_tab[1])
							logger.warning("Truncate of table %s failed." % to_tab[1])
					else:
						logger.warning('#### Skipping truncate of %s.' % to_tab[1])
						
				self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],to_tab[1] )
		
		return 0

	def file2nz_load(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch(etl_object, logger)
		
		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		if status:
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')
			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			confirm(len(self._default_login)>0, 'Cannot set default login.')
			from_db = self._pp['FROM_DB']
			to_db= self._pp['TO_DB']
			for tab in tmpl_batch:
				if 1:
					#print '---------------',tab
					to_tab= self.get_to_tab(string.split(tab,'.'))
					if self.is_set('TO_TABLE'):
						to_tab[1]=self._pp['TO_TABLE'].strip()
					from_tab=self.get_from_tab(string.split(tab,'.'))
					if 1:
						logger.info('#### START file2pa copy of %s.' % to_tab[1])
						status=0
						if self.p_if('IF_TRUNCATE'):
							logger.info('#### START truncate of %s.' % etl_object['name'])
							#pprint(tmpl_batch[tab]['PA_TRUNCATE'])
							#pprint(tmpl_batch)
							tmpl= 'TRUNCATE %s;\n' % to_tab[1]
							rx= self.get_q_rx(tmpl)
							#(r, status) = self.do_nz_query(to_db,tmpl,0,rx)
							logger.info('#### END truncate of %s.' % etl_object['name'])						
							#self.save_nz_log(etl_object, tmpl, r,status, logger)
						if status==0:
							(r, status) = self.do_file2nz_copy(etl_object, from_db,  to_db, from_tab,to_tab)
							logger.info('#### END file2pa copy of %s.' % to_tab[1])
							
							if status==0:
								logger.info('Load of %s completed successfully.' % to_tab[1])
						else:
							logger.warning('#### Skipping load of %s.' % to_tab[1])
							logger.warning("Truncate of table %s failed." % to_tab[1])
					else:
						logger.warning('#### Skipping truncate of %s.' % to_tab[1])
						
				self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],to_tab[1] )
		
		return 0		
	def ckey2cols(self, col_key):
		return map(lambda x: x.split(':')[0],col_key)

		
	def do_file2nz_copy(self, etl_object,from_db, to_db, from_t, to_t):
		f = ""
		out=[]
		err=[]
		self.confirm(len(from_db)>0, 'Source login is not set.')
		#self.confirm(len(to_db)>0, 'Target login is not set.')
		
		#(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print from_db, from_t
		#sys.exit(1)
		(r_from,status) = self.get_columns(from_db, from_t)
		#pprint(r_from)
		#sys.exit(1)
		if not status:
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			#to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_from,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#pprint(self.ckey2cols(r_from))
			#sys.exit(1)
			ca=self.ckey2cols(r_from)
			cl =  "%s||%s" % (string.rstrip(string.join(ca,"||%s||\n " % ft),'||%s||\n ' % ft),lt)
			#ins = "'('''||%s||''');'" % (string.rstrip(string.join(r_from,"||''',',''''||"),"||''',',''''||"))
			#pprint(ins)
			#sys.exit(0)
			#cl =  "%s||%s" % (string.join(r_from,"||%s||\n" % ft),lt)
			llen=32767
			
			#sys.exit(1)
			q=''
			if 0: #column word_wraapped
				wwp = "COLUMN %s WORD_WRAPPED\n" % string.join(ca,' WORD_WRAPPED\n COLUMN ')
				q= "%s set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='yyyy/mm/dd'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL(%s)*/ %s FROM %s %s;\nexit;\n" % (wwp, llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			else:
				q= "set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='yyyy/mm/dd'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL(%s)*/ %s FROM %s %s;\nexit;\n" % (llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			#set timing off pagesize 0 heading off line 2000 long 128000  feedback off\ncolumn object_ddl format a121 word_wrapped
			self._logger.sql(q)
			#pprint(q)
			#sys.exit(1)
			tab= string.join(from_t,'.')
			#sys.exit(1)
			sqdir= '%s/sql' % self._logger.get_logdir()
			sqfn='%s/%s.sql' % (sqdir,self._pp['WORKER_NAME'])
			if self.is_set('PARTITION'):
				sqfn='%s/%s.%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'])
			if not os.path.isdir(sqdir):
				try:
					os.mkdir(sqdir) 
				except Exception, e:
                        		print 'Created in other thread.', e.strerror
			sqf = open(sqfn, "w")
			sqf.write(q)
			sqf.close()
			datdir= '%s/data' % self._logger.get_logdir()
			if not os.path.isdir(datdir):
				os.mkdir(datdir) 
			gzfn = '%s/%s.gz' % (datdir,self._pp['WORKER_NAME'])
			if self.is_set('PARTITION'):
				gzfn = '%s/%s.%s.%s.gz' % (datdir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'])
			gzfn ='/tmp/%s.pipe' % self._pp['WORKER_NAME']
			os.system( 'rm %s' % gzfn)
			os.system( 'mknod %s p' % gzfn)
			
			#log = open(gzfn, "w")
			#print sqfn
			#srcf='/home/paraccel/data_spooler/tmp/logs/PIPED_TEST/20110911_183256/data/CSMARTVOL.TRD_VOL_UNION_1.SPOOL.CSMARTVOL.TRD_VOL_UNION_1.data'
			cmd="""\n--select count(*) \"%s: Count before COPY\" from %s;
			copy %s from '%s' delimiter '|' dateformat 'YYYY/MM/DD' timeformat 'YYYY/MM/DD HH:MI:SS';
			--select count(*) \"%s: Count after COPY\" from %s;
			""" % (to_t[1],to_t[1],to_t[1],gzfn,to_t[1],to_t[1])
			print cmd
			confirm(self.is_set('FROM_FILE'), "Source file param FROM_FILE is not set.")
			gzfn=self._pp['FROM_FILE']
			q="""copy %s from '%s' delimiter '|' dateformat 'YYYY/MM/DD' timeformat 'YYYY/MM/DD HH:MI:SS';
				""" % (to_t[1],gzfn)
			print q
			rx= self.get_q_rx(q)
			p1 = Popen(['echo', q], stdout=PIPE, stderr=PIPE)
			
			#print from_db
			#IF_COMPRESSED_SPOOL
			
			grp=None

			a_t = datetime.datetime.now()

			if 1:
				self._logger.info('Starting UNCOMPRESSED file2nzsql COPY')
				if 1:
					p3 = Popen([ self._native_client, self._padb], stdin=p1.stdout, stdout=PIPE , stderr=PIPE)
					status =0
					out=[]
					err=[]
					if 1:
						output=' '
						if 1:
							
							while output:
								output = p3.stdout.readline()
								#out.append(output)
								#print output
								#self._logger.info(output.rstrip())
								if len(rx)==1:
									#pprint(regexpt)
									regexp=rx[0]
									if regexp:
										#print regexp
										m = re.match(regexp, output) 
										if m:
											if grp:
												out.append(m.group(grp))
												#print 'append: ', output
											else:
												out.append(m.groups())
												#print 'append: ', output
												self._logger.info(output.rstrip())
											#else out.append(m.group(grp))
						status=p3.wait()
						if status==0:
							self._logger.info('spool status =%s' % status)
						else:
							while output:
								output = p3.stderr.readline()
								err.append(output)
								print 'ERROR: ', output
								self._logger.error(output.rstrip())
							status=p3.wait()
						if status==1:
							self._logger.error('spool status =%s' % status)
					
						if status==2:
							self._logger.warning('spool status =%s' % status)
						

					else:
						output=' '
						
						while output:
							output = p3.stdout.readline()
							#out.append(output)
							print output
							#self._logger.info(output.rstrip())

						
						status=p3.wait()
						if status==0:
							self._logger.info('SQL*Plus status =%s' % status)
						else:
							if status==1:
								self._logger.warning('SQL*Plus status =%s' % status)
								output=' '
								while output:
									output = p3.stderr.readline()
									err.append(output)
									#print output
									self._logger.error(output.rstrip())
								status=p3.wait()
								if status==1:
									self._logger.error(string.join(err,'\n'))							
							else:
								self._logger.error('SQL*Plus status =%s' % status)				
		else:
			self._logger.warning('Cannot fetch common columns.')
		#a_t = datetime.datetime.now()
		worker_sec = datetime.datetime.now()-a_t
		self.save_nz_log(etl_object, q, out,status,worker_sec)
		return (out,status)
	def do_ora2nz_load(self, etl_object,from_db, to_db, from_t, to_t):
		f = ""
		out=[]
		err=[]
		self.confirm(len(from_db)>0, 'Source login is not set.')
		#self.confirm(len(to_db)>0, 'Target login is not set.')
		
		#(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print from_db, from_t
		#sys.exit(1)
		(r_from,status) = self.get_columns(from_db, from_t)
		#pprint(r_from)
		#sys.exit(1)
		a_t = datetime.datetime.now()
		if not status:
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			#to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_from,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#pprint(self.ckey2cols(r_from))
			#sys.exit(1)
			ca=self.ckey2cols(r_from)
			cl =  "%s||%s" % (string.rstrip(string.join(ca,"||%s||\n " % ft),'||%s||\n ' % ft),lt)
			#ins = "'('''||%s||''');'" % (string.rstrip(string.join(r_from,"||''',',''''||"),"||''',',''''||"))
			#pprint(ins)
			#sys.exit(0)
			#cl =  "%s||%s" % (string.join(r_from,"||%s||\n" % ft),lt)
			llen=32767
			
			#sys.exit(1)
			q=''
			if 0: #column word_wraapped
				wwp = "COLUMN %s WORD_WRAPPED\n" % string.join(ca,' WORD_WRAPPED\n COLUMN ')
				q= "%s set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='yyyy/mm/dd'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL(%s)*/ %s FROM %s %s;\nexit;\n" % (wwp, llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			else:
				q= "set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='yyyy/mm/dd'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL(%s)*/ %s FROM %s %s;\nexit;\n" % (llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			#set timing off pagesize 0 heading off line 2000 long 128000  feedback off\ncolumn object_ddl format a121 word_wrapped
			self._logger.sql(q)
			#pprint(q)
			#sys.exit(1)
			tab= string.join(from_t,'.')
			#sys.exit(1)
			sqdir= '%s/sql' % self._logger.get_logdir()
			sqfn='%s/%s.sql' % (sqdir,self._pp['WORKER_NAME'])
			if self.is_set('PARTITION'):
				sqfn='%s/%s.%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'])
			if not os.path.isdir(sqdir):
				try:
					os.mkdir(sqdir) 
				except Exception, e:
                        		print 'Created in other thread.', e.strerror
			sqf = open(sqfn, "w")
			sqf.write(q)
			sqf.close()
			datdir= '%s/data' % self._logger.get_logdir()
			if not os.path.isdir(datdir):
				os.mkdir(datdir) 
			gzfn = '%s/%s.gz' % (datdir,self._pp['WORKER_NAME'])
			if self.is_set('PARTITION'):
				gzfn = '%s/%s.%s.%s.gz' % (datdir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'])
			gzfn ='/tmp/%s.pipe' % self._pp['WORKER_NAME']
			os.system( 'rm %s' % gzfn)
			os.system( 'mknod %s p' % gzfn)
			
			#log = open(gzfn, "w")
			#print sqfn
			#srcf='/home/paraccel/data_spooler/tmp/logs/PIPED_TEST/20110911_183256/data/CSMARTVOL.TRD_VOL_UNION_1.SPOOL.CSMARTVOL.TRD_VOL_UNION_1.data'
			cmd="""\n--select count(*) \"%s: Count before COPY\" from %s;
			copy %s from '%s' delimiter '|' dateformat 'YYYY/MM/DD' timeformat 'YYYY/MM/DD HH:MI:SS';
			--select count(*) \"%s: Count after COPY\" from %s;
			""" % (to_t[1],to_t[1],to_t[1],gzfn,to_t[1],to_t[1])
			q="""copy %s from '%s' delimiter '|' dateformat 'YYYY/MM/DD' timeformat 'YYYY/MM/DD HH:MI:SS';
				""" % (to_t[1],gzfn)
				
			rx= self.get_q_rx(q)
			p1 = Popen(['echo', q], stdout=PIPE, stderr=PIPE)
			#print from_db
			#IF_COMPRESSED_SPOOL
			grp=None
			if 1:
				self._logger.info('Starting UNCOMPRESSED nzsql COPY')
				cmd="/home/iz31541/Oracle11/sqlplus -s ab95022/Aug106@gmail.com @/home/paraccel/data_spooler/%s>%s &" % (sqfn,gzfn) 
				print cmd
				os.system( cmd)
				if 1:
					p3 = Popen([ self._native_client, self._padb], stdin=p1.stdout, stdout=PIPE , stderr=PIPE)
					status =0
					out=[]
					err=[]
					if 1:
						output=' '
						if 1:
							
							while output:
								output = p3.stdout.readline()
								#out.append(output)
								#print output
								#self._logger.info(output.rstrip())
								if len(rx)==1:
									#pprint(regexpt)
									regexp=rx[0]
									if regexp:
										#print regexp
										m = re.match(regexp, output) 
										if m:
											if grp:
												out.append(m.group(grp))
												#print 'append: ', output
											else:
												out.append(m.groups())
												#print 'append: ', output
												self._logger.info(output.rstrip())
											#else out.append(m.group(grp))
							erro = ' '
							while erro:
								erro = p3.stderr.readline()
								if erro.strip():
									err.append(erro)
									print 'ERROR: ', erro
							if len(err)>0:
								self._logger.error(string.join(err,'\n'))											
						status=p3.wait()
						if status==0:
							self._logger.info('spool status =%s' % status)
						else:

							status=p3.wait()
						if status==1:
							self._logger.error('spool status =%s' % status)
					
						if status==2:
							self._logger.warning('spool status =%s' % status)
						

					else:
						output=' '
						
						while output:
							output = p2.stdout.readline()
							#out.append(output)
							print output
							#self._logger.info(output.rstrip())

						
						status=p3.wait()
						if status==0:
							self._logger.info('SQL*Plus status =%s' % status)
						else:
							if status==1:
								self._logger.warning('SQL*Plus status =%s' % status)
								output=' '
								while output:
									output = p3.stderr.readline()
									err.append(output)
									#print output
									self._logger.error(output.rstrip())
								status=p3.wait()
								if status==1:
									self._logger.error(string.join(err,'\n'))							
							else:
								self._logger.error('SQL*Plus status =%s' % status)				
		else:
			self._logger.warning('Cannot fetch common columns.')
		#a_t = datetime.datetime.now()
		worker_sec = datetime.datetime.now()-a_t			
		self.save_nz_log(etl_object, q, out,status,worker_sec)
		return (out,status)
				
	def sql_echo_loader(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)

		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		if status:
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
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
						status=0
						if self._p.has_key('IF_TRUNCATE') and self._p['IF_TRUNCATE']>0 :
							logger.info('#### START truncate of %s.' % etl_object['name'])
							(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
							logger.info('#### END truncate of %s.' % etl_object['name'])						
						if status==0:
							(r, status) = self.do_load(from_db, from_tab, to_db, to_tab)
							logger.info('#### END copy of %s.' % tab)
							if status==0:
								logger.info('Load of %s completed successfully.' % tab)
						else:
							logger.warning('#### Skipping load of %s.' % tab)
							logger.warning("Truncate of table %s failed." % tab)
					else:
						logger.warning('#### Skipping truncate of %s.' % tab)
						
				self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0
		
	def sql_echo_loader_fixed(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)

		confirm(len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.')
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		
		if status:
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
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
						(r, status) = self.do_load_fixed(from_db, from_tab, to_db, to_tab,tmpl_batch[tab])
						if status==0:
								logger.info('Fixed load of %s completed successfully.' % tab)
						logger.info('#### END copy of %s.' % tab)
					else:
						logger.warning('#### Skipping %s.' % tab)
						
				self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			#confirm(self._process_meta[string.strip(self._pp['EMAIL_TO'],'%')], '%s is not defined in process_spec.' % self._pp['EMAIL_TO'])
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0		
	def do_nz_query(self, login, query, analyze=1, regexpt=None, grp=None):
		f = ""
		out=[]
		err=[]
		ora_err =False
		errpos=-1
		#errreg=re.compile(r'.*(ERROR).*')
		confirm(len(login)>0, 'Default login is not set.')
		if 1:			
			#from subprocess import Popen, PIPE
			q=''
			if analyze:
				q = "%s\nset autotrace on timing on echo on serveroutput on\n%s\n%s" % ('-'*20, query,'-'*20) 
			else:
				q = "%s\n" % (query)
			
			#self._logger.info(login)
			self._logger.sql(q)
			pprint(q)
			
			p1 = Popen(['echo', q], stdout=PIPE)
			login= login.split(' ')
			#print login
			p2 = Popen([ self._native_client, "-U", 'ab95022', "-W", 'ab95022', '-h','b4-netezza-01', '-p', '5480', '-d', 'MAP'], stdin=p1.stdout, stdout=PIPE, stderr=PIPE)
			output=' '
			while output:
				output = p2.stdout.readline()
				#err.append(output)
				#print output
				
				if len(regexpt)==1:
					#pprint(regexpt)
					regexp=regexpt[0]
					if regexp:
						#print regexp
						m = re.match(regexp, output) 
						if m:
							if grp:
								out.append(m.group(grp))
								print 'append: ',output
							else:
								out.append(m.groups())
								self._logger.info(output.rstrip())
							#else out.append(m.group(grp))
						
							#self._logger.error(output.rstrip())	
			if 1:
				#print err
				erro=' '
				while erro:
					erro = p2.stderr.readline()
					if erro.strip():
						err.append(erro)
						out.append((erro))
						print 'ERROR:', erro	
				pprint(err)
				if len(err):
					status=2
					self._logger.error(string.join(err,'\n'))	
					
			status=p2.wait()
			print 'psql status= ', status
			if status==0:
				if len(err):
					status=2
			print 'do_nz_query status= ', status
		#sys.exit(1)
		#print 'end'
		return (out,status,err)

	def  p(self,pname):
		confirm(self._pp.has_key(pname),'Parameter %s is not set' % pname)
		return self._pp[pname]

	def get_ctl(self, to_tab, r_int):

		tmpl="""
LOAD DATA
	INFILE '-' "str '%s\n'"
	APPEND
	INTO TABLE %s
	FIELDS TERMINATED BY '%s'
	TRAILING NULLCOLS
	(C_FILLER FILLER,
	 %s)""" % (self.p('LINE_TERMINATOR'),to_tab, self.p('FIELD_TERMINATOR'), string.join(r_int,','))
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
		tmpl="""OPTIONS (READSIZE=200000, ROWS=5000, BINDSIZE=200000, PARALLEL=false, direct=false, columnarrayrows=5000)
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
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			cl =  "'%s'||%s||'%s'" % (ft,string.join(r_int,"||'%s'||" % ft),lt)
			ctl=self.get_ctl(string.join(self.get_to_tab(to_t),'.'),r_int)
			self._logger.log(ctl)
			fname= 'sqlloader/%s.ctl' % to_tab
			import codecs
			f = codecs.open(fname, 'w',"utf-8")
			status = f.write(unicode(ctl))
			if status!= None:
				self._logger.error('Cannot write to %s.' % fname)
			f.close()
			(r,status) = self.get_line_len(((from_db, from_t),(to_db, to_t)))
			llen=10000
			#pprint(r)
			#sys.exit(1)
			if len(r)==0:
				self._logger.error("Cannot find line length.")
			llen=int(r[0]); # +20
			q= "set head off line %s pages 0 echo off feedback off termout off  feed off newpage 0 num 2 arraysize 5000\nSELECT %s FROM %s %s;" % (llen,   cl , string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			self._logger.sql(q)
			#pprint(self._pp)
			p1 = Popen(['echo', q], stdout=PIPE, stderr=PIPE)
			p2 = Popen([ 'sqlplus', '-S',from_db], stdin=p1.stdout, stdout=PIPE , stderr=PIPE
			)
			#cmd= "sqlldr control=sqlloader/ins.ctl userid=mdw/DEPOTbank@gmail.com data=\\'-\\' %s" % to_db
			#READSIZE=200000, ROWS=5000, BINDSIZE=200000, PARALLEL=false, direct=false, columnarrayrows=5000
			status =0
			out=[]
			err=[]
			if 1:
				p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, 'rows=5000',
				'COLUMNARRAYROWS=5000','STREAMSIZE=200000','readsize=200000',' parallel=false','bindsize=200000','direct=true', "data=\'-\'",
				'LOG=sqlloader/%s.log' % to_tab, 'BAD=sqlloader/%s.bad' % to_tab,'DISCARD=sqlloader/%s.dsc' % to_tab,'ERRORS=10'], 
				stdin=p2.stdout, stdout=PIPE, stderr=PIPE)
				output=' '
				#pprint(dir(p3.stderr))
				while output:
					output = p3.stdout.readline()
					out.append(output)
					#print output
					self._logger.info(output.rstrip())
				status=p3.wait()
				if status==0:
					self._logger.info('SQL*Loader status =%s' % status)
				if status==1:
					self._logger.error('SQL*Loader status =%s' % status)
					output=' '
					while output:
						output = p3.stderr.readline()
						err.append(output)
						#print output
						self._logger.warning(output.rstrip())
					status=p3.wait()
					if status==1:
						self._logger.error(string.join(err,'\n'))						
				if status==2:
					self._logger.warning('SQL*Loader status =%s' % status)
				

			else:
				output=' '
				
				while output:
					output = p2.stdout.readline()
					out.append(output)
					#print output
					self._logger.info(output.rstrip())
				
				status=p2.wait()
				if status==0:
					self._logger.info('SQL*Plus status =%s' % status)
				else:
					if status==1:
						self._logger.warning('SQL*Plus status =%s' % status)
						output=' '
						while output:
							output = p2.stderr.readline()
							err.append(output)
							#print output
							self._logger.error(output.rstrip())
						status=p2.wait()
						if status==1:
							self._logger.error(string.join(err,'\n'))							
					else:
						self._logger.error('SQL*Plus status =%s' % status)

		else:
			self._logger.warning('Cannot fetch common columns.')
		return (out,status)		
	def do_spool(self, from_db, from_t):
		f = ""
		out=[]
		err=[]
		confirm(len(from_db)>0, 'Source login is not set.')
		#confirm(len(to_db)>0, 'Target login is not set.')
		
		#(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print from_db, from_t
		#sys.exit(1)
		(r_from,status) = self.get_columns(from_db, from_t)
		
		if not status:
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			#to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_from,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			cl =  "%s||%s" % (string.rstrip(string.join(r_from,"||%s||\n " % ft),'||%s||\n ' % ft),lt)
			#ins = "'('''||%s||''');'" % (string.rstrip(string.join(r_from,"||''',',''''||"),"||''',',''''||"))
			#pprint(ins)
			#sys.exit(0)
			#cl =  "%s||%s" % (string.join(r_from,"||%s||\n" % ft),lt)
			llen=20000
			q= "set head off line %s pages 0 newpage 0 echo off feedback off   feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='yyyy/mm/dd'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL(t)*/ %s FROM %s t %s;\n" % (llen,  cl,  string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			self._logger.sql(q)
			#pprint(q)
			
			sqdir= '%s/sql' % self._logger.get_logdir()
			sqfn='%s/%s.sql' % (sqdir,self._pp['WORKER_NAME'])
			if not os.path.isdir(sqdir):
				try:
					os.mkdir(sqdir) 
				except Exception, e:
                        		print 'Created in other thread.', e.strerror
			sqf = open(sqfn, "w")
			sqf.write(q)
			sqf.close()
			datdir= '%s/data' % self._logger.get_logdir()
			if not os.path.isdir(datdir):
				os.mkdir(datdir) 
			gzfn = '%s/%s.gz' % (datdir,self._pp['WORKER_NAME'])
			log = open(gzfn, "w")
			#print sqfn
			p1 = Popen(['echo', ' @%s' % sqfn], stdout=PIPE, stderr=PIPE)
			#print from_db
			p2 = Popen([ 'sqlplus', '-S', from_db], stdin=p1.stdout, stdout=PIPE , stderr=PIPE
			)
			status =0
			out=[]
			err=[]
			if 1:				
				p3 = Popen(['gzip', '-c'], 
				stdin=p2.stdout, stdout=log, stderr=PIPE)
				p3.wait()
				output=' '
				#while output:
					#output = p3.stdout.readline()
					#out.append(output)
					#print output
					#self._logger.info(output.rstrip())
				status=p3.wait()
				if status==0:
					self._logger.info('gzip status =%s' % status)
				if status==1:
					self._logger.error('gzip status =%s' % status)
					output=' '
					while output:
						output = p3.stderr.readline()
						err.append(output)
						print output
						self._logger.warning(output.rstrip())
					status=p3.wait()
					if status==1:
						self._logger.error(string.join(err,'\n'))						
				if status==2:
					self._logger.warning('gzip status =%s' % status)
				

			else:
				output=' '
				
				while output:
					output = p2.stdout.readline()
					out.append(output)
					print output
					self._logger.info(output.rstrip())
				
				status=p2.wait()
				if status==0:
					self._logger.info('SQL*Plus status =%s' % status)
				else:
					if status==1:
						self._logger.warning('SQL*Plus status =%s' % status)
						output=' '
						while output:
							output = p2.stderr.readline()
							err.append(output)
							#print output
							self._logger.error(output.rstrip())
						status=p2.wait()
						if status==1:
							self._logger.error(string.join(err,'\n'))							
					else:
						self._logger.error('SQL*Plus status =%s' % status)

		else:
			self._logger.warning('Cannot fetch common columns.')
		return (out,status)


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
	def get_template(self, etl_object, logger):
		""" Runs mist tool """
		#pprint(etl_object)
		#pprint(type(etl_object['node']['param']))
		#pprint(self._connector)
		regexp=re.compile(r'((%)([\w\_]+)(%))')
		pp=self._pp
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
		
		#sys.exit(1)
		return template 

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
		pprint(self._p)
		#parse ref params
		regexp=re.compile(r'((%)([\w\_]+)(%))')		
		for param in self._p:
			m = re.match(regexp, self._p[param])
			if m:
				confirm(not(self._process_meta.has_key(m.groups()[2]) and self._connector.has_key(m.groups()[2])), 'EXCEPTION: process_spec and connectors has the same key %s' % m.groups()[2])
				if (self._process_meta.has_key(m.groups()[2])):
					self._pp[param]=self._pp[param].replace(m.groups()[0],self._process_meta[m.groups()[2]])
					
				if (self._connector.has_key(m.groups()[2])):
					#print m.groups()
					#pprint(self._connector)
					self._pp[param]= self.get_login(self._connector[m.groups()[2]]) 

	def get_login(self, connector):
		#pprint(connector)
		confirm(connector.has_key('type'),'connector needs type attribute to be set.')
		confirm(connector.has_key('pword'), 'Connector has no <pword> attribute')
		confirm(connector.has_key('schema'), 'Connector has no <schema> attribute')
		confirm(connector.has_key('sid'), 'Connector has no <sid> attribute')		
		if connector['type']=='NZ':
			return  "-U %s -d %s" %(connector['schema'], connector['sid'])
		else:
			if connector['type']=='ORACLE':
				return self.get_ora_login(connector)
			else:
				self._logger.warning('Unknown connector type - assuming regular connect type.')	
			
		return " -U %s -d %s" %(connector['schema'], connector['sid'])
		
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
		col_key = self.get_cc_key((login, t))
		if not self._ci_nots.has_key(col_key):
			self._ci_nots[col_key]={}
			
		if len(self._ci_nots[col_key])==0:
			q="select  'COLUMN.'||column_name from dba_tab_columns t where table_name =UPPER('%s') and owner='%s' AND data_type IN ('VARCHAR2','CHAR','DATE','LONG','NUMBER') order by column_name;" % (t[1],t[0])
		
			regexp=re.compile(r'.*\.([\w\_]+)\n')
			(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off\n%s" % q,0,regexp,1)

			if status!=0:
				if len(r)==0:
					status=2
					self._logger.fatal('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*)\@', '/***@', login)))
			self._ci_nots[col_key]=r				
			return (r,status)
		else:
			return (self._ci_nots[col_key],0)

	def get_columns(self, login, t):
		col_key = self.get_cc_key((login, t))
		#print 'col_key = ',col_key
		if not self._ci.has_key(col_key):
			self._ci[col_key]={}
		#pprint(self._ci)
		
		if len(self._ci[col_key])==0:
			#AND data_type IN ('VARCHAR2','CHAR','DATE','LONG','NUMBER')
			#q="select  'COLUMN.'||column_name from all_tab_columns t where table_name =UPPER('%s') and owner='%s'  order by column_id;" % (t[1],t[0])
			q="select  'COLUMN.'||column_name||':'||data_length from all_tab_columns t where table_name =UPPER('%s') and owner='%s'  order by column_id;" % (t[1],t[0])
			regexp=re.compile(r'.*\.([\w\_\:]+)\n')
			#print q
			
			(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off\n%s" % q,0,regexp,1)
			#pprint(r)
			if not status:
				if len(r)==0:
					status=2
					self._logger.fatal('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*)\@', '/***@', login)))
			self._ci[col_key]=r	
			#pprint(r)
			#sys.exit(1)
			return (r,status)
		else:
			return (self._ci[col_key],0)
			
	def get_col_format(self, tab_tt):

		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		(login, t) = tab_tt[0]
		ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"','")
		#print ci
		q="select 'COL '||column_name||' FORMAT '||DECODE(data_type, 'VARCHAR2','a'||DATA_LENGTH, 'CHAR','a'||DATA_LENGTH, 'NUMBER','9999999999999999999999999999999','DATE','DATE', 'TIMESTAMP(6)','a28',  'UNDEFINED') fmt from dba_tab_columns where table_name =UPPER('%s') and owner='%s' %s order by column_name;" % (t[1],t[0],ci)
		self._logger.sql(q)
		#sys.exit(1)
		regexp=re.compile(r'[\ ]*(COL [\w \d\_]+)')
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		#pprint(r)
		if status!=0:
			if len(r)==0:
				status=2
				self._logger.fatal('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*),\@', '/***@', login)))
		return (r,status)
	def get_line_len(self, tab_tt):
		(login, t) = tab_tt[0]
		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		#column index
		ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"','")
		#q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') ' q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',32,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from dba_tab_columns) where table_name ='%s' and owner='%s' %s order by column_name);" % (t[1],t[0], ci)		
		q= """
SELECT 'line_length='||(MAX (len) + COUNT (*) - 1) max_len
  FROM (SELECT   column_name, data_type,
                 SUM (data_length) OVER (PARTITION BY table_name ORDER BY column_name ROWS UNBOUNDED PRECEDING)
                                                                          len,
                 data_length
            FROM (SELECT column_name, data_type,
                         DECODE (data_type,
                                 'TIMESTAMP(6)', 28,
								 'TIMESTAMP(6) WITH LOCAL TIME ZONE', 30,
                                 data_length
                                ) data_length,
                         table_name, owner
                    FROM dba_tab_columns)
           WHERE table_name =UPPER('%s') and owner='%s' %s order by column_name);
""" % (t[1],t[0], ci)
		self._logger.sql(q)	
		#print q, login
		#sys.exit(1)
		#q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') '||DECODE(data_type,'VARCHAR2','CHAR', 'INTEGER','CHAR','NUMBER','INTEGER EXTERNAL','TIMESTAMP(6)','TIMESTAMP(6)', data_type) q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',11,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from dba_tab_columns) where table_name ='%s' and owner='%s' %s order by column_name);" % (t[1],t[0], ci)
		#self._logger.info(q)
		#regexp=re.compile(r'[\ ]*([\w\d\_]+\ POSITION\(\d+\:\d+\) [\w\d\(\)]+)')
		regexp=re.compile(r'.*line_length=([\w]+)')
		
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		
		if status!=0:
			if len(r)==0:
				status=2
				self._logger.fatal('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*),\@', '/***@', login)))
		return (r,status)
		

	def get_col_position(self, tab_tt):
		(login, t) = tab_tt[0]
		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		#column index
		ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"','")
		q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') ' q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',32,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from dba_tab_columns) where table_name =UPPER('%s') and owner='%s' %s order by column_name);" % (t[1],t[0], ci)		
		self._logger.sql(q)
		regexp=re.compile(r'[\ ]*([\w\d\_]+\ POSITION\(\d+\:\d+\))')
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		#pprint(r)
		if status!=0:
			if len(r)==0:
				status=2
				self._logger.fatal('Table %s doesn\'t exist in %s.' % (string.join(t,'.'), re.sub('\/(.*),\@', '/***@', login)))
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
			confirm(len(r_from)>0, 'Table %s does not exists in source db.' % from_t,self._logger)
			(r_to,s_to) = self.get_columns_nots(to_db, to_t)
			confirm(len(r_to)>0, 'Table %s does not exists in target db.' % to_t,self._logger)
			if not s_from and not s_to:
				r_int = list(set(r_from) & set(r_to))
				r_int.sort()
				self._cci_nots[to_key][from_key]=r_int
				self._cci_nots[from_key][to_key]=r_int
				return (r_int, 0)
			else:
				self._logger.error('Cannot get column lists.')
			return (None, 1)
		else:
			return (self._cci_nots[to_key][from_key], 0)
	def get_cc_key (self, db_tab_t):
		(db, tab_t) =db_tab_t
		return "%s|%s" % (db, self.gt(tab_t))
	def get_common_cols(self, from_db, from_t, to_db, to_t):
		from_key = self.get_cc_key((from_db, from_t))
		#print 'from_key=%s' % from_key
		to_key = self.get_cc_key( (to_db, to_t))
		#print 'to_key= %s'% to_key
		#pprint (self._cci.keys())
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
					(r_int, status)=self.get_columns(from_db, from_t)
					#print 'got common cols',from_db, from_t,r_int
					#sys.exit(1)
					
				if not status:
					#q_to = self.get_select_from_cols( r_int, to_t)
					#q_from = self.get_select_from_cols( r_int, from_t)
					lame_duck=''
					if pp.has_key('LAME_DUCK') and int(pp['LAME_DUCK'])>0:
						lame_duck = "WHERE ROWNUM <= %s " % pp['LAME_DUCK']
					part=''
					if pp.has_key('PARTITION'):
						part = " PARTITION (%s) " % pp['PARTITION']
					else:
						if pp.has_key('PARTITION'):
							part = " PARTITION (%s) " % pp['PARTITION']
						else:
							if pp.has_key('SUBPARTITION'):
								part = " SUBPARTITION (%s) " % pp['SUBPARTITION']
						
						
					bucket=''
					if pp.has_key('BUCKET_ID'):
						bucket = " AND ora_hash(GFCID||CUST_NAM,2)=%s " % pp['BUCKET_ID']	
					ins_mode=' APPEND '
					#pprint(pp)
					if pp.has_key('INSERT_MODE'):
						ins_mode = " %s " % pp['INSERT_MODE']
					template[from_tab]={}
					template[from_tab]['PA_TRUNCATE'] ="TRUNCATE %s;\n" % to_t[1]
				else:
					logger.error('Failed to create code templates.')

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
					#print 'got common colsfor ', from_db, from_t, to_db, to_t	
					#pprint(r_int)
					
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
					logger.error('Failed to create fixed code templates.')

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
		


#!/usr/bin/python2.7
#
# Copyright 2016.  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""Ad-hoc parallel pipes for scalar Oracle table data.
Sorce and targe should be Oracle instances.
"""
__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'
__date__    = '2016-02-08'  # yyyy-mm-dd
__module_name__ = "tab_copy"
__short_cright__= " Creative Commons License" # http://creativecommons.org/licenses/by/3.0/
__version__ = '1.0'     # Human-Readable Version number
version_info = (1,0,0)  # Easier format: if version_info > (1,2,5)

import string, urlparse, time
from os import curdir, sep
import os, re
import threading
from subprocess import Popen, PIPE

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os
import getpass

if os.name == 'nt':
	import clr


import sys
import traceback
import StringIO

if os.name == 'nt':
	sys.path.append(r'I:\development\python\www\lib')
	clr.AddReference("System.Data")
	clr.AddReference("Oracle.DataAccess")
	import System.Data
	import System.Environment
	import Oracle.DataAccess.Client
	
#clr.AddReference("Oracle.DataAccess.Types")

import copy

import pyexpat
from xml.dom import minidom
from pprint import pprint
import gc
from lib.logger import TestEvent,logger as singleton_logger
import lib.pipeline_flags as pipeline_flags 
from lib.etl_environment import Environment



# Hardcoded constants.
# traceback
STACKTRACE_MAX_DEPTH = 50

def confirm(test, testname = "Test"):
    if not test:
        msg=  "Failed: " + testname
        raise Exception( '%s (%s)' % (msg, test) )

class ConnectionProperties :
	def set(self, string):
		self._dict = {}
		for i in string.split(';'):
			k, v = i.split('=')
			self._dict[k.lower()] = v
	def __getitem__(self, key):
		return self._dict[key]

	def n2onoff(val):
		if val:
			return 'ON'
		else:
			return 'OFF'

class EtlPipeline:
	'''ETL Pipeline class. Usage:
	
	flags = pipeline_flags.PipelineFlags(singleton_logger)
	environment = Environment(flags, singleton_logger)
	etl_pipeline = EtlPipeline(flags, environment,singleton_logger)

	etl_logger = etl_pipeline._logger

	etl_pipeline.ExecutePipeline()

	while threading.activeCount()>1:
		#print '------count=',  threading.activeCount()
		time.sleep(1)
	etl_logger.info('ETL finished.')

	
	Notes:
	*	The pipeline can accept 2 parameters - pipeline_spec and pipeline
	*	Pipeline can use shell envirinment variables.
	*	All options must be predefined in flags.py
	*	Log location is defined in pipeline_spec.
	'''
	def __init__(self, flags, environment, s_logger):
		self._echo = 0
		self._feedback = 0
		self._prompt = '>'
		self._singleton_logger=s_logger
		self._timestamp_string = time.strftime('%Y%m%d-%H%M%S')
		self._environment = environment
		#pprint(self._environment._pipeline_spec)
		self._pipeline_name = self._environment.get_pipeline_name()
		#print self._environment.get_pipeline_name()
		#sys.exit(1)
		self._logger = self._environment.SetupStructuredLogger(self._pipeline_name, self._pipeline_name,s_logger, False)
		#print dir(self._environment )
		#print type(self._logger)
		#sys.exit(1)
		self._logger.set_jobname(TestEvent)
		self._ws = None #workseet
		self._wb = None #workbook
		#self._test_xml = None #xml defining test
		self._pipeline = None #list of tests
		#self._test_spec =None #test specs
		self._conn = {} #connections dict
		self._test_timestamp = time.ctime().replace(':','_')
		#print self._test_timestamp
		#print sys.argv
		self._etl_meta = self._environment.etl()
		self._schema_meta = self._environment.schema()
		self._pipeline_meta =self._environment._pipeline_spec
		self._process_spec =self._pipeline_meta['process_spec']

		#pprint(self._environment._pipeline_spec)
		#pprint(self._pipeline_meta)
		self._xml_config = self._pipeline_meta['worker']
		#self._logger.set_jobname(logger.ETLEvent)
		self._workers = {}
		self._ConstructWorkers()
		#self._ConstructTransformers()
		#pprint(self._pipeline_meta)
		#sys.exit(1)   
			
				
	def confirm(test, testname = "Test"):
		if not test:
			msg=  "Failed: " + testname
			raise Exception( '%s (%s)' % (msg, test) )

	def _ConstructWorkers(self):
		"""Construct Worker Object."""
		
		xml_workers = self._xml_config
		
		for worker in xml_workers.iteritems():
			#pprint(worker)
			#sys.exit(0)
			if 1:			
				worker_meta = worker[1].values()[0]
				worker_name= worker[1].keys()[0]
				confirm(worker_meta['attr'].has_key('module_name'),
						'Undefined module_name attribute for worker <%s>' % worker[0])
				module_name = worker_meta['attr']['module_name']
				binaries_path = self._pipeline_meta['process_spec']['binaries_path']
				worker_object =None
				if module_name and binaries_path:
						_import = 'import %s.%s as %s' % (binaries_path,module_name,module_name)
						#self._logger.info('Trying: %s' % _import)
						exec _import
						_exec = 'worker_object = %s.%s(self._pipeline_meta,self._logger, self._environment)' % (module_name,worker_name)
						#self._logger.info('Trying: %s' % _exec)
						exec _exec
						if not self._workers.has_key(worker[0]):
							self._workers[worker[0]]={}
						if not self._workers[worker[0]].has_key("%s.%s" %(module_name,worker_name)):
							self._workers[worker[0]]["%s.%s" %(module_name,worker_name)]=None
						self._workers[worker[0]]["%s.%s" %(module_name,worker_name)] = worker_object
						#pprint(worker_object)
						#sys.exit(1)
				else:
						self._logger.error('Unrecognized module name "%s" for worker <%s>' %
										   (module_name, worker[0]))
	def _ConstructExtracters(self):
			"""Construct Extracter Object."""
			self._extracters = {}
			xml_extracters = self._xml_config['extracter']
			#pprint(dir(xml_extracters))
			#sys.exit(1)
			for e in xml_extracters.iteritems():
					if  not e[1].has_key('module_name'):
							self._logger.error('Undefined module_name attribute for extracter %s' % e[0])
					#if e.module_name():
					module_name = e[1]['module_name']
					#pprint(self._pipeline_meta['process_spec'])
					binaries_path = self._pipeline_meta['process_spec']['binaries_path']
					if module_name and binaries_path:
							_import = 'import %s.%s as %s' % (binaries_path,module_name,module_name)
							self._logger.info('Trying: %s' % _import)
							exec _import
							extracter = None
							_exec = 'extracter = %s.%s(self._pipeline_meta["process_spec"],self._logger)' % (module_name,e[0])
							#print _exec,
							self._logger.info('Trying: %s' % _exec)
							exec _exec
							#pprint(extracter)
							#sys.exit(1)
							self._extracters[e[0]] = extracter
					else:
							self._logger.error('Unrecognized module name %s for extracter %s' %
											   (module_name, e.name()))
	def queryConnectInfo(self, test):
		#pprint(test)
		#pprint (self._test_spec['connector'][test['config']['connector']])
		conn_info = self._pipeline_meta['connector'][test['config']['connector']]
		dataSource = conn_info['sid']
		#'GMAD' #raw_input('Data Source: ')
		user = conn_info['schema']
		#'C160970GMA' #raw_input('Username: ')
		password = conn_info['pword']
		#'DEPOTbank1$' #raw_input('password: ')
		self._logger.info('Connecting to Data Source=%s;User ID=%s;Password=xxxxxxx' % (dataSource, user), __name__)
		return 'Data Source=%s;User ID=%s;Password=%s' % (dataSource, user, password)

	def queryConnInfo(self, connector):
		#pprint(test)
		#pprint (self._test_spec['connector'][test['config']['connector']])
		conn_info = self._pipeline_meta['connector'][connector]
		dataSource = conn_info['sid']
		#'GMAD' #raw_input('Data Source: ')
		user = conn_info['schema']
		#'C160970GMA' #raw_input('Username: ')
		password = conn_info['pword']
		#'DEPOTbank1$' #raw_input('password: ')
		self._logger.info('Connecting to Data Source=%s;User ID=%s;Password=xxxxxxx' % (dataSource, user), __name__)
		return 'Data Source=%s;User ID=%s;Password=%s' % (dataSource, user, password)

	def Set(self, OptionString):
		''' some resamblance to SQL*PLUS
		Tablemode on|off|auto
		'''
		s = OptionString.upper().strip()
		if s == 'ECHO ON':
			self._echo = 1
		elif s == 'ECHO OFF':
			self._echo = 0
		elif s == 'FEEDBACK ON':
			self._feedback = 1
		elif s == 'FEEDBACK OFF':
			self._feedback = 0

	def Show(self, OptionString):
		''' when there are more options i'll work it out, meanwhile SHOW ALL
		'''
		print 'ECHO is ' + n2onoff(self._echo)
		print 'FEEDBACK is ' + n2onoff(self._echo)


	def Open(self, ConnectString):
		self._ConnectString = ConnectString
		self._ConnectionProperties = ConnectionProperties()
		self._ConnectionProperties.set(self._ConnectString)
		self._Connection = Oracle.DataAccess.Client.OracleConnection(self._ConnectString)
		self._Connection.Open()

		print '\nServerVersion: ' + self._Connection.ServerVersion
		print '\nConnection state: %s' % self._Connection.State.ToString()

	def Close(self):
		self._Connection.Close()

	## def getConnection(self):
	## return self._Connection

	def setCommand(self, query):
		self._Command = Oracle.DataAccess.Client.OracleCommand(query, self._Connection) 

	def ExecuteReader(self):
		self._Reader = self._Command.ExecuteReader()
		## bei SELECT immer -1
		## if self._feedback == 1:
		## print self._Reader.RecordsAffected

	def ExecuteNonQuery(self):
		self._count = self._Command.ExecuteNonQuery()
		if self._feedback == 1:
			print '%d rows affected' % self._count

	def ExecSql(self, query):
		if self._echo:
			print '> ' + query
		try:
			## if 1:
			if query.strip()[:6].upper() == 'SELECT':
				self.setCommand(query)
				self.ExecuteReader()
				self.print_Reader()
			elif query.strip()[:5].upper() == 'EXEC ':
				statement = query[5:]
				print 'statement %s' % statement
				proc = statement.split(' ')[0]
				print 'proc %s' % proc
			elif query.strip()[:5].upper() == 'DESC ':
				print '--> desc'
				statement = query[5:]
				self.desc(statement.upper().strip())
			else:
				print '--> else'
				print query
				self.setCommand(query)
				self.ExecuteNonQuery()
		##if 0:
		except StandardError, e:
			if self._echo == 0: 
				print query
				print "Fehler: ", e


	def print_Reader (self):
		rdr = self._Reader
		if rdr:
			anz = rdr.FieldCount
			print
		cnt = 0
		while rdr.Read():
			cnt += 1
			for i in range(anz):
				''' print '%-30s %-30s%s' % (rdr.GetName(i), rdr.GetFieldType(i), rdr[i])'''
				print '%-30s %s' % (rdr.GetName(i), rdr[i])
				print
				self._count = cnt
			if self._feedback == 1:
				print '%d rows affected' % self._count
		rdr.Close()
		rdr.Dispose()
		self._Reader = None


	def prompt1(self):
		return '%s@%s -->>' % (self._ConnectionProperties['user id'], self._ConnectionProperties['data source']) 

	def ufi2(self):
		''' multi line commands
		I would like to use cancel ^C for cancel,
		but KeyboardInterrupt works somewhat different in IronPython
		'''
		cmd = ''
		print self.prompt1()
		while 1:
			a = raw_input()
			
			try:
				a_lc = a.lstrip().lower().split()[0]
			except:
				a_lc = ''
			## work around. I would like to cancel input with ^C
			print a_lc
			if a_lc == 'cancel':
				print 'input canceld'
				cmd = ''
				print self.prompt1()
			elif a_lc == 'set':
				self.Set(' '.join(a.lstrip().split()[1:]))
			elif a_lc == 'show':
				self.Show(' '.join(a.lstrip().split()[1:]))
			elif a_lc == 'connect':
				print 'a:', a
				p = ' '.join(a.lstrip().split()[1:])
				print 'p: ', p
				try:
					(up, dataSource) = p.split('@', 1)
				except:
					up = p
					dataSource = self._ConnectionProperties['data source']

				print up, dataSource

				try:
					user, password = up.split('/',1)
				except:
					user = up
					password = raw_input('password: ')
					connectString = 'Data Source=%s;User ID=%s;Password=%s' % (dataSource, user, password)
					print '--> connect %s' % connectString
				self.Close()
				self.Open(connectString)
			else: 
				cmd += a + '\n' 
				print cmd
				if cmd.lower() == 'quit\n':
					break
				if a != '' and cmd.strip():
					print 'calling: %s' % cmd 
					self.ExecSql(cmd)
				else:
					continue
				cmd = ''
				print self.prompt1()
	def ProcessInsert(self, ins):
		for i in range(1,ins.Count):
			#try:
				query=ins[i]
				print query
				self.setCommand(query)
				self.ExecuteNonQuery()
			#except StandardError, e:
				#print query
		print "Inserted %d records." % ins.Count
	def PrintRefCursor(self, refCursor):
		#refCursor = cmd.Parameters["OUT_MBR_SMRY_VW"].Value; 
		reader = refCursor.GetDataReader();
		print reader.FieldCount
		for i in range(0, reader.FieldCount): 
			print "%s\t" % reader.GetName(i),
		print
		while reader.Read():
			for i in range(0, reader.FieldCount):
					print "%s\t" % reader[i],
			print
			print
	def GetTest(self, loc):
			f = open(loc, 'r')
			self._test_xml = f.read();
	def ParseTestXml(self):
			dom = minidom.parse(self._test_xml)

	def setTestParams(self,  cmd,  test, in_param):
		cmd.Parameters.Clear();
		#import lib.srcinfo as srcinfo
		ptype = None
		in_out = None
		dvalue = System.DBNull.Value
		self._logger.info('Setting params for procedure %s.' % test['procedure']['name'], __name__)
		#pprint(dir(in_param))
		self._logger.info('Num of params in metadata: %d' % (test['procedure']['params'].Count), __name__)
		if in_param is not None:
				self._logger.info('Param init from sql.', __name__)
				
				self._logger.info('Num of params: %d' % (in_param.Count), __name__)
				#self._logger.info('exec %s(' % test['procedure']['name'], __name__)
		else:
				self._logger.info('Param init from metadata.', __name__)
		for pid,param in test['procedure']['params'].iteritems():
				pname = param['name']
				#print param['type']
				if param['type'] == 'REF CURSOR':
						self._logger.info('\t:%s,' % (pname), __name__)
						ptype = Oracle.DataAccess.Client.OracleDbType.RefCursor
				else:
						if param['type']=='VARCHAR2':
								ptype = Oracle.DataAccess.Client.OracleDbType.Varchar2
						else:
								if param['type']=='NUMBER':
										#pprint(dir(Oracle.DataAccess.Client.OracleDbType))
										ptype = Oracle.DataAccess.Client.OracleDbType.Decimal
								else:
										self._logger.info( 'Unknown param type %s' % param['type'], __name__)
				#pprint (ptype)
				if param['in_out'] == 'OUT':
						
						in_out = System.Data.ParameterDirection.Output
				else:
						if param['in_out']=='IN':
								in_out = System.Data.ParameterDirection.Input
						else:
								self._logger.info('Unknown param direction %s' % param['in_out'], __name__)
				#pprint (in_out)
				if in_param == None:
						
						if param['value'] == 'Null':
								self._logger.info('\t%d.%s = Null' % (pid,pname), __name__)
								dvalue = System.DBNull.Value
						else:
								self._logger.info('\t%d.%s = %s' % (pid,pname,param['value']), __name__)
								dvalue = param['value']
				else:
						
						if in_param.has_key(pname):
							   
								if in_param[pname] == None:
										self._logger.info('\t%d.%s = Null' %(pid, pname), __name__)
										dvalue = System.DBNull.Value
								else:
										self._logger.info("\t%d.%s = '%s'" % (pid,pname,in_param[pname]), __name__)
										dvalue = in_param[pname]
						#self._logger.info('Param %s not found in init dict.' % pname)
										 
				if 1:
						p_input = cmd.Parameters.Add(pname, ptype, dvalue, in_out);
		#self._logger.info(') \n', __name__)
	def getCmdSql(self,  test, in_param):
			self._logger.info('Setting params for procedure %s.' % test['procedure']['name'], __name__)
			#pprint(dir(in_param))
			self._logger.info('Num of params in metadata: %d' % (test['procedure']['params'].Count), __name__)
			if in_param is not None:
					self._logger.info('Param init from sql.', __name__)
					
					self._logger.info('Num of params: %d' % (in_param.Count), __name__)
			else:
					self._logger.info('Param init from metadata.', __name__)
					
			out_sql= 'exec %s(' % test['procedure']['name']
			variable=''
			for pid,param in test['procedure']['params'].iteritems():
					pname = param['name']
					pvalue='Null'
					ptype= param['type']
					#pprint(ptype)
					#print param['type']
					if ptype == 'REF CURSOR':
							#ptype = Oracle.DataAccess.Client.OracleDbType.RefCursor
							variable = """%svariable %s refcursor
""" % (variable,pname) 
							out_sql = '%s %s=>:%s,' % (out_sql , pname, pname)
					else:
							pvalue=None
							if in_param == None:
									pvalue = param['value']
							else:
									pvalue = in_param[pname]
											
									
							if ptype=='VARCHAR2' or param['type']=='CHAR':
									#ptype = Oracle.DataAccess.Client.OracleDbType.Varchar2
									if pvalue =='Null':
											out_sql = '%s %s=>%s,' % (out_sql , pname, pvalue)
									else:
											out_sql = "%s %s=>'%s'," % (out_sql , pname, pvalue)
							else:
									if ptype=='NUMBER':
											#pprint(dir(Oracle.DataAccess.Client.OracleDbType))
											#ptype = Oracle.DataAccess.Client.OracleDbType.Decimal
											out_sql = '%s %s=>%d,' % (out_sql , pname, pvalue)
									else:
											self._logger.info( 'Unknown param type %s' % param['type'], __name__)


			out_sql = '%s %s )' % (variable, out_sql.rstrip(',') )
			#pprint(dir(out_sql))
			#sys.exit(1)
			return   out_sql;                                
	def execTest(self,con, test):
		clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')                
		tname = test['name']
		procname = test['procedure']['name']
		cmd = con.CreateCommand();
		cmd.CommandType= System.Data.CommandType.StoredProcedure
		cmd.CommandText=test['procedure']['name']
		self._logger.info('Executing test %s, procedure %s.' % (tname,procname), __name__)
		sql = None
		self._logger.code('set autoprint on timing on echo off term off serveroutput off')
		self._logger.code('spool %s.log' % procname)
		self._logger.code('PROMPT Started at:')
		self._logger.code('select systimestamp from dual;')
		if test['procedure']['param_source']=='sql':
				self._logger.info('param_source=sql', __name__)
				for sid,sqld in test['procedure']['sqls'].iteritems():
						#print sid
						sql=sqld['value'].replace('\\','')
						self._logger.info('SQL: %s' % sql, __name__)
						sql_cmd = con.CreateCommand();
						sql_cmd.Parameters.Clear();
						#pprint(dir(System.Data.CommandType))
						sql_cmd.CommandType= System.Data.CommandType.Text
						sql_cmd.CommandText=sql
						dr = sql_cmd.ExecuteReader();
						#pprint(dir(dr))
						tid=0
						while dr.Read():
								tid +=1
								in_param = {}
								#pprint(dir(dr))
								self._logger.info('Field count = %d ' % dr.FieldCount, __name__) 
								for colid in range(0,dr.FieldCount):
										#print dr.GetName(colid), '(', dr.GetDataTypeName(colid), '), ',
										if dr.IsDBNull(colid):
												#self._logger.info('Value in %s is null.' % dr.GetName(colid)) 
												in_param[dr.GetName(colid)]=None
										else:
												if  dr.GetDataTypeName(colid)=='Date':
														in_param[dr.GetName(colid)]= '%d/%d/%d' % (dr.GetOracleDate(colid).Month,dr.GetOracleDate(colid).Day,dr.GetOracleDate(colid).Year) 
												else:
														if dr.GetDataTypeName(colid)=='Varchar2' or dr.GetDataTypeName(colid)=='Char':
																#self._logger.info('Found param #%d, name=%s, type=%s' % (colid,dr.GetName(colid),dr.GetDataTypeName(colid)))
																in_param[dr.GetName(colid)]=dr.GetOracleString(colid).Value 
														else:
																#print dr.GetDataTypeName(colid)
																#raise Exception('Undefined data type.')
																self._logger.error('Undefined data type.', __name__);
								#pprint(in_param)
								test['id']=tid
								self.setTestParams(cmd,test,in_param)
								self._logger.code('\nPROMPT Test# %d' % test['id'])
								self._logger.code(self.getCmdSql(test,in_param))
								self.ExecuteAndSave(cmd,test)
								#dispose every 100 fetches so we do not get
								#SystemError: ORA-01000: maximum open cursors exceeded
								#should be less then 300/number_of_refcursors
								if tid%100==0:
										self._logger.info('Disposing cmd.', __name__);
										cmd.Dispose()
										gc.collect()
										cmd = con.CreateCommand();
										cmd.CommandType= System.Data.CommandType.StoredProcedure
										cmd.CommandText=test['procedure']['name'] 
										#sys.exit(1)
								#cmd.Dispose()
						sql_cmd.Dispose()
		else:
			self.setTestParams(cmd,test,None)
			test['id']=1
			self.ExecuteAndSave(cmd, test)
			cmd.Dispose()
		self._logger.code('PROMPT Finished at:')
		self._logger.code('select systimestamp from dual;')
		self._logger.code('spool off')
		self._logger.code('host notepad %s.log' % procname)
		#create DONE file       
		self.CreateFile('%s/DONE' % test['log_dir'])

				
	def runWorker(self, w):
		#clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')                
		#pprint(w)
		#pprint(self._workers)
		#pprint(self._pipeline_meta)
		from lib.worker import Worker 
		wo = Worker(self._environment,self._logger)
		#pprint(sorted(w['node'].keys()))
		for subworker_id in sorted(w['node'].keys()):
			#worker_type=w['node'].keys()[0]
			#rx = re.compile( r'(\d+)')		
			#short_t = rx.sub( '', subworker_type).strip('_')
			#print short_t
			subworker_type= w['node'][subworker_id]['type']
			confirm(self._pipeline_meta['worker'].has_key(subworker_type),"Specified worker type <%s> is not listed in pipeline meta." % subworker_type)
			confirm(self._workers.has_key(subworker_type),"Specified worker type <%s> is not defined in pipeline workers." % subworker_type)
			subworker_name=w['node'][subworker_id]['node'].keys()[0]
			print subworker_name
			confirm(self._pipeline_meta['worker'][subworker_type].has_key(subworker_name),"Specified worker <%s> of type <%s> is not defined in pipeline meta." % (subworker_name,subworker_type))
			subworker_attr=self._pipeline_meta['worker'][subworker_type][subworker_name]['attr']
			subworker_key='%s.%s' % (subworker_attr['module_name'],subworker_attr['name'])
			#pprint((self._workers[worker_type]));
			#pprint(worker_attr)
			confirm(self._workers[subworker_type].has_key(subworker_key),
					"Specified worker <%s> of type <%s> is not defined in pipeline workers." % (subworker_key,subworker_type))
			subworker_obj = self._workers[subworker_type][subworker_key]
			confirm( not type(subworker_obj) is 'instance', 'Worker object <%s> is not set.' % subworker_key)
		#print worker_obj.__module__
			subwo = copy.copy(subworker_obj)
			#pprint(subwo)
			#sys.exit(1)
			#set etl_object
			etl_object = w['node'][subworker_id]['node'][subworker_attr['name']]
			etl_object['name']=w['attr']['name']
			#pprint(self._environment._pipeline_flags)
			subwo._etl_object=etl_object
			wo.add(subwo)
		#print type(wo)
		#pprint(w)
		wo.set(w)
		#pprint(wo._pp)
		#print 'params: ', wo._pp
		#pprint(dir(wo._pp))
		#sys.exit(1)
		#if not int(self._environment._pipeline_flags.release):
		ft =wo.get_p('FLOW_TYPE', 'ASYNC')
		if ft=='ASYNC':
			wo.start()
		else:
			if ft=='SYNC':
				wo.run()
			else:
				self._logger.error('Unknown FLOW_TYPE %s.' % ft)
				
		


			
	def SaveAsExcel(self, cmd, test):
		from Microsoft.Office.Interop import Excel
		from System import Type
		t = System.Type.GetTypeFromProgID("Excel.Application")
		ex = System.Activator.CreateInstance(t)
		self._wb = ex.Workbooks.Add()
		wsid=1
		for pid,param in test['procedure']['params'].iteritems():
				
				if param['type'] == 'REF CURSOR':
						pname = param['name']
						ws = self._wb.Worksheets[wsid]
						ws.Name = pname
						self.RcToWorksheet(cmd.Parameters[pname].Value,ws)
						
						wsid +=1
		fname = 'C:/tmp/%s.%s_%s_%d.xls' % (tname, procname, ttype, tid) 
		self._wb.SaveAs(fname,Excel.XlFileFormat.xlWorkbookNormal, Type.Missing, Type.Missing,Type.Missing, Type.Missing, Type.Missing, Type.Missing, Type.Missing,Type.Missing)
		ex.Quit() 

	def SaveAsText(self, cmd, test):
		wsid=1
		tname = test['name']
		procname = test['procedure']['name']
		tid=test['id']
		ext=test['config']['file_ext']
		tmpl=test['config']['file_tmpl']
		test['file_name'] = '%s/%s.%s' % (test['log_dir'], tmpl,ext)
		#self._logger.info('Filename tmpl = %s.' % tmpl, __name__)
		rcs = []
		for pid,param in test['procedure']['params'].iteritems():
				
				
				if param['type'] == 'REF CURSOR':
						rcs.append(param['name'])
						self._logger.info('Found cursor %s.' % param['name'], __name__)
						#test['file_name']=test['file_name'].Replace('{RC_NAME}',param['name'])
				else:
						test['file_name']=test['file_name'].Replace('{'+param['name']+'}',
																	cmd.Parameters[param['name']].Value.ToString().Replace('/','-'))
		#pprint((rcs))
				


		if rcs.Count>0:
				fname_restore= test['file_name']
				for rc_name in rcs:
						#print rc_name
						test['file_name']=test['file_name'].Replace('{RC_NAME}',rc_name)
						#sys.exit(1)
						#text = []
						#rc_name=''
						self._logger.info('Opening log file %s ...' % test['file_name'], __name__)
						f = open(test['file_name'], 'w')
						rc= cmd.Parameters[rc_name].Value
						self.RcToFile(rc,f, test)

						wsid +=1
						f.close()

						self._logger.info('Log file is closed.', __name__)
						#restore fname for next cursor file
						test['file_name']=fname_restore
		#sys.exit(1)
				
	def getLogDir(self,test):
			#print test['config']['log_dest']
			return self._pipeline_meta['process_spec'][test['config']['log_dest']]
			#return 'test';


	def ExecuteAndSave(self, cmd, test):
			tname=test['name']
			procname=test['procedure']['name']
			ttype = test['procedure']['param_source']
			tid=test['id']
			#create dirs
			log_dir = self.getLogDir(test)
			if not os.path.isdir(log_dir):
					os.mkdir('%s' % (log_dir))
			log_dir ='%s/%s/' % (log_dir,self._test_timestamp)
			#print log_dir
			if not os.path.isdir(log_dir):
					os.mkdir('%s' % (log_dir))                
			log_dir ='%s/%s/' % (log_dir,tname)
			
			if not os.path.isdir(log_dir):
					os.mkdir('%s' % (log_dir))
			log_dir ='%s/%s/' % (log_dir,procname)
			if not os.path.isdir(log_dir):
					os.mkdir('%s' % (log_dir))
			test['log_dir'] = log_dir
					
			self._logger.info('Executing %s ...' % cmd.CommandText, __name__)
			cmd.ExecuteNonQuery()
			
			self._logger.info('File type: %s.' % test['config']['file_ext'] , __name__)
			if test['config']['file_ext']=='xls':
					
					self.SaveAsExcel()
			else:
					
					self.SaveAsText(cmd, test)
			
			
	def CreateFile(self, fname):
			print 'Creating File: %s' % fname
			fh= open(fname,'w')
			fh.close()

	def ExecSProc(self, val):
		test_home='C:/Program Files/IronPython 2.6/www'
		#self._pipeline_spec = self._environment.pipeline_spec()
		#self._logger.info(self._pipeline_spec)
		test =[]
		self._pipeline = self._environment.pipeline()
  
		#print '-----------------------------------------------'
		for test in self._pipeline['etldataflow']:
				 for k,v in test.iteritems():
						#con = self.getConnection(v)
						#pprint(k)
						#sys.exit(1)
						#self.execTest(con, v)
						self.runWorker(v)
		for  key  in self._conn.Keys:
				con= self._conn[key]

				if con.State.ToString() == 'Open':
						con.Close()
						self._logger.info('Connection %s is closed.' % key, __name__)
	def getConn(self, connector):
			#pprint((test))
			#connector = test['config']['connector']
			if  not self._conn.has_key(connector):
					self._conn[connector] =  Oracle.DataAccess.Client.OracleConnection(self.queryConnInfo(connector));
					self._conn[connector].Open();
					self._logger.info('Connected to %s' % connector, __name__);
			else:
					self._logger.info('Reusing connector %s.' % connector, __name__);
					self._logger.info('Connection state = %s.' % self._conn[connector].State.ToString(), __name__);
					
					if self._conn[connector].State.ToString() == 'Closed':
							self._conn[connector].Open();
							self._logger.info('Connection reopened successfully.', __name__);
			return self._conn[connector]                                
	def getConnection(self, test):
			#pprint((test))
			connector = test['config']['connector']
			if  not self._conn.has_key(connector):
					self._conn[connector] =  Oracle.DataAccess.Client.OracleConnection(self.queryConnectInfo(test));
					self._conn[connector].Open();
					self._logger.info('Connected to %s' % connector, __name__);
			else:
					self._logger.info('Reusing connector %s.' % connector, __name__);
					self._logger.info('Connection state = %s.' % self._conn[connector].State.ToString(), __name__);
					
					if self._conn[connector].State.ToString() == 'Closed':
							self._conn[connector].Open();
							self._logger.info('Connection reopened successfully.', __name__);
			return self._conn[connector]
	def RcToWorksheet(self,refCursor, ws):
		#clr.AddReferenceByName('Microsoft.Office.Interop.Excel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
		#from Microsoft.Office.Interop import Excel
		#from System import Type
		reader = refCursor.GetDataReader();
		#print reader.FieldCount
		for i in range(0, reader.FieldCount): 
			#print "%s\t" % reader.GetName(i),
			ws.Rows[1].Cells[i+1].Value2=reader.GetName(i)
			#print "%s\t" % ws.Rows[1].Cells[i+1].Value2
		#print
		j=2
		if 1:
				while reader.Read():
					for i in range(0, reader.FieldCount):
							ws.Rows[j].Cells[i+1].Value2=reader[i]
							#print "%s\t" % reader[i],
					#print
					#print
					j +=1
			  
	def RcToFile(self,refCursor, f, test):
		#sys.exit(1)
		reader = refCursor.GetDataReader();
		#pprint(dir(reader))
		delim=test['config']['delim']
		self._logger.info('Data delimeter = "%s"' % delim, __name__)
		self._logger.info('Number of columns in cursor = %d' % reader.FieldCount, __name__)
		j=1
		f.write('##,') 
		for i in range(0, reader.FieldCount): 
			f.write("%s%s" % (reader.GetName(i), delim))
			j +=1
		f.write("\n")
		j=1
		if 1:
				while reader.Read():
						f.write('%d,' % j)
						for i in range(0, reader.FieldCount):
								#print '%s%s' % (reader[i],delim),
								f.write("%s%s" % (reader[i],delim))
						#print ''
						f.write("\n")
						j +=1
		self._logger.info('%d records fetched.' % j, __name__)
		reader.Close()
		reader.Dispose()
			 

	def GetTimeStamp(self):
			timestamp = int(time.time())
			return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
	
	def ExecutePipeline(self):
		"""Executes Run method for all the tasks defined in the pipeline."""
		# Initialize Start Time.
		self._etl_start_time = self.GetTimeStamp()
		#self._logger.set_eventname(logger.ExtractEvent)
		self._logger.set_eventname(TestEvent)
		test_home='test/'
		worker =[] 
		#pprint(self._environment.pipeline())
		self._pipeline = self._environment.pipeline()
		#pprint(self._pipeline['worker'].keys())
		#for  wname,worker in self._pipeline['worker'].iteritems():
		for  worker in self._pipeline['worker']:
			#pprint(worker['attr']['name'])
			#pprint(worker)
			#sys.exit(1)
			self.runWorker(worker)
			
		for  key  in self._conn.keys():
			con= self._conn[key]

			if con.State.ToString() == 'Open':
				con.Close()
				self._logger.info('Connection %s is closed.' % key, __name__)
				
	def get_svar(self, vname):		
		confirm(len(vname)>0, 'Empty variiable name.')
		regexp=re.compile(r'\{\$([\w\_]+)\}')
		out=None
		if 1:			
			m = re.match(regexp, vname) 
			if m:
				print m.groups()
			out=os.environ.get('HOSTNAME')
		return out				
def ls(dir, logger):
	
	out=[]
	logger.log(dir)
	p1 = Popen(['ls', '-ltRh', dir], stdout=PIPE, stderr=PIPE)
	output=' '
	while output:
		output = p1.stdout.readline()
		out.append(output)

	status=p1.wait()
	if status!=0:
		logger.error(string.join(out,'\n'))	
		return (out,status)
	return (out,status)

def du(dir, logger):
	
	out=[]
	logger.log(dir)
	p1 = Popen(['du', '-h', dir], stdout=PIPE, stderr=PIPE)
	output=' '
	while output:
		output = p1.stdout.readline()
		out.append(output)

	status=p1.wait()
	if status!=0:
		logger.error(string.join(out,'\n'))	
		return (out,status)
	return (out,status)
	
def targz(dir,etlflow_name, logger):	
	out=[]
	logger.log(dir)
	print 'tar', '-zcvf', '%s/%s_LOGS.tar.gz' % (dir, etlflow_name), '%s/%s.*' % (dir, etlflow_name)
	p1 = Popen(['tar', '-zcvf', '%s/%s_LOGS.tar.gz' % (dir, etlflow_name), '%s/%s.*' % (dir, etlflow_name)], stdout=PIPE, stderr=PIPE)
	output=' '
	while output:
		output = p1.stdout.readline()
		out.append(output)
		#print 'out=',out
		print output
	status=p1.wait()
	#if status!=0:
	#	logger.error(string.join(out,'\n'))	
	#	return (out,status)
	return (out,status)

def rm(dir,etlflow_name, logger):	
	out=[]
	logger.log(dir)
	#print 'rm %s/%s.*' % (dir, etlflow_name)
	#p1 = Popen(['rm', '%s/%s.*' % (dir, etlflow_name)], stdout=PIPE, stderr=PIPE)
	import subprocess
	subprocess.call(['rm %s/%s.* -f' % (dir, etlflow_name)])
	return (out,status)
def get_etl_status(etl_status):
	if etl_status.has_key('FATAL') and int(etl_status['FATAL'])>0:
		return 'FATAL'
	if etl_status.has_key('ERR') and int(etl_status['ERR'])>0:
		return 'ERROR'		
	if etl_status.has_key('WARN') and int(etl_status['WARN'])>0:
		return 'WARNING'		
	return 'SUCCESS'
		

#zip test.zip tmp/logs/PARACCELL_POC/20110622-091855/*.*
def zip_log(dir,etlflow_name, logger):
	out=[]
	logger.log(dir)
	import zipfile
	import glob, os
	r=0
	status=0
	etls={}
	# open the zip file for writing, and write stuff to it
	zfn = '%s/%s_LOGS.zip' % (dir, etlflow_name)
	file = zipfile.ZipFile(zfn, "w")
	for name in glob.glob( '%s/%s.*' % (dir,etlflow_name)):
		#pprint(name)
			#zi = zipfile.ZipInfo(name)
			#pprint(zi)

		#file.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
		fn=name.encode('latin-1')
		ext =os.path.splitext(fn)[1].strip('.')
		if ext in ('WARN','ERR','LOG','FATAL'):
			
			file.write(fn, os.path.basename(fn), zipfile.ZIP_DEFLATED)
			#print name.encode('latin-1'), os.path.getsize(fn)
			#print os.path.basename(fn), os.path.splitext(fn)[1].strip('.')
			
			etls[ext]=os.path.getsize(fn)
			#print etls
	
	file.close()
	#print 'returning', out,status,get_etl_status(etls) 
	return (out,status,get_etl_status(etls))

	
def mail(email, table, logger, etl_pipeline=None):
	SENDMAIL = "/usr/sbin/sendmail" # sendmail location
	import os
	p = os.popen("%s -t" % SENDMAIL, "w")
	p.write("From: %s\n" % email)
	p.write("To: %s\n" % email)
        ex_status='SUCCESS'
	etlflow_name=table
        osuser=getpass.getuser()
	host=os.uname()[1]
	basedir=os.getcwd()
	if etl_pipeline:
                #fname = logger.logfile_name('INFO')
                #if fname:
                #       f = open(logger.logfile_iname('INFO'), "r")
		etlflow_name=etl_pipeline._pipeline_name
                dirn =  ' %s/%s.*' % (logger.get_logdir(), etlflow_name)

                (r, status, etls) = zip_log(logger.get_logdir(),etlflow_name,logger)

                zf ='%s/%s_LOGS.zip' % (logger.get_logdir(),etlflow_name)
                if 'SUCCESS' not in etls:
                        ex_status=etls

	p.write("Subject: %s: %s\n" % (ex_status, table))
	p.write("\n") # blank line separating headers from body
	#p.write("Please, find log file attached.\n")
	p.write("%s" % '#'*80)
	p.write(" \n")
	if etl_pipeline:
		p.write("# User: 	%s@%s\n" % (osuser, host))
		p.write("# Base: 	%s\n" % (basedir))
		p.write("# Pipeline:	%s\n" % etl_pipeline._environment._pipeline_flags.pipeline) 
		p.write("# Client:	%s\n" % etl_pipeline._environment._pipeline_flags.pipeline_spec) 
		p.write("# applog: %s\n" % logger.logfile_name('INFO'))
		p.write("# syslog: %s\n" % logger.logfile_name('SYS'))
		(r, status) = ls(logger.get_logdir(),logger)
		p.write('\n')
		if not status:
			#p.write("%s\n" % logger.get_logdir())
			print string.join(r,'')
			p.write(string.join(r,''))
	else:
		p.write("# %s\n" % logger.logfile_name())
	print 'log.INFO = %s' % logger.logfile_name('INFO')
	print 'log.SYS = %s' % logger.logfile_name('SYS')	
	#print 'logger.logfile_name() = ', logger.logfile_name()
	p.write("%s" % '#'*80)
	p.write(" \n")
	f=None
	ex_status='SUCCESS'
	if etl_pipeline:
		#fname = logger.logfile_name('INFO')
		#if fname:
		#	f = open(logger.logfile_name('INFO'), "r")
                dirn =  ' %s/%s.*' % (logger.get_logdir(), etlflow_name)

                (r, status, etls) = zip_log(logger.get_logdir(),etlflow_name,logger)

                zf ='%s/%s_LOGS.zip' % (logger.get_logdir(),etlflow_name)
                if 'SUCCESS' not in etls:
			ex_status=etls
	else:
		fname=logger.logfile_name('SYS')
		#print 'logger.logfile_name(): ',logger.logfile_name()
		#print 'logger._singleton_logger.logfile_name(): ',logger._singleton_logger.logfile_name()
		if fname:
			f = open(logger.logfile_name(), "r")
	if f:
		p.write("%s\n" % f.read())
	sts = p.close()
	print "Sendmail exit status", sts
	return sts

def mail_attch(email, etlflow_name, logger, etl_pipeline=None):
	SENDMAIL = "/usr/sbin/sendmail" # sendmail location
	import os
	p=[]
	p.append("%s%s" % (' ','#'*80))
	p.append("\n")
	if etl_pipeline:
		p.append("# %s\n" % etl_pipeline._environment._pipeline_flags.pipeline) 
		p.append("# %s\n" % etl_pipeline._environment._pipeline_flags.pipeline_spec) 
		p.append("# applog: %s\n" % logger.logfile_name('INFO'))
		p.append("# syslog: %s\n" % logger.logfile_name('SYS'))
		(r, status) = ls(logger.get_logdir(),logger)
		p.append('\n')
		if not status:
			#p.write("%s\n" % logger.get_logdir())
			print string.join(r,'')
			p.append(string.join(r,''))
		if os.path.isdir('%s/data' % logger.get_logdir()):
			(r, status) = du('%s/data' % logger.get_logdir(),logger)
			p.append('\n')
			if not status:
				#p.write("%s\n" % logger.get_logdir())
				print string.join(r,'')
				p.append(string.join(r,''))			
	else:
		p.append("# %s" % logger.logfile_name())

	p.append("%s" % '#'*80)
	#p.append(" \n")
	f=None
	etls='SUCCESS'
	files=[]
	if etl_pipeline:
	        import glob, os
		dirn =  ' %s/%s.*' % (logger.get_logdir(), etlflow_name)

		(r, status, etls) = zip_log(logger.get_logdir(),etlflow_name,logger)

		zf ='%s/%s_LOGS.zip' % (logger.get_logdir(),etlflow_name)
		if 'SUCCESS' not in etls:
			files.append(zf)
		else:
			os.remove(zf)
			
	sendMail(email.split(';'), "%s: %s\n" % (etls,etlflow_name) ,string.join(p),files)
	return 0
	#sts = p.close()
	#print "Sendmail exit status", sts
	#return sts
	


def sendMail(to, subject, text, files=[],server="localhost"):
	assert type(to)==list
	assert type(files)==list
	fro = "Test <AlexBuzunov@gmail.com>"

	msg = MIMEMultipart()
	msg['From'] = fro
	msg['To'] = COMMASPACE.join(to)
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject

	msg.attach( MIMEText(text) )

	for file in files:
		part = MIMEBase('application', "octet-stream")
		part.set_payload( open(file,"rb").read() )
		Encoders.encode_base64(part)
		part.add_header('Content-Disposition', 'attachment; filename="%s"'
					   % os.path.basename(file))
		msg.attach(part)

	smtp = smtplib.SMTP(server)
	smtp.sendmail(fro, to, msg.as_string() )
	smtp.close()



	

def PrintException(logger, emailed):
		#logger=etl_pipeline._logger
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
												output.write('\t%s=%s\r\n' % (key, str(value)))
										except:
												output.write('[UNPRINTABLE VALUE]\n')
				except Exception:
						traceback.print_exc()

		finally:
				if output:
						#pprint (dir(logger))
						#sys.stderr.write(output.getvalue())
						logger.warning(output.getvalue())
						if logger:
							if not emailed:
								
								#while threading.activeCount()>1:
									#print '------count=',  threading.activeCount()
									#time.sleep(1)
								email=None
								name= None
								if etl_pipeline:
									logger.info(output.getvalue())
									email= environment.get_email_to('EMAIL_TO')
									name= etl_pipeline._pipeline['name']
									print 'Sending to %s\n' % email
								
									#status=mail_attch(email, name, logger, etl_pipeline)								
								else:
									logger.sys(output.getvalue())
									email = 'AlexBuzunov@gmail.com'	
									name= 'FATAL'
									print 'Sending to %s\n' % email
								
									#status=mail_attch(email, name,logger)	
								emailed=1
								
							else:						
								logger.fatal(output.getvalue())
						output.close()


		
if __name__ == '__main__':
	etl_logger = None
	emailed =0
	etl_pipeline=None
	#singleton_logger.sys('test')
	#try:
	if 1:
		
		flags = pipeline_flags.PipelineFlags(singleton_logger)
		environment = Environment(flags, singleton_logger)
		#print singleton_logger.logfile_name()
		#sys.exit(1)
		etl_pipeline = EtlPipeline(flags, environment,singleton_logger)

		etl_logger = etl_pipeline._logger

		etl_pipeline.ExecutePipeline()
		print etl_logger.getElapsedSec()
		if 1:
			while threading.activeCount()>1:
				print '%s: thread pool count = %s' % (etl_logger.getElapsedSec() , threading.activeCount())
				time.sleep(1)
		#print("%s"  %(etl_logger.ins_filename))
		if 0:
			cmd = '/opt/netezzaClient/bin/nzsql  -U ab95022 -W ab95022 -h b4-netezza-01 -p 5480 -d map  -f "%s"' % etl_logger.ins_filename
			print cmd
			cmd = '/opt/netezzaClient/bin/nzsql  -U ab95022 -W netezza_map_12 -h lab7-netezza12-vip -p 5480 -d map_12  -f '
			print cmd
			fsize= os.path.getsize(etl_logger.ins_filename)
			#print cmd, fsize
			if 0:
				if fsize>0:
					print os.system(cmd)
				else:
					etl_logger.info('Insert log %s is empty.' % etl_logger.ins_filename )
		etl_logger.info('ETL finished.')
		email= environment.get_email_to('EMAIL_TO')
		if email:

			#print 'Sending to %s\n' % email
			if etl_pipeline:
				name= etl_pipeline._pipeline_name
				print 'sending email to %s' % email
				mail(email, name, etl_pipeline._logger, etl_pipeline)
			else:
				name= environment._pipeline_name
				mail(email, name, singleton_logger, None)
			emailed=1
	#var = etl_pipeline.get_svar('HOSTNAME')
	#print var
	#except Exception, e:

		#if etl_pipeline:
		#	PrintException(etl_logger, emailed)
			
		#else:
			#print e
			
			#print singleton_logger.logfile_name()
			#PrintException(singleton_logger, emailed)
			#raise e
			#pprint(environment)
		print 'emailed=',emailed

		#raise e


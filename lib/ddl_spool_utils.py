#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all DDL spool routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from subprocess import Popen, PIPE
from app_utils import app_utils

STACKTRACE_MAX_DEPTH = 2



class ddl_spool_utils(app_utils):
	"""A class for DDL spool."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def spool_ddl(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		#template = self.get_template(etl_object, logger)
		template = self.get_spool_template(etl_object, logger)
		pprint(template)
		#sys.exit(1)
		assert  len(template)>0, 'Template batch is missing or misconfigured.'
		def_conn=self.get_connector(self._p['FROM_DB'])
		status=0
		#pprint(template)
		if 1:
			self._default_login=self.get_ora_login(def_conn)
			assert len(self._default_login)>0, 'Cannot set default login.'
			from_db = self._pp['FROM_DB']
			workn =self._pp['WORKER_NAME'].strip()
			if template:
				#get object list
				logger.info('#### START Getting object list.' )												
				#pprint(template)
				regexp=re.compile(r'[\s|\ ]?(\w+)[\s|\ ]+(\w+)[\s|\ ]+(\w+)[\s|\ ]?')
				q= "set heading off pagesize 0 line 300 echo off termout off show off feedback off\n%s" % template
				#print q 
				#sys.exit(1)
				(r, status) = self.do_query(from_db, q,0,regexp)
				#pprint(r)
				
				logger.info('#### END Getting object list.' )
				for obj in r:
					#pprint(obj)
					if 1:
						#to_tab= self.get_to_tab(string.split(tab,'.'))
						from_obj=obj[0]
						#print from_tab
						if 1:
							#(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
							if 1:
								#loop all partitions

								if  0: #self.is_set('PARTITION'):
									pts = self.get_prt_set(from_db, from_tab, self._p['PARTITION'])
									#pprint(pts)
									#sys.exit(1)
									assert len(pts)>0, 'Could not find partitions for table  %s [%s]' % (obj, self._p['PARTITION'])
									for pt in pts:
										
										if pt:
											self._p['PARTITION']=pt
											self._pp['PARTITION']=pt
											status=0
											logger.info('#### START spool of %s[%s][%s]' % (workn,obj,pt))												
											#(r, status) = self.do_spool(from_db, from_tab)
											logger.info('#### END spool of %s[%s][%s].' % (workn,obj,pt))
										#sys.exit(1)
								else:
									status=0
									logger.info('#### START spool of %s[%s] no partiton ' % (workn,obj))												
									(r, status) = self.do_spool_ddl(from_db, obj)
									logger.info('#### END spool of %s[%s] no partition.' % (workn,obj))
		
		

								if status==0:
									logger.info('Spool of %s[%s] completed successfully.' % (workn,obj))
							else:
								logger.warning('#### Skipping spool of %s[%s].' % (workn,obj))
								#logger.warning("Truncate of table %s failed." % tab)
						else:
							logger.warning('#### Skipping spool of %s[%s].' % (workn,obj))
							
					self.cleanup()
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],obj )
		
		return 0
	def do_spool_ddl(self, from_db, from_t):
		f = ""
		out=[]
		err=[]
		len(from_db)>0, 'Source login is not set.'
		status=0
		drop_dml=''
		if self.is_set('IF_ADD_DROP_DML'):
			drop_dml= """SELECT 'DROP %s %s.%s' OBJ_DDL FROM DUAL\n/\nSELECT '/' OBJ_DDL FROM DUAL\n/\n""" % (from_t[1],from_t[0], from_t[2])
			#print drop_dml
		if not status:
			q='SELECT '
			if 1: #column word_wraapped
				
				wwp = "COLUMN OBJ_DDL format a121 WORD_WRAPPED\n"
				q= """%s\n set head off line 32766 long 10000000 pages 0 newpage 0 echo off feedback off define off
set serveroutput off	
%s
select dbms_metadata.get_ddl(
  object_type =>'%s',
  name=>'%s',
  schema=>'%s') OBJ_DDL
from dual;\nexit;\n""" % (wwp,drop_dml,from_t[1],from_t[2], from_t[0])
			self._logger.sql(q)
			obj= '.'.join(from_t)
			#print obj
			#sys.exit(1)
			if 1:
				sqdir= '%s/sql' % self._logger.get_logdir()
				sqfn='%s/%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],obj)
				if not os.path.isdir(sqdir):
					try:
						os.mkdir(sqdir) 
					except Exception, e:
						print 'Created in other thread.', e.strerror
				sqf = open(sqfn, "w")
				sqf.write(q)
				sqf.close()
			ddldir= '%s/ddl' % self._logger.get_logdir()
			if not os.path.isdir(ddldir):
				os.mkdir(ddldir) 
			ext='ddl'
			if self.p_if('IF_COMPRESSED_SPOOL'):
				ext='gz'
			gzfn = '%s/%s.%s.%s' % (ddldir,self._pp['WORKER_NAME'],obj,ext)
			if self.is_set('PARTITION'):
				gzfn = '%s/%s.%s.%s.%s' % (ddldir,self._pp['WORKER_NAME'],obj,self._pp['PARTITION'],ext)
			log = open(gzfn, "w")
			self._result.append(gzfn)
			#self._result.append(gzfn)
			self._wc['DDL_LOC'] = self._result
			self._gwc['DDL_LOC'] = self._result
			#print q
			#sys.exit(1)
			p1 = Popen(['echo', '@%s' % sqfn], stdout=PIPE, stderr=PIPE)
			#print from_db
			#IF_COMPRESSED_SPOOL
			if self.p_if('IF_COMPRESSED_SPOOL'):
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
				self._logger.info('Starting UNCOMPRESSED spool')
				p2 = Popen([ 'sqlplus',  '-S', from_db], stdin=p1.stdout, stdout=log , stderr=PIPE
				)
				status =0
				out=[]
				err=[]
				if 1:
					status=p2.wait()
					if status==0:
						self._logger.info('spool status =%s' % status)
					if status==1:
						self._logger.error('spool status =%s' % status)
						output=' '
						while output:
							output = p2.stderr.readline()
							err.append(output)
							print output
							self._logger.warning(output.rstrip())
						status=p2.wait()
						if status==1:
							self._logger.error(string.join(err,'\n'))						
					if status==2:
						self._logger.warning('spool status =%s' % status)
					

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
		
	def get_spool_template(self,  etl_object, logger,obj_type='TABLE',):
		out=''
		if obj_type.upper() in 'TABLE':
			template = self.get_template(etl_object, logger)
			print '#'*60
			print template
			#tab=template.strip().split('.')
			#print '#'*60
			#print tab
			out =template
			if 0:
				out="""
SELECT OWNER, 'TABLE' OBJECT_TYPE, table_name OBJECT_NAME 
  FROM all_tables 
 WHERE  owner='%s' 
   AND table_name IN ('%s') ;""" % tuple(tab)
		assert out, 'Spool template is not set'
		return out

	
	def export(self):
		return ('DDL_LOC',self._result)		

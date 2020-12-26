#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all data spool routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re, string
from pprint import pprint
from subprocess import Popen, PIPE
from app_utils import app_utils
import  pickle

STACKTRACE_MAX_DEPTH = 2



class data_spool_utils(app_utils):
	"""A class for data spool."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes the extracter.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)

	def spool(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		template = self.get_mtt_template(etl_object, logger)
		#pprint(template)
		#sys.exit(1)
		assert len(template)>0, 'Template batch is missing or misconfigured.'
		#(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		def_conn=self.get_connector(self._p['FROM_DB'])
		status=0
		self._gwc['OUTPUT_FILE']=[]
		if 1:
			self._default_login=self.get_ora_login(def_conn)
			assert len(self._default_login)>0, 'Cannot set default login.'
			from_db = self._pp['FROM_DB']
			#to_db= self._pp['TO_DB']
			#pprint(self._pp)
			#print template
			#sys.exit(1)
			#tab=template #self._pp['WORKER_NAME']
			workn =string.strip(self._pp['WORKER_NAME'])
			if template:
				self._pp['_COLUMNS']={}
				self._pp['_TABLE']=[]
				self._pp['_OUTPUT_FILE']={}
				for tab in set(template):
					if 1:
						#to_tab= self.get_to_tab(string.split(tab,'.'))
						from_tab=self.get_from_tab(string.split(string.strip(tab),'.'))
						#print from_tab
						if 1:
							
							#(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
							if 1:
								#loop all partitions

								if  self.is_set('PARTITION'):
									pts = self.get_prt_set(from_db, from_tab, self._p['PARTITION'])
									#pprint(pts)
									#sys.exit(1)
									assert len(pts)>0, 'Could not find partitions for table  %s [%s]' % (tab, self._p['PARTITION'])
									for pt in pts:
										
										if pt:
											self._p['PARTITION']=pt
											self._pp['PARTITION']=pt
											status=0
											logger.info('#### START spool of %s[%s][%s]' % (workn,tab,pt))												
											(r, status) = self.do_spool(from_db, from_tab)
											logger.info('#### END spool of %s[%s][%s].' % (workn,tab,pt))
										#sys.exit(1)
								else:
									status=0
									logger.info('#### START spool of %s[%s] no partiton ' % (workn,tab))												
									(r, status) = self.do_spool(from_db, from_tab)
									logger.info('#### END spool of %s[%s] no partition.' % (workn,tab))
		
		

								if status==0:
									logger.info('Spool of %s[%s] completed successfully.' % (workn,tab))
								#self.save_metadata(etl_object, logger)

							else:
								logger.warning('#### Skipping spool of %s[%s].' % (workn,tab))
								#logger.warning("Truncate of table %s failed." % tab)
						else:
							logger.warning('#### Skipping spool of %s[%s].' % (workn,tab))
							
					self.cleanup()
				self._gwc['LATEST']={'COLUMNS':self._pp['_COLUMNS'],
									 'FLAGS':self._FLAGS, 
									 'TABLE':self._pp['_TABLE'],
									 'OUTPUT_FILE':self._pp['_OUTPUT_FILE']}
				#pprint(self._gwc['LATEST'])
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0		
			
	def get_mtt_template(self, etl_object, logger):
		""" Multi-table template """
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
		template= etl_object['node']['sql_template']['data'].strip()
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
		return re.findall('([\w\d\_\.]+)', template) 
	
	def do_spool(self, from_db, from_t):
		f = ""
		out=[]
		err=[]
		tab = None
		assert  len(from_db)>0, 'Source login is not set.'
		#assert  len(to_db)>0, 'Target login is not set.')
		
		#(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print from_db, from_t
		#sys.exit(1)
		(r_from,status) = self.get_columns(from_db, from_t)
		pprint(r_from)
		print from_t
		sys.exit(1) 
		if not status:
			ft = self.p('FIELD_TERMINATOR').strip("'")
			lt = self.p('LINE_TERMINATOR').strip("'") 
			#to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_from,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#pprint(self.ckey2cols(r_from))
			#sys.exit(1)
			ca=self.ckey2cols(r_from)
			print ca
			sys.exit(1) 
			#pprint(ca)
			cl =  "%s||'%s'" % (string.rstrip(string.join(ca,"||'%s'||\n " % ft),"||'%s'||\n " % ft),lt) 
			#sys.exit(1)
			#ins = "'('''||%s||''');'" % (string.rstrip(string.join(r_from,"||''',',''''||"),"||''',',''''||"))
			#pprint(ins)
			#sys.exit(0)
			#cl =  "%s||%s" % (string.join(r_from,"||%s||\n" % ft),lt)
			llen=32767
			orderby=''
			if 'ORDER_BY' in self._pp:
				orderby = 'ORDER BY %s' % self._pp['ORDER_BY']
			#sys.exit(1)
			q=''
			if 0: #column word_wraapped 
				wwp = "COLUMN %s WORD_WRAPPED\n" % string.join(ca,' WORD_WRAPPED\n COLUMN ')
				q= "%s set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='DD-MON-RRRR HH.MI.SS'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL1(%s)*/ %s FROM %s %s;\nexit;\n" % (wwp, llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			else:
				q= "set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nALTER SESSION SET workarea_size_policy = manual\n/\nALTER SESSION SET sort_area_size = 524288000\n/\nALTER SESSION SET sort_hash_size = 524288000\n/\nalter session set NLS_DATE_FORMAT='DD-MON-RRRR HH.MI.SS AM'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='DD-MON-RRRR HH.MI.SSXFF AM'\n/\n\nSELECT %s FROM %s %s %s;\nexit;\n" % (llen,    cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp,{'_PARTITION':self._pp.get('PARTITION',None)}),orderby)
				#q= "set line %s arraysize 5000\nalter session set NLS_DATE_FORMAT='DD-MON-YY'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='DD-MON-RR HH.MI.SSXFF AM'\n/\n\nSELECT %s FROM %s %s;\nexit;\n" % (llen,    cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			#set timing off pagesize 0 heading off line 2000 long 128000  feedback off\ncolumn object_ddl format a121 word_wrapped
			pprint(q)
			sys.exit(1)
			self._logger.sql(q)
			#pprint(q)
			tab= string.join(from_t,'.')
			#sys.exit(1)
			sqdir= '%s/sql' % self._logger.get_logdir()
			sqfn='%s/%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],tab)
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
			(gzfn, fexists)=self.get_log_fn('data','data',tab)
			log = None
			if not fexists:
				if not self.p_if('IF_SKIP_HEADER'):
					header = "|".join(ca)
					log = open(gzfn, "w")
					log.write("%s\n" % header)
					log.close()
					#sys.exit(1)
			
			log = open(gzfn, "a")

			#print sqfn
			p1 = Popen(['echo', ' @%s' % sqfn], stdout=PIPE, stderr=PIPE)
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
				p2 = Popen([ 'sqlplus', '-S', from_db], stdin=p1.stdout, stdout=log , stderr=PIPE
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
			#self._gwc['OUTPUT_FILE'].append(gzfn)
			assert  tab,'Table name is undefined'
			if '_OUTPUT_FILE' not in self._pp:
				self._pp['_OUTPUT_FILE']={}
			if '_COLUMNS' not in self._pp:				
				self._pp['_COLUMNS']={}
			if '_TABLE' not in self._pp:
				self._pp['_TABLE']=[]
			self._pp['_OUTPUT_FILE'][tab]=gzfn
			self._pp['_COLUMNS'][tab]=r_from
			self._pp['_TABLE'].append(tab)
			#self._p['PIPELINE_FLAGS'] = self._FLAGS
			#self
			self.save_metadata(from_db,from_t)

		else:
			self._logger.warning('Cannot fetch common columns.')
		
		return (out,status)
	def save_metadata(self,from_db,from_t):
		ext='meta'
		metadir= '%s/meta' % self._logger.get_logdir()
		tab= string.join(from_t,'.')
		if not os.path.isdir(metadir):
			os.mkdir(metadir) 
		metafn = '%s/%s.%s.%s' % (metadir,self._pp['WORKER_NAME'],tab,ext)
		if self.is_set('PARTITION'):
			metafn = '%s/%s.%s.%s.%s' % (metadir,self._pp['WORKER_NAME'],tab,self._pp['PARTITION'],ext)	
		output = open(metafn, 'wb')	
		pickle.dump({'CONFIG':self._p,'COLUMNS':self.get_columns(from_db, from_t),'FLAGS':self._FLAGS, 'TABLE':from_t}, output)
		output.close()
		
		pkl_file = open(metafn, 'rb')
		data1 = pickle.load(pkl_file)
		#pprint(data1)
	def spool_query_data(self, etl_object, logger):
		""" Spool query using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		template = self.get_template(etl_object, logger).strip().strip(';')
		pprint(template)
		#sys.exit(1)
		assert len(template)>0, 'Template batch is missing or misconfigured.'
		#(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		def_conn=self.get_connector(self._p['FROM_DB'])
		status=0
		self._gwc['OUTPUT_FILE']=[]
		if 1:
			self._default_login=self.get_ora_login(def_conn)
			assert len(self._default_login)>0, 'Cannot set default login.'
			from_db = self._pp['FROM_DB']
			#to_db= self._pp['TO_DB']
			#pprint(self._pp)
			#print template
			#sys.exit(1)
			#tab=template #self._pp['WORKER_NAME']
			workn =string.strip(self._pp['WORKER_NAME'])
			if template:
				self._pp['_COLUMNS']={}
				self._pp['_TABLE']=[]
				self._pp['_OUTPUT_FILE']={}
				#for tab in set(template):
				if 1:
					tab='%s.%s' % ((self._pp.get('FROM_SCHEMA'), self.get_temp_table_name()))
					if 1:
						#to_tab= self.get_to_tab(string.split(tab,'.'))
						#from_tab=self.get_from_tab(string.split(string.strip(tab),'.'))
						#print from_tab
						if 1:
							
							#(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
							if 1:
								status=0
								logger.info('#### START query spool of %s[%s] no partiton ' % (workn,tab))												
								(r, status) = self.do_query_spool(from_db, template)
								logger.info('#### END query spool of %s[%s] no partition.' % (workn,tab))
		
		

								if status==0:
									logger.info('Query spool of %s[%s] completed successfully.' % (workn,tab))
								#self.save_metadata(etl_object, logger)

							else:
								logger.warning('#### Skipping spool of %s[%s].' % (workn,tab))
								#logger.warning("Truncate of table %s failed." % tab)
						else:
							logger.warning('#### Skipping spool of %s[%s].' % (workn,tab))
							
					self.cleanup()
				self._gwc['LATEST']={'COLUMNS':self._pp['_COLUMNS'],
									 'FLAGS':self._FLAGS, 
									 'TABLE':self._pp['_TABLE'],
									 'OUTPUT_FILE':self._pp['_OUTPUT_FILE']}
				#pprint(self._gwc['LATEST'])
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0		
	def do_query_spool(self, from_db, qry):
		f = ""
		out=[]
		err=[]
		tab = None
		assert  len(from_db)>0, 'Source login is not set.'
		assert  len(qry)>0, 'Query is not set.'
		#assert  len(to_db)>0, 'Target login is not set.')
		if_compress = self.p_if('IF_COMPRESSED_SPOOL')
		#(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		#print from_db, from_t
		#print qry
		#sys.exit(1)
		(r_from,status) = self.get_query_columns(from_db, qry)
		#pprint(r_from)
		#sys.exit(1)
		from_t= list((self._pp.get('FROM_SCHEMA'), self.get_temp_table_name()))
		if not status:
			ft = self.p('FIELD_TERMINATOR').strip("'")
			lt = self.p('LINE_TERMINATOR').strip("'") 
			#to_tab= string.join(self.get_to_tab(to_t),'.')
			#cl = "'\"'||%s||'\"'" % string.join(r_from,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#pprint(self.ckey2cols(r_from))
			#sys.exit(1)
			ca=self.ckey2cols(r_from)
			#pprint(ca)
			cl =  "%s||'%s'" % (string.rstrip(string.join(ca,"||'%s'||\n " % ft),"||'%s'||\n " % ft),lt)
			
			#sys.exit(1)
			#ins = "'('''||%s||''');'" % (string.rstrip(string.join(r_from,"||''',',''''||"),"||''',',''''||"))
			#pprint(ins)
			#sys.exit(0)
			#cl =  "%s||%s" % (string.join(r_from,"||%s||\n" % ft),lt)
			llen=32767
			orderby=''
			if 'ORDER_BY' in self._pp:
				orderby = 'ORDER BY %s' % self._pp['ORDER_BY']
			#sys.exit(1)
			q=''
			if 0: #column word_wraapped
				wwp = "COLUMN %s WORD_WRAPPED\n" % string.join(ca,' WORD_WRAPPED\n COLUMN ')
				q= "%s set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nalter session set NLS_DATE_FORMAT='DD-MON-RR HH.MI.SS'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='yyyy/mm/dd hh24:mi:ss'\n/\nSELECT /*+PARALLEL1(%s)*/ %s FROM %s %s;\nexit;\n" % (wwp, llen,   from_t[1], cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			else:
				q= "set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nALTER SESSION SET workarea_size_policy = manual\n/\nALTER SESSION SET sort_area_size = 524288000\n/\nALTER SESSION SET hash_area_size = 524288000\n/\nalter session set NLS_DATE_FORMAT='DD-MON-RRRR HH.MI.SS AM'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='DD-MON-RRRR HH.MI.SSXFF AM'\n/\n\nSELECT %s FROM (%s) %s %s;\nexit;\n" % (llen,    cl, qry, self.get_q_options(self._pp,{'_PARTITION':self._pp.get('PARTITION',None)}),orderby)
				#q= "set head off line %s pages 0 newpage 0 echo off feedback off define off feed off arraysize 5000\nALTER SESSION SET workarea_size_policy = manual\n/\nALTER SESSION SET sort_area_size = 524288000\n/\nALTER SESSION SET sort_hash_size = 524288000\n/\nalter session set NLS_DATE_FORMAT='DD-MON-RR HH.MI.SS AM'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='DD-MON-RR HH.MI.SSXFF AM'\n/\n\nSELECT %s FROM %s %s %s;\nexit;\n" % (llen,    cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp,{'_PARTITION':self._pp.get('PARTITION',None)}),orderby)
				#q= "set line %s arraysize 5000\nalter session set NLS_DATE_FORMAT='DD-MON-YY'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='DD-MON-RR HH.MI.SSXFF AM'\n/\n\nSELECT %s FROM %s %s;\nexit;\n" % (llen,    cl, string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp))
			#set timing off pagesize 0 heading off line 2000 long 128000  feedback off\ncolumn object_ddl format a121 word_wrapped
			pprint(q)
			#sys.exit(1)
			self._logger.sql(q)
			#pprint(q)
			tab= string.join(from_t,'.')
			#sys.exit(1)
			sqdir= '%s/sql' % self._logger.get_logdir()
			sqfn='%s/%s.%s.sql' % (sqdir,self._pp['WORKER_NAME'],tab)
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
			
			(spoolfn, fexists)=self.get_log_fn('data','data',tab)
			#print 'after', spoolfn
			log = None
			if not fexists:
				if not self.p_if('IF_SKIP_HEADER'):
					assert self._pp.get('FIELD_TERMINATOR'), 'FIELD_TERMINATOR is not set'
					term =self._pp.get('FIELD_TERMINATOR').strip().strip("'")
					header = term.join(ca)
					log = open(spoolfn, "w")
					log.write("%s\n" % header)
					#log.flash()
					log.close()
					#print spoolfn
					
					if if_compress: #pass or write comressed header
						status = os.system('gzip %s' % spoolfn)
						#print status
						assert not status, 'Header compress failed.'
							
						spoolfn = '%s.gz' % spoolfn
			#print spoolfn
			#sys.exit(1)
			log = open(spoolfn, "a")

			#print sqfn
			p1 = Popen(['echo', ' @%s' % sqfn], stdout=PIPE, stderr=PIPE)
			#print from_db
			#IF_COMPRESSED_SPOOL
			if if_compress:
				p2 = Popen([ 'sqlplus', '-S', from_db], stdin=p1.stdout, stdout=PIPE , stderr=PIPE
				)
				status =0
				out=[]
				err=[]

				if 1:				
					p3 = Popen(['gzip', '-c'], 
					stdin=p2.stdout, stdout=log, stderr=PIPE)
					#p3.wait()
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
						#out.append(output)
						print output
						#self._logger.info(output.rstrip())
					
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
				p2 = Popen([ 'sqlplus', '-S', from_db], stdin=p1.stdout, stdout=log , stderr=PIPE
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
			#self._gwc['OUTPUT_FILE'].append(spoolfn)
			assert  tab,'Table name is undefined'
			if '_OUTPUT_FILE' not in self._pp:
				self._pp['_OUTPUT_FILE']={}
			if '_COLUMNS' not in self._pp:				
				self._pp['_COLUMNS']={}
			if '_TABLE' not in self._pp:
				self._pp['_TABLE']=[]
			self._pp['_OUTPUT_FILE'][tab]=spoolfn
			self._pp['_COLUMNS'][tab]=r_from
			self._pp['_TABLE'].append(tab)
			#self._p['PIPELINE_FLAGS'] = self._FLAGS
			#self
			self.save_metadata(from_db,from_t)

		else:
			self._logger.warning('Cannot fetch common columns.')
		
		return (out,status)		
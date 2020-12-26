#!/usr/bin/python2.4
#
# Copyright 20012 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""This module contains all hierarchy transformation routines
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys, os, re, string, time
from pprint import pprint
from subprocess import Popen, PIPE
from threading import Thread,activeCount
from lib.thread_pool import  ThreadPool
from app_utils import app_utils
from index_utils import index_utils



STACKTRACE_MAX_DEPTH = 2



class copy_utils(app_utils,index_utils):
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

	def copy_table(self, etl_object, logger):
		""" Runs copy using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		#print tmpl_batch
		(r,status)=(None, None)
		out=[]
		
		assert  len(tmpl_batch)>0 & (not status), 'Template batch is missing or misconfigured.'
		(def_conn,status)=self.get_default_conn(self.get_connector(self._p['FROM_DB']),self.get_connector(self._p['TO_DB']))
		nosh = self.is_set('NUM_OF_SHARDS')
		if status and 0:
			logger.error('Dual inline connectors are not supported by SQL*Plus COPY.')
			logger.warning('#### Skipping batch processing.')
			logger.info("COPY of batch %s has failed." % etl_object['name'])
		else:
			self._default_login=self.get_ora_login(def_conn)
			assert  len(self._default_login)>0, 'Cannot set default login.'
			from_db = self._pp['FROM_DB'].strip(' ').replace(' ','')
			to_db= self._pp['TO_DB'].strip(' ').replace(' ','')
			for tab in tmpl_batch:
				if 1:
					#print tab
					#print tab.split('.')
					#sys.exit(1)
					to_tab= self.get_to_tab(tab.split('.'))
					from_tab=self.get_from_tab(tab.split('.'))
					#print from_tab, to_tab
					#sys.exit(1)
					if 1:

						status=0
					
						if status==0:
							delta='DATE_RANGE_DELTA'
							if self.is_set(delta):
								delta_type="PARTITON_RANGE" 
								#partition_interval_type="BIWEEKLY" 
								#truncate target partition
								logger.info('#### START truncate of %s.' % etl_object['name'])

								regexp=re.compile(r'[\s|\ ]?(\w+)[\s|\ ]+(\w+)[\s|\ ]+(\w+)')
								pq="""set heading off line %s echo off feedback off termout off colsep | feed off newpage 0 pagesize 99 serveroutput off show off trim on
								%s""" % (200,self.get_part_q(from_tab, self.p(delta)))
								(out, status) = self.do_query(from_db, pq,0,regexp)
								#pprint(out)
								print len(out)
								gpts={}
								for i in out:
									if gpts.has_key(i[0]):
										pass
									else:
										gpts[i[0]]={}
									if gpts[i[0]].has_key(i[1]):
										pass
									else:
										gpts[i[0]][i[1]]=[]										
									gpts[i[0]][i[1]].append(i[2])										
										
								#pprint(gpts)
								pts=gpts[str(from_tab[0])][str(from_tab[1])]
								#pprint(pts)
								range=self.p(delta)

								#ptns=self.get_pts(pts)	
								for ptsn in pts:
									t="ALTER TABLE %s TRUNCATE PARTITION (%s);" % (string.join(to_tab,'.'),ptsn)	
									print t								
									
									logger.info('#### START truncate of %s PARTITION (%s).' % (tab,ptsn))
									(r, status) = self.do_query(to_db, t,0)
									logger.info('#### END truncate of %s PARTITION (%s).' % (tab,ptsn))						
									self.set_p('PARTITION',ptsn)
									logger.info('#### START copy of %s PARTITION (%s).' % (tab,ptsn))		
									(r, status) = self.do_load(from_db, from_tab, to_db, to_tab)
									logger.info('#### END copy of %s PARTITION (%s).' % (tab,ptsn))
									#sys.exit(1)

							else: #full load
								#ptn =
								if  self.is_set('PARTITION') or self.is_set('SUBPARTITION'):
									pprint(self._pp)
									#sys.exit(1)
									assert not (self.is_set('PARTITION') and self.is_set('SUBPARTITION')), 'You cannot specify both PARTITION and SUBPATITION.'
									pts=None 
									spts=None
									if self.is_set('PARTITION'):
										pts = self.get_prt_set(from_db, from_tab, self._p['PARTITION'])
										#pprint(pts)
										assert  len(pts)>0, 'Could not find partitions for table  %s [%s]' % (tab, self._p['PARTITION'])
									else:
										print 'getting spart'
										spts = self.get_sprt_set(from_db, from_tab, self._p['SUBPARTITION'])
										#pprint(spts)
										#print 'after spart'
										assert  len(spts)>0, 'Could not find sub-partitions for table  %s [%s]' % (tab, self._p['SUBPARTITION'])
									
									#sys.exit(1)
									if pts and len(pts)>0:
										for pt in pts:
											
											if pt:
												self._p['PARTITION']=pt
												self._pp['PARTITION']=pt
												status=0
												if self.p_if('IF_TRUNCATE'):
													t = None
													if self._pp.has_key('TO_PARTITION'):
														if self.is_set('TO_PARTITION'):

															t="ALTER TABLE %s tRUNCATE PARTITION (%s);" % (string.join(to_tab,'.'), self._pp['TO_PARTITION'])	
													else:
														t="ALTER TABLE %s tRUNCATE PARTITION (%s);" % (string.join(to_tab,'.'), pt)
													print t
													if t:	
														logger.info('#### START truncate of %s [%s].' % (tab,pt))
														(r, status) = self.do_query(to_db, t,0)
													
														logger.info('#### END truncate of %s [%s].' % (tab,pt))						
														if status!=0:
															logger.info('#### TRUNCATE of %s [%s] failed.' % (tab,pt))
													#else:
													#	logger.info('#### START copy of %s [%s].' % (tab,pt))							
													#	(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, pt)
													#	logger.info('#### END copy of %s [%s].' % (tab,pt))
												else:
													if self.p_if('IF_DELETE'):
														t="""DELETE /*+ PARALLEL(T) */ %s %s;
															COMMIT;
															""" % (string.join(to_tab,'.'), self.get_q_options(self._pp,{'_PARTITION':pt}))	
														print t	
														#print 
														#sys.exit(1)
														logger.info('#### START delete of %s [%s].' % (tab,pt))
														(r, status) = self.do_query(to_db, t,0)
														
														logger.info('#### END delete of %s [%s].' % (tab,pt))						
														if status!=0:
															logger.info('#### TRUNCATE of %s [%s] failed.' % (tab,pt))
														#else:
														#	logger.info('#### START copy of %s [%s].' % (tab,pt))							
														#	(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, pt)
														#	logger.info('#### END copy of %s [%s].' % (tab,pt))												
												if status==0:
													if 0:
														logger.info('#### START copy of %s [%s].' % (tab,pt))
														
														(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, {'PARTITION':pt})
														logger.info('#### END copy of %s [%s].' % (tab,pt))	
													print nosh
													if nosh:
														logger.info('#### START sharded copy of %s [%s].' % (tab,pt))	
														(r, status) = self.do_sharded_load(from_db, from_tab, to_db, to_tab, {'_PARTITION':pt})
														logger.info('#### DONE sharded copy of %s [%s].' % (tab,pt))
													else:
														print 'loading'
														logger.info('#### START unsharded copy of %s [%s].' % (tab,pt))	
														(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, {'_PARTITION':pt})
														logger.info('#### DONE unsharded copy of %s [%s].' % (tab,pt))
														#print r
														#print status
													
											#sys.exit(1)
									else:
										assert len(spts)>0, 'Could not fetch subpatitions.'
										for spt in spts:
											#pprint(spts)
											#sys.exit(1)
											if spt:
												self._p['SUBPARTITION']=spt
												self._pp['SUBPARTITION']=spt
												status=0
												if self.p_if('IF_TRUNCATE'):
													t = None
													if self._pp.has_key('TO_SUBPARTITION'):
														if self.is_set('TO_SUBPARTITION'):
															t="ALTER TABLE %s tRUNCATE SUBPARTITION %s;" % (string.join(to_tab,'.'), self._pp['TO_SUBPARTITION'])	
													else:
														t="ALTER TABLE %s tRUNCATE SUBPARTITION %s;" % (string.join(to_tab,'.'), spt)
													print t
													if t:	
														logger.info('#### START truncate of subpartition %s [%s].' % (tab,spt))
														(r, status) = self.do_query(to_db, t,0)
													
														logger.info('#### END truncate of  subpartition %s [%s].' % (tab,spt))						
														if status!=0:
															logger.info('#### TRUNCATE of subpartition %s [%s] failed.' % (tab,spt))
													#else:
													#	logger.info('#### START copy of %s [%s].' % (tab,pt))							
													#	(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, pt)
													#	logger.info('#### END copy of %s [%s].' % (tab,pt))
												else:
													if self.p_if('IF_DELETE'):
														t="""DELETE /*+ PARALLEL(T) */ %s %s;
															COMMIT;
															""" % (string.join(to_tab,'.'), self.get_q_options(self._pp,{'_SUBPARTITION':spt}))	
														print t	
														#print 
														#sys.exit(1)
														logger.info('#### START delete of subpartition %s [%s].' % (tab,spt))
														(r, status) = self.do_query(to_db, t,0)
														
														logger.info('#### END delete of subpartition %s [%s].' % (tab,spt))						
														if status!=0:
															logger.info('#### TRUNCATE of subpartition %s [%s] failed.' % (tab,spt))
														#else:
														#	logger.info('#### START copy of %s [%s].' % (tab,pt))							
														#	(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, pt)
														#	logger.info('#### END copy of %s [%s].' % (tab,pt))												
												if status==0:
													if 0:
														logger.info('#### START copy of %s [%s].' % (tab,spt))
														
														(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, {'SUBPARTITION':spt})
														logger.info('#### END copy of %s [%s].' % (tab,spt))	
													print nosh
													if nosh:
														logger.info('#### START sharded copy of %s [%s].' % (tab,spt))	
														(r, status) = self.do_sharded_load(from_db, from_tab, to_db, to_tab, {'_SUBPARTITION':spt})
														logger.info('#### DONE sharded copy of %s [%s].' % (tab,spt))
													else:
														print 'loading'
														logger.info('#### START unsharded copy of %s [%s].' % (tab,spt))	
														(r, status) = self.do_load(from_db, from_tab, to_db, to_tab, {'_SUBPARTITION':spt})
														logger.info('#### DONE unsharded copy of %s [%s].' % (tab,spt))
														#print r
														#print status
													
											#sys.exit(1)
								else:							
									status=0
									if self.p_if('IF_TRUNCATE'):
										t=tmpl_batch[tab]['TRUNCATE']

										if 1:
											logger.info('#### START truncate of %s.' % etl_object['name'])
											(r, status) = self.do_query(to_db, t,0)
											logger.info('#### END truncate of %s.' % etl_object['name'])						
											if status!=0:
												logger.info('#### TRUNCATE of %s failed.' % etl_object['name'])
									if status==0:
										if 1:
															
											
											print nosh
											if nosh:
												logger.info('#### START sharded copy of %s.' % tab)	
												(r, status) = self.do_sharded_load(from_db, from_tab, to_db, to_tab,{})
												logger.info('#### DONE sharded copy of %s.' % tab)
											else:
												print 'loading'
												logger.info('#### START unsharded copy of %s.' % tab)	
												(r, status) = self.do_load(from_db, from_tab, to_db, to_tab)
												logger.info('#### DONE unsharded copy of %s.' % tab)
											
										else: 
											logger.info('#### START copy of %s.' % tab)							
											t='CREATE TABLE tmp_%s as select * from %s WHERE 1=2;' % (logger.get_jobid(),tab)
											print t
											#sys.exit(1)
											(r, status) = self.do_query(to_db, t,0)
											tmp_to_tab = [to_tab[0], 'tmp_%s' % (logger.get_jobid())]
											print from_db, from_tab, to_db, to_tab, tmp_to_tab
											(r, status) = self.do_load(from_db, from_tab, to_db, tmp_to_tab)
											t='INSERT /*+APPEND*/ INTO %s SELECT * FROM tmp_%s;' % (string.join(to_tab,'.'),logger.get_jobid())
											print t
											#sys.exit(1)
											(r, status) = self.do_query(to_db, t,0)
											
											t='DROP TABLE tmp_%s;' % (logger.get_jobid())
											print t
											#sys.exit(1)
											(r, status) = self.do_query(to_db, t,0)
											#(r, status) = self.do_load(from_db, from_tab, to_db, to_tab)
											logger.info('#### END copy of %s.' % tab)

							if status==0:
								logger.info('Load of %s completed successfully.' % tab)
						else:
							logger.warning('#### Skipping load of %s.' % tab)
							logger.warning("Truncate of table %s failed." % tab)
					else:
						logger.warning('#### Skipping truncate of %s.' % tab)
				if self.p_if("IF_REBUILD_UNUSABLE_INDEXES") and not nosh: #logging indexes for rebuild
					self.rebuild_tab_indexes(to_db,(tab,to_tab),{})
					#pass
				#sys.exit(1)
			self.cleanup()
				
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return (r,status)
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
		assert pp.has_key('FROM_DB'),'FROM_DB is not defined'
		assert pp.has_key('TO_DB'),'TO_DB is not defined'
		
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
				to_tab= '.'.join(to_t)
				to_view= '.v_'.join(to_t)				
				from_tab='.'.join(from_t)

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
					#sys.exit(1)
					
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
	def get_to_tab(self,t):
		#pprint(self._pp)
		if 'TO_SCHEMA' in self._pp:
			tmp = self.p('TO_SCHEMA')
			assert tmp, 'TO_SCHEMA is not set'
			t[0]=tmp
		else:
			pass
		if 'TO_TABLE' in self._pp:
			tmp = self.p('TO_TABLE')
			assert tmp, 'TO_TABLE is not set'
			
			t[1]=tmp
		else:
			pass
		#print t
		return t		
	def get_from_tab(self,t):
		if 'FROM_SCHEMA' in self._pp:
			t[0]=self._pp['FROM_SCHEMA']
		else:
			if 'FROM_SCHEMA' in self._pipeline:
				t[0]=self._pipeline['FROM_SCHEMA']			
		return t		
	def do_load(self, from_db, from_t, to_db, to_t, options={} ):
		f = ""
		out=[]
		err=[]

		assert  len(from_db)>0, 'Source login is not set.'
		assert  len(to_db)>0, 'Target login is not set.'

		(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
		
		if not status:
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			if_dpl_parallel='TRUE'
			if self.p_if('IF_DPL_SERIAL'):
				if_dpl_parallel='FALSE'	
				
			dpl_mode='APPEND'
			if self.is_set('DPL_MODE'):
				if 'APPEND' in self._pp['DPL_MODE']:
					dpl_mode='APPEND'	
				else:
					if if_dpl_parallel=='TRUE':
						self._logger.fatal('Cannot use DPL mode %s with parallel enabled (use IF_DPL_SERIAL=1).' % self._pp['DPL_MODE'])
					else:
						if 'INSERT' in self._pp['DPL_MODE']:
							dpl_mode='INSERT'	
						else:
							if 'REPLACE' in self._pp['DPL_MODE']:
								dpl_mode='REPLACE'	
							else:
								if 'TRUNCATE' in self._pp['DPL_MODE']:
									dpl_mode='TRUNCATE'	
								else:
									self._logger.error('Unsupproted Direct Path Load mode %s.' % self._pp['DPL_MODE'])
									
			to_tab= '.'.join(self.get_to_tab(to_t))
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#print 'r_int:'
			#pprint(r_int)
			#sys.exit(1)
			r_col = map(lambda x: x.split(':')[0], r_int)
			#print 'r_col:'
			#pprint(r_col)
			#r_cl = r_col 
			r_cl = map(self.coldef, r_int)
			#print 'r_cl:'
			#pprint(r_cl)
			#sys.exit(1)
			#r_cl = [line.split()[2] for col in r_int:if ]
			cl =  "'%s'||%s||'%s'" % (ft,string.join(r_col,"||'%s'||\n" % ft),lt)
			#print 'cl:'
			#print cl
			#sys.exit(1)
			(nls_df,nls_tf) = self.get_date_format()
			ctl=self.get_ctl(string.join(self.get_to_tab(to_t),'.'),r_cl,dpl_mode,
							{'_NLS_DATE_FORMAT':nls_df,'_NLS_TIMESTAMP_FORMAT':nls_tf})
			#self._logger.log(ctl)
			#ptn = ''
			#print ctl
			#fname= 'sqlloader/%s.ctl' % to_tab
			if_direct='TRUE'
			#if self.is_set('PARTITION'):
			ptn=options.get('_PARTITION')
			if ptn:
				ptn= "_%s" % options['_PARTITION']
			else:
				ptn=''
			sptn=options.get('_SUBPARTITION')
			if sptn:
				sptn= "_%s" % options['_SUBPARTITION']
			else:
				sptn=''				
			#else:
			#ptn
			
			#pprint(ptn)
			#sys.exit(1)
			



			if self.p_if('IF_CONVENTIONAL'):
				if_direct='FALSE'	
				
			dpl_rows =40000
			if self.is_set('DPL_ROWS'):
				dpl_rows = int(self._pp['DPL_ROWS'])
				if if_dpl_parallel=='TRUE':
					self._logger.warn('DPL_ROWS is ignored in parallel mode.')
			dpl_bindsize = 1000000
			if self.is_set('DPL_BINDSIZE'):
				dpl_bindsize = int(self._pp['DPL_BINDSIZE'])
			#dpl_rows = 100000
			#if self.is_set('DPL_ROWS'):
			#	dpl_rows = int(self._pp['DPL_ROWS'])				
			dpl_readsize = 1000000
			if self.is_set('DPL_READSIZE'):
				dpl_readsize = int(self._pp['DPL_READSIZE'])
			dpl_streamsize = 100000
			if self.is_set('DPL_STREAMSIZE'):
				dpl_streamsize = int(self._pp['DPL_STREAMSIZE'])
			dpl_columnarrayrows = 10000
			if self.is_set('DPL_COLUMNARRAYROWS'):
				dpl_columnarrayrows = int(self._pp['DPL_COLUMNARRAYROWS'])				
			dpl_skip_index_maintenance = 'TRUE'
			if self.is_set('SKIP_INDEX_MAINTENANCE'):
				dpl_skip_index_maintenance = self._pp['SKIP_INDEX_MAINTENANCE']
			dpl_skip_unusable_indexes = 'TRUE'
			if self.is_set('SKIP_UNUSABLE_INDEXES'):
				dpl_skip_unusable_indexes = self._pp['SKIP_UNUSABLE_INDEXES']
			loader_errors = 10
			if self.is_set('LOADER_ERRORS'):
				loader_errors = int(self._pp['LOADER_ERRORS'])
			shard=''
			#pprint(options)
			if '_SHARD' in options:
				if not ptn and not sptn and options['_SHARD'][3]:
					shard="_%s_%s" % (options['_SHARD'][0],options['_SHARD'][3])
				else:
					shard="_%s" % options['_SHARD'][0]
			#print ptn, options['_SHARD'][3]	
			fname= 'sqlloader/%s%s%s.ctl' % (to_tab, "%s%s" % (ptn,sptn),shard)
			print fname
			#sys.exit(1)
			import codecs
			f = codecs.open(fname, 'w',"utf-8")
			status = f.write(unicode(ctl))
			
			if status!= None:
				self._logger.error('Cannot write to %s.' % fname)
			f.close()
			#fname= 'sqlloader/%s%s_2.ctl' % (to_tab, ptn)
			(r,status) = self.get_line_len(((from_db, from_t),(to_db, to_t)))
			maxlen=32767
			#pprint(r)
			#sys.exit(1)
			#if len(r)==0:
			#	self._logger.error("Cannot find line length.")
			llen=int(r[0]); # +20
			if llen>maxlen:
				llen=maxlen
			q= """set tab off head off line %s pages 0 echo off feedback off termout off  feed off newpage 0 arraysize 5000
			alter session set NLS_DATE_FORMAT='%s'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='%s'\n/\n
			SELECT %s FROM  %s  %s;\nexit;\n""" % \
			(llen, nls_df, nls_tf, cl , string.join(self.get_from_tab(from_t),'.'), self.get_q_options(self._pp,options))
			#/*WHERE  account_id='1427826'%/
			self._logger.sql(q)
			self.export_sql((q, to_tab))
			#pprint(q) 
			#pprint(options)
			#sys.exit(1)
			p1 = Popen(['echo', q], stdout=PIPE, stderr=PIPE)
			p2 = Popen([ 'sqlplus', '-S',from_db], stdin=p1.stdout, stdout=PIPE , stderr=PIPE
			)
			status =0
			out=[]
			err=[]
			#print to_db
			#sys.exit(1)
			slconf=['sqlldr', 'control=%s' % fname, # 'userid=%s' % to_db, 
			'ROWS1=%s' % dpl_rows,
				'COLUMNARRAYROWS=%s' % dpl_columnarrayrows,#'size=10000',
				'STREAMSIZE=%s' % dpl_streamsize,'READSIZE=%s' % dpl_readsize,
				'PARALLEL=%s' % if_dpl_parallel,
				'BINDSIZE=%s' % dpl_bindsize, #' UNRECOVERABLE=Y ', 
				'SKIP_INDEX_MAINTENANCE=%s' % dpl_skip_index_maintenance, 'SKIP_UNUSABLE_INDEXES=%s' % dpl_skip_unusable_indexes,
				'DIRECT=%s' % if_direct, #"data=\'-\'",
				'MULTITHREADING=TRUE',
				'LOG=sqlloader/%s%s%s.log' % (to_tab, "%s%s" % (ptn,sptn),shard), 'BAD=sqlloader/%s%s%s.bad' % (to_tab, "%s%s" % (ptn,sptn),shard),
				'DISCARD=sqlloader/%s%s%s.dsc' % (to_tab, "%s%s" % (ptn,sptn),shard),
				'ERRORS=%s' % loader_errors]
			self._logger.log(slconf)
			pprint(slconf)
			if 1:
				p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, #'ROWS=%s' % dpl_rows,
				'COLUMNARRAYROWS=%s' % dpl_columnarrayrows,#'size=10000',
				'STREAMSIZE=%s' % dpl_streamsize,'READSIZE=%s' % dpl_readsize,
				'PARALLEL=%s' % if_dpl_parallel,
				'BINDSIZE=%s' % dpl_bindsize, #' UNRECOVERABLE=Y ', 
				'SKIP_INDEX_MAINTENANCE=%s' % dpl_skip_index_maintenance, 'SKIP_UNUSABLE_INDEXES=%s' % dpl_skip_unusable_indexes,
				'DIRECT=%s' % if_direct, #"data=\'-\'",
				'MULTITHREADING=TRUE',
				'LOG=sqlloader/%s%s%s.log' % (to_tab, "%s%s" % (ptn,sptn),shard), 'BAD=sqlloader/%s%s%s.bad' % (to_tab, "%s%s" % (ptn,sptn),shard),
				'DISCARD=sqlloader/%s%s%s.dsc' % (to_tab, "%s%s" % (ptn,sptn),shard),				
				'ROWS=%s' % dpl_rows,	
				'ERRORS=%s' % loader_errors], 
				stdin=p2.stdout, stdout=PIPE, stderr=PIPE)
				output=' '
				#pprint(dir(p3.stderr))
				while output:
					output = p3.stdout.readline()
					out.append(output)
					#print 'stdout', output,'___'
					self._logger.info(output.rstrip())
				status=p3.wait()
				
				if status==0:
					self._logger.info('SQL*Loader status =%s' % status)
				if status!=0:
					self._logger.error('SQL*Loader status =%s' % status)
					if 0:
						output=' '
						while output:
							output = p3.stderr.readline()
							err.append(output)
							#print 'errout', output
							self._logger.warning(output.rstrip())
						status = p3.wait()
						#pprint(err)
						#sys.exit(1)

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

	def copy_query_data(self, etl_object, logger):
		""" Spool query using SQL*Plus and SQL*Loader"""
		self.set_params(etl_object, logger)
		#(tmpl_batch, status) = self.get_tmpl_batch_fixed(etl_object, logger)
		template = self.get_template(etl_object, logger).strip().strip(';')
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
			from_db = self._pp['FROM_DB'].strip(' ').replace(' ','')
			to_db= self._pp['TO_DB'].strip(' ').replace(' ','')		
			#print from_db, to_db
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
						to_tab= self.get_to_tab(tab.split('.'))
						from_tab=self.get_from_tab(tab.split('.'))
						#print from_tab, to_tab
						
						if 1:
							
							#(r, status) = self.do_query(to_db, tmpl_batch[tab]['TRUNCATE'],0)
							status=0
							if self.p_if('IF_CREATE_TARGET_TABLE'):
								ctast = '.'.join(to_tab)
								logger.info('#### START CTAS of %s.' % ctast)							
								t='CREATE TABLE %s as select * from (%s) WHERE 1=2;' % (ctast, template)
								#print t
								#sys.exit(1)
								(r, status) = self.do_query(to_db, t,0)
								
								#print r, status
								
								assert status==0, 'CTAS for table %s failed.' % ctast
								#sys.exit(1)

								logger.info('#### END CTAS of %s.' % ctast)
							
							if self.p_if('IF_TRUNCATE'):
								trunt = '.'.join(to_tab)
								t='TRUNCATE TABLE %s;' % trunt
								#print t
								#sys.exit(1)
								if 1:
									logger.info('#### START truncate of %s.' % trunt)
									(r, status) = self.do_query(to_db, t,0)
									logger.info('#### END truncate of %s.' % trunt	)
									#sys.exit(1)									
									if status!=0:
										logger.info('#### TRUNCATE of %s failed.' % etl_object['name'])
							if status==0:
								if 1:
									#print 'loading'
									logger.info('#### START query copy of %s[%s] no partiton ' % (workn,tab))												
									#(r, status) = self.do_query_spool(from_db, template)
									(r, status) = self.do_query_load(from_db, from_tab, to_db, to_tab, template)
									logger.info('#### END query copy of %s[%s] no partition.' % (workn,tab))

		

								if status==0:
									logger.info('Query copy of %s[%s] completed successfully.' % (workn,tab))
								#self.save_metadata(etl_object, logger)

							else:
								logger.warning('#### Skipping copy of %s[%s].' % (workn,tab))
								#logger.warning("Truncate of table %s failed." % tab)
						else:
							logger.warning('#### Skipping copy of %s[%s].' % (workn,tab))
							
					self.cleanup()
				self._gwc['LATEST']={'COLUMNS':self._pp['_COLUMNS'],
									 'FLAGS':self._FLAGS, 
									 'TABLE':self._pp['_TABLE'],
									 'OUTPUT_FILE':self._pp['_OUTPUT_FILE']}
				#pprint(self._gwc['LATEST'])
		if self._pp.has_key('EMAIL_TO') and 0:
			self.mail(self._pp['EMAIL_TO'],tab )
		
		return 0	

	def do_query_load(self, from_db, from_t, to_db, to_t, qstr, options={} ):
		f = ""
		out=[]
		err=[]

		assert  len(from_db)>0, 'Source login is not set.'
		assert  len(to_db)>0, 'Target login is not set.'
		
		#pprint(r_from)
		#sys.exit(1)
		#from_t= list((self._pp.get('FROM_SCHEMA'), self.get_temp_table_name()))
		self.set_query_cols( from_db, from_t,to_db, to_t, qstr)
		(r_int, status)=self.get_common_query_cols(from_db, from_t, to_db, to_t)
		#print r_int
		#sys.exit(1)
		if not status:
			ft = self.p('FIELD_TERMINATOR') 
			lt = self.p('LINE_TERMINATOR') 
			if_dpl_parallel='TRUE'
			if self.p_if('IF_DPL_SERIAL'):
				if_dpl_parallel='FALSE'	
				
			dpl_mode='APPEND'
			if self.is_set('DPL_MODE'):
				if 'APPEND' in self._pp['DPL_MODE']:
					dpl_mode='APPEND'	
				else:
					if if_dpl_parallel=='TRUE':
						self._logger.fatal('Cannot use DPL mode %s with parallel enabled (use IF_DPL_SERIAL=1).' % self._pp['DPL_MODE'])
					else:
						if 'INSERT' in self._pp['DPL_MODE']:
							dpl_mode='INSERT'	
						else:
							if 'REPLACE' in self._pp['DPL_MODE']:
								dpl_mode='REPLACE'	
							else:
								if 'TRUNCATE' in self._pp['DPL_MODE']:
									dpl_mode='TRUNCATE'	
								else:
									self._logger.error('Unsupproted Direct Path Load mode %s.' % self._pp['DPL_MODE'])
									
			to_tab= '.'.join(self.get_to_tab(to_t))
			#cl = "'\"'||%s||'\"'" % string.join(r_int,"||'\",\"'||")
			#print "'%s'||||'~'" % ft,"||'%'||" % ft
			#print 'r_int:'
			#pprint(r_int)
			#sys.exit(1)
			r_col = map(lambda x: x.split(':')[0], r_int)
			#print 'r_col:'
			#pprint(r_col)
			#r_cl = r_col 
			r_cl = map(self.coldef, r_int)
			#print 'r_cl:'
			#pprint(r_cl)
			#sys.exit(1)
			#r_cl = [line.split()[2] for col in r_int:if ]
			cl =  "'%s'||%s||'%s'" % (ft,string.join(r_col,"||'%s'||\n" % ft),lt)
			#print 'cl:'
			#print cl
			#sys.exit(1)
			(nls_df,nls_tf) = self.get_date_format()
			ctl=self.get_ctl(string.join(self.get_to_tab(to_t),'.'),r_cl,dpl_mode,
							{'_NLS_DATE_FORMAT':nls_df,'_NLS_TIMESTAMP_FORMAT':nls_tf})
			#self._logger.log(ctl)
			#ptn = ''
			#print ctl
			#fname= 'sqlloader/%s.ctl' % to_tab
			if_direct='TRUE'
			#if self.is_set('PARTITION'):
			ptn=options.get('_PARTITION')
			if ptn:
				ptn= "_%s" % options['_PARTITION']
			else:
				ptn=''
			#else:
			#ptn
			
			#pprint(ptn)
			#sys.exit(1)
			



			if self.p_if('IF_CONVENTIONAL'):
				if_direct='FALSE'	
				
			dpl_rows =40000
			if self.is_set('DPL_ROWS'):
				dpl_rows = int(self._pp['DPL_ROWS'])
				if if_dpl_parallel=='TRUE':
					self._logger.warn('DPL_ROWS is ignored in parallel mode.')
			dpl_bindsize = 1000000
			if self.is_set('DPL_BINDSIZE'):
				dpl_bindsize = int(self._pp['DPL_BINDSIZE'])
			dpl_readsize = 1000000
			if self.is_set('DPL_READSIZE'):
				dpl_readsize = int(self._pp['DPL_READSIZE'])
			dpl_streamsize = 1000000
			if self.is_set('DPL_STREAMSIZE'):
				dpl_streamsize = int(self._pp['DPL_STREAMSIZE'])
			dpl_columnarrayrows = 100000
			if self.is_set('DPL_COLUMNARRAYROWS'):
				dpl_columnarrayrows = int(self._pp['DPL_COLUMNARRAYROWS'])				
			dpl_skip_index_maintenance = 'TRUE'
			if self.is_set('SKIP_INDEX_MAINTENANCE'):
				dpl_skip_index_maintenance = self._pp['SKIP_INDEX_MAINTENANCE']
			dpl_skip_unusable_indexes = 'TRUE'
			if self.is_set('SKIP_UNUSABLE_INDEXES'):
				dpl_skip_unusable_indexes = self._pp['SKIP_UNUSABLE_INDEXES']
			loader_errors = 10
			if self.is_set('LOADER_ERRORS'):
				loader_errors = int(self._pp['LOADER_ERRORS'])
			shard=''
			#pprint(options)
			if '_SHARD' in options:
				if not ptn and options['_SHARD'][3]:
					shard="_%s_%s" % (options['_SHARD'][0],options['_SHARD'][3])
				else:
					shard="_%s" % options['_SHARD'][0]
			#print ptn, options['_SHARD'][3]	
			fname= 'sqlloader/%s%s%s.ctl' % (to_tab, ptn,shard)
			#print fname
			#sys.exit(1)
			import codecs
			f = codecs.open(fname, 'w',"utf-8")
			status = f.write(unicode(ctl))
			
			if status!= None:
				self._logger.error('Cannot write to %s.' % fname)
			f.close()
			#fname= 'sqlloader/%s%s_2.ctl' % (to_tab, ptn)
			(r,status) = self.get_line_len(((from_db, from_t),(to_db, to_t)))
			maxlen=32767
			#pprint(r)
			#sys.exit(1)
			#if len(r)==0:
			#	self._logger.error("Cannot find line length.")
			llen=maxlen #int(r[0]); # +20
			if llen>maxlen:
				llen=maxlen
			q= """set tab off head off line %s pages 0 echo off feedback off termout off  feed off newpage 0 arraysize 5000
			alter session set NLS_DATE_FORMAT='%s'\n/\n\nalter session set NLS_TIMESTAMP_FORMAT='%s'\n/\n
			SELECT %s FROM  (%s ) %s;\nexit;\n""" % \
			(llen, nls_df, nls_tf, cl , qstr, self.get_q_options(self._pp,options))
			#/*WHERE  account_id='1427826'%/
			#self._logger.sql(q)
			self.export_sql((q, to_tab))
			#print(q) 
			#pprint(options)
			#sys.exit(1)
			p1 = Popen(['echo', q], stdout=PIPE, stderr=PIPE)
			p2 = Popen([ 'sqlplus', '-S',from_db], stdin=p1.stdout, stdout=PIPE , stderr=PIPE
			)
			status =0
			out=[]
			err=[]
			#print to_db
			#sys.exit(1)
			slconf=['sqlldr', 'control=%s' % fname, # 'userid=%s' % to_db, 
			'ROWS2=%s' % dpl_rows,
				'COLUMNARRAYROWS=%s' % dpl_columnarrayrows,#'size=10000',
				'STREAMSIZE=%s' % dpl_streamsize,'READSIZE=%s' % dpl_readsize,
				'PARALLEL=%s' % if_dpl_parallel,
				'BINDSIZE=%s' % dpl_bindsize, #' UNRECOVERABLE=Y ', 
				'SKIP_INDEX_MAINTENANCE=%s' % dpl_skip_index_maintenance, 'SKIP_UNUSABLE_INDEXES=%s' % dpl_skip_unusable_indexes,
				'DIRECT=%s' % if_direct, #"data=\'-\'",
				'MULTITHREADING=TRUE',
				'LOG=sqlloader/%s%s%s.log' % (to_tab, ptn,shard), 'BAD=sqlloader/%s%s%s.bad' % (to_tab, ptn,shard),
				'DISCARD=sqlloader/%s%s%s.dsc' % (to_tab, ptn,shard),
				'ERRORS=%s' % loader_errors]
			self._logger.log(slconf)
			pprint(slconf)
			if 1:
				p3 = Popen(['sqlldr', 'control=%s' % fname, 'userid=%s' % to_db, #'ROWS=%s' % dpl_rows,
				'COLUMNARRAYROWS=%s' % dpl_columnarrayrows,#'size=10000',
				'STREAMSIZE=%s' % dpl_streamsize,'READSIZE=%s' % dpl_readsize,
				'PARALLEL=%s' % if_dpl_parallel,
				'BINDSIZE=%s' % dpl_bindsize, #' UNRECOVERABLE=Y ', 
				'SKIP_INDEX_MAINTENANCE=%s' % dpl_skip_index_maintenance, 'SKIP_UNUSABLE_INDEXES=%s' % dpl_skip_unusable_indexes,
				'DIRECT=%s' % if_direct, #"data=\'-\'",
				'MULTITHREADING=FALSE',
				'LOG=sqlloader/%s%s%s.log' % (to_tab, ptn,shard), 'BAD=sqlloader/%s%s%s.bad' % (to_tab, ptn,shard),
				'DISCARD=sqlloader/%s%s%s.dsc' % (to_tab, ptn,shard),
				'ROWS=%s' % dpl_rows,
				'ERRORS=%s' % loader_errors
				], 
				stdin=p2.stdout, stdout=PIPE, stderr=PIPE)
				output=' '
				#pprint(dir(p3.stderr))
				while output:
					output = p3.stdout.readline()
					out.append(output)
					#print '>>>', output,' <<<'
					self._logger.info(output.rstrip())
				status=p3.wait()
				
				if status==0:
					self._logger.info('SQL*Loader status =%s' % status)
				if status!=0:
					self._logger.error('SQL*Loader status =%s' % status)
					if 0:
						output=' '
						while output:
							output = p3.stderr.readline()
							err.append(output)
							#print 'errout', output
							self._logger.warning(output.rstrip())
						status = p3.wait()
						#pprint(err)
						#sys.exit(1)

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
	def set_query_cols(self, from_db, from_t,to_db, to_t, qstr):
		from_key = self.get_cc_key((from_db, from_t))
		to_key = self.get_cc_key( (to_db, to_t))
		self._cci[from_key]={}
		self._cci[from_key][to_key]={}
		#(r_from,s_from) = self.get_columns(from_db, from_t)	
		(r_from,s_from) = self.get_query_columns(from_db, qstr)	
		#pprint(r_from)
		#sys.exit(1)
	def get_common_query_cols(self, from_db, from_t, to_db, to_t):
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
			r_from_col = map(lambda x: x.split(':')[0], r_from)
			#pprint(r_from_col)
			in_filter =  "AND COLUMN_NAME IN ('%s')" % (string.join(r_from_col,"',\n'")) 
			#print in_filter			
			#print 'getting columns for:',to_db, to_t
			(r_to,s_to) = self.get_columns(to_db, to_t,in_filter)	
			#print s_from, s_to
			#sys.exit(1)
			if not s_from and not s_to:
				#pprint(r_from)
				#pprint(r_to)
				#sys.exit(1)

				#sys.exit(1)
				r_int = r_to #list(set(r_from) & set(r_to))
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

	def do_sharded_load(self, from_db, from_t, to_db, to_t, options):
		#from threading import Thread
		r=None
		
		status=1		
		assert self.is_set('SKIP_INDEX_MAINTENANCE') == 'TRUE', 'Cannot shard without SKIP_INDEX_MAINTENANCE = TRUE'
		assert self.is_set('IF_DPL_SERIAL') == '0', 'Cannot shard without IF_DPL_SERIAL = 0'
		#(r, status) =self.do_load(from_db, from_t, to_db, to_t, ptin)
		nosh = self.is_set('NUM_OF_SHARDS')
		assert nosh, 'NUM_OF_SHARDS is undefined.'
		nosh=int(nosh)
		maxt=20
		sharded_part={}
		if nosh:
			pprint(to_t)
			self._logger.info('Sharding table %s.%s' % tuple(from_t) )
			if 1: #optimize
				(r_int, status)=self.get_common_cols(from_db, from_t, to_db, to_t)
			(shards, status)=self.get_tab_shards(nosh, from_db, from_t,options)
			#pprint(shards)
			#print status
			#sys.exit(1)
			assert status==0,'Cannot fetch shards.'
			start = time.time()
			#queue = Queue.Queue()
			# Create a pool with three worker threads
			prev_count=activeCount()
			pool_size = len(shards)
			assert pool_size<=maxt, 'Too many shards.'
			if pool_size>maxt:
				pool_size=maxt
			if pool_size<1:
				pool_size=3
			pool = ThreadPool(pool_size)

			# Insert tasks into the queue and let them run
			i =0
			self.pool_cntr=[]
			
			for ln in shards:
				shard = ln[0].split('||')
				#print shard
				#time.sleep(1)
				#options['_SHARD']=shard
				#pprint(options)
				#sys.exit(1)
				shpart=shard[3]
				if shpart:
					sharded_part[shpart]=1
				pool.queueTask(self.do_load, (from_db, from_t, to_db, to_t,{'_PARTITION':options.get('_PARTITION'),'_SUBPARTITION':options.get('_SUBPARTITION'),'_SHARD':shard}), self.taskCallback)
				#del options['_SHARD']
				if i==0  and 0:
					break
				i +=1
			# When all tasks are finished, allow the threads to terminate
			pool.joinAll()
			
			#print 'pool.__threads',pool.__threads
			#print 'threads left ==============', len(self.pool_cntr)
			#time.sleep(1)
			#import threading
			while activeCount()>1: #pool.getThreadCount()>0:
				print '%s: Waiting for tpool %s' % (self._logger.getElapsedSec() , activeCount() - prev_count)
				#print activeCount()
				if len(shards)==len(self.pool_cntr):
					break
				time.sleep(1)
			
			#print 'threads left ==============', len(self.pool_cntr)
			print "Elapsed Time: %s" % (time.time() - start)
			start = time.time()
			if self.p_if("IF_REBUILD_UNUSABLE_INDEXES") and len(shards)>0: #logging indexes for rebuild
				part=options.get('_PARTITION')
				if part:
					print 'Index partition', part
					self.rebuild_tab_indexes(to_db,('.'.join(to_t),to_t),{'_PARTITION':part})
				else:
					pprint(sharded_part)
					#sys.exit(1)
					if sharded_part:
						for part in sharded_part.keys():
							print 'Sharded index partition', part
							self.rebuild_tab_indexes(to_db,('.'.join(to_t),to_t),{'_PARTITION':part})
					else:
						self.rebuild_tab_indexes(to_db,('.'.join(to_t),to_t),{})
				print "Elapsed Time: %s" % (time.time() - start)
			

		else:
			self._logger.warn('Passing sharded load. NUM_OF_SHARDS = %s' % nosh)
		#sys.exit(1)
		return (r, status) 
	def taskCallback(self,data):
		self.pool_cntr.append(data)
		print "Callback called for", data		


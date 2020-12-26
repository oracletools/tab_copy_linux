#!/usr/bin/python2.4
#
# Copyright 2012 .  All Rights Reserved.
# 
# Original author alex_buz@gmail.com  (Alex Buzunov)

"""This module contains all metadata collection routines
"""

__author__ = 'alex_buz@gmail.com (Alex Buzunov)'

import sys, os, re
from pprint import pprint
from lib.common_utils import sql_utils

STACKTRACE_MAX_DEPTH = 2



class meta_utils(sql_utils):
	"""A class for table metadata."""

	def __init__(self, pipelinemeta, extract_logger, environment):
		"""Initializes metadata collector.  See also Extracter.__init__.

		Args:
		  extract_logger: An object supporting the methods info(message),
			warning(message), and error(message) where message is a string.
			The intent of course is that we wish to log messages using the
			provided logger.
		"""
		app_utils.__init__(self, pipelinemeta, extract_logger, environment)

			
	def get_columns(self, login, t, in_filter=''):
		col_key = self.get_cc_key((login, t))
		#print 'col_key = ',col_key
		if not self._ci.has_key(col_key):
			self._ci[col_key]={}
		#pprint(self._ci)
		if len(self._ci[col_key])==0:
			#AND data_type IN ('VARCHAR2','CHAR','DATE','LONG','NUMBER')
			#q="select  'COLUMN.'||column_name from all_tab_columns t where table_name =UPPER('%s') and owner='%s'  order by column_id;" % (t[1],t[0])
			q="select  'COLUMN.'||column_name||':'||data_length||':'||data_type from all_tab_columns t where table_name =UPPER('%s') and owner='%s' %s order by column_id;" % (t[1],t[0],in_filter)
			regexp=re.compile(r'.*\.([\w\_\:\(\)\d]+)\n')
			#print(q)
			#sys.exit(1)
			r=None
			status=0
			if in_filter: # save sql to a file
				sqfn=self.export_sql(("set echo off pagesize 0 serveroutput off feedback off termout on\n%s\nexit;" % q, '.'.join(t)))
				#print sqfn 
				#sys.exit(1)				
				(r,status) = self.do_query(login, None,sqfn,regexp,1)
				#print(r)
				#print(status)
				#print(login)
				#sys.exit(1)
			else:
				#print q
				(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off\n%s" % q,0,regexp,1)

			if not status:
				if len(r)==0:
					status=2
					self._logger.fatal('Table %s doesn\'t exist0 in %s.' % ('.'.join(t), re.sub('\/(.*)\@', '/***@', login)))
			r.sort()
			self._ci[col_key]=r	
			#pprint(r)
			#sys.exit(1)
			return (r,status)
		else:
			return (self._ci[col_key],0)
	def get_temp_table_name(self):
		return 'TCL_%s' % self.get_temp_token()
	def get_temp_token(self):
		return self._logger.temp_file_name.strip('/tmp')		
	def get_query_columns(self, login, qry):
		assert self._pp.get('FROM_SCHEMA'), 'FROM_SCHEMA is not set'
		t= list((self._pp.get('FROM_SCHEMA'), self.get_temp_table_name()))
		col_key = self.get_cc_key((login, t))
		#print 'col_key = ',col_key
		if not self._ci.has_key(col_key):
			self._ci[col_key]={}
		#pprint(self._ci)
		if len(self._ci[col_key])==0:
			"""['ASET_LVL_0_DESC:120:VARCHAR2',
 'ASET_LVL_1_DESC:120:VARCHAR2',
 'ASET_LVL_2_DESC:120:VARCHAR2',
 'ASET_LVL_KEY:180:VARCHAR2',
 'BLTR_CD:10:VARCHAR2',
			"""
			#print len(qry[70000:100000])
			#sys.exit(1)
			q="""DECLARE
  c           NUMBER;
  d           NUMBER;
  col_cnt     INTEGER;
  f           BOOLEAN;
  rec_tab     DBMS_SQL.DESC_TAB;
  col_num    NUMBER;
  v_sql dbms_sql.varchar2a;
 v_sql_1 varchar2(32767);
 v_sql_2 varchar2(32767);
 v_sql_3 varchar2(32767);
 v_sql_4 varchar2(32767);
  v_type VARCHAR2(32):='';
  PROCEDURE print_rec(rec in DBMS_SQL.DESC_REC) IS
  BEGIN
	v_type:=CASE rec.col_type
				WHEN 1 THEN 'VARCHAR2'
				WHEN 12 THEN 'DATE'
				WHEN 2 THEN 'NUMBER'
			ELSE ''||rec.col_type
			END;
    DBMS_OUTPUT.PUT_LINE(rec.col_name||':'||rec.col_name_len||':'||v_type);
  END;
BEGIN
  v_sql(1):='%s';
  v_sql(2):='%s';
  v_sql(3):='%s';
  v_sql(4):='%s';
  v_sql(5):='%s';
  c := DBMS_SQL.OPEN_CURSOR;
  DBMS_SQL.PARSE(c, v_sql,1,5,False, DBMS_SQL.NATIVE);
  d := DBMS_SQL.EXECUTE(c);
  DBMS_SQL.DESCRIBE_COLUMNS(c, col_cnt, rec_tab);
/*
 * Following loop could simply be for j in 1..col_cnt loop.
 * Here we are simply illustrating some of the PL/SQL table
 * features.
 */
  col_num := rec_tab.first;
  IF (col_num IS NOT NULL) THEN
    LOOP
      print_rec(rec_tab(col_num));
      col_num := rec_tab.next(col_num);
      EXIT WHEN (col_num IS NULL);
    END LOOP;
  END IF;
  DBMS_SQL.CLOSE_CURSOR(c);
END;
/

""" % (qry[0:32000].replace("'","''"),qry[32000:64000].replace("'","''"),qry[64000:96000].replace("'","''"),qry[96000:128000].replace("'","''"),qry[128000:160000].replace("'","''"))
			regexp=re.compile(r'([\w\_\:\(\)\d]+)')
			#regexp=re.compile(r'(.*)')
			#print(q);
			#sys.exit(1)
			(r,status) = self.do_query(login, 
			#"set echo off pagesize 0 serveroutput off feedback off termout off\n%s" 
			'set serveroutput on echo on termout on feedback off\n%s'% q,0,regexp,1)
			#pprint(r)
			
			#print t, col_key 
			#sys.exit(1)
			if not status:
				if len(r)==0:
					status=2
					self._logger.fatal('Table %s doesn\'t exist1 in %s.' % ('.'.join(t), re.sub('\/(.*)\@', '/***@', login)))
			#r.sort()
			self._ci[col_key]=r	
			#pprint(r)
			#sys.exit(1)
			return (r,status)
		else:
			return (self._ci[col_key],0)				
	def get_select_from_cols(self, l_cols, t_tab):
		out="SELECT %s FROM %s " % (', '.join(l_cols), '.'.join(t_tab))
		return out	
	def coldef (self,x): 
		#pprint(x)
		#sys.exit(1)
		
		(colname, colsize, coltype)= x.split(':')
		#print sp
		if colsize:
			if int(colsize)>265: # or colname in ('FIRM_NOS_NAM_PAY_SIDE', 'FIRM_NOS_NAM_RECV_SIDE'):
				row = x.split(':')
				return '%s CHAR(%s) NULLIF %s=BLANKS ' % (colname,row[1],colname)
			#if colname in ('FIRM_NOS_NAM_PAY_SIDE', 'FIRM_NOS_NAM_RECV_SIDE'):
			#	return '%s PRESERVE BLANKS' % colname
			if 'DATE' ==  coltype:
				#return '%s DATE' % (sp[0])
				(nls_df,blah) = self.get_date_format()
				if nls_df != self._default_df:
					return '%s "TO_DATE(:%s, \'%s\')" ' % (colname,colname,nls_df)
			#if 'TRD_ENTR_TS' in sp:
			#	#return '%s DATE' % (sp[0])
			#	#return '%s "TO_DATE(:%s, \'DD-MON-RR HH.MI.SS AM\')" ' % (sp[0],sp[0])
		
		
		return colname 
	def get_date_format (self):
		nls_df = self._pp.get('NLS_DATE_FORMAT')
		if not nls_df:
			nls_df = self._default_df
		nls_tf = self._pp.get('NLS_TIMESTAMP_FORMAT')
		if not nls_tf:
			nls_tf = 'DD-MON-RR HH.MI.SSXFF AM'	
		return (nls_df,nls_tf)	
	def get_ctl(self, to_tab, r_int, dpl_mode, options):
		part = ''
		if self.is_set('PARTITION'):
			if self._pp.has_key('TO_PARTITION'):
				to_part = self._pp.get('TO_PARTITION')
				if to_part:
					part = 'PARTITIOn (%s)' % to_part
				else:
					pass
			else:
				part = 'PARTITION (%s)' % self.p('PARTITION')
		unrec = ''
		if self.p_if('IF_UNRECOVERABLE'):
			unrec = 'UNRECOVERABLE'			
		tmpl="""%s
LOAD DATA
	INFILE '-' "str '%s\n'"
	%s
	INTO TABLE %s %s
	FIELDS TERMINATED BY '%s'
	TRAILING NULLCOLS
	(C_FILLER FILLER,
	 %s)""" % (unrec,self.p('LINE_TERMINATOR').strip("'"),dpl_mode,to_tab, part, self.p('FIELD_TERMINATOR').strip("'"), ','.join(r_int))
		#pprint(tmpl)
		#pprint(r_int)
		#sys.exit(1)
		return tmpl	
		
	def get_line_len(self, tab_tt):
		(login, t) = tab_tt[0]
		tab_key=(self.get_cc_key(tab_tt[0]),self.get_cc_key(tab_tt[1]))
		#column index
		#ci = " AND COLUMN_NAME IN ('%s') " % string.join(self._cci[tab_key[0]][tab_key[1]],"',\n'")
		ci = " AND COLUMN_NAME IN ('%s') " % "',\n'".join(map(lambda x: x.split(':')[0],self._cci[tab_key[0]][tab_key[1]]))
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
								 'DATE', 28,
								 'TIMESTAMP(6) WITH LOCAL TIME ZONE', 30,
                                 data_length
                                ) data_length,
                         table_name, owner
                    FROM all_tab_columns)
           WHERE table_name =UPPER('%s') and owner='%s' %s order by column_name);
""" % (t[1],t[0], ci)
		self._logger.sql(q)	
		#print q, login
		
		#q="select COLUMN_NAME ||' POSITION('||(len-data_length+1)||':'||len||') '||DECODE(data_type,'VARCHAR2','CHAR', 'INTEGER','CHAR','NUMBER','INTEGER EXTERNAL','TIMESTAMP(6)','TIMESTAMP(6)', data_type) q FROM (select COLUMN_NAME, data_type,sum(data_length) OVER (PARTITION BY table_name ORDER BY column_name   ROWS UNBOUNDED PRECEDING) len, data_length from ( select column_name, data_type,DECODE(data_type,'NUMBER',11,'TIMESTAMP(6)',28, data_length) data_length, table_name, owner from dba_tab_columns) where table_name ='%s' and owner='%s' %s order by column_name);" % (t[1],t[0], ci)
		#self._logger.info(q)
		#regexp=re.compile(r'[\ ]*([\w\d\_]+\ POSITION\(\d+\:\d+\) [\w\d\(\)]+)')
		regexp=re.compile(r'.*line_length=([\w]+)')
		
		(r,status) = self.do_query(login, "set echo off pagesize 0 serveroutput off feedback off termout off HEADING OFF SHOW OFF PAGESIZE 0 VERIFY OFF DOCUMENT OFF NEWP NONE feed off\n%s" % q,0,regexp,1)
		#pprint(r)
		#sys.exit(1)
		if status!=0:
			if len(r)==0:
				status=2
				self._logger.fatal('Table %s doesn\'t exist2 in %s.' % ('.'.join(t), re.sub('\/(.*),\@', '/***@', login)))
		return (r,status)
	def get_q_options(self,pp,options={}):
		lame_duck=''
		if pp.has_key('LAME_DUCK') and int(pp['LAME_DUCK'])>0:
			lame_duck = "WHERE ROWNUM <= %s " % pp['LAME_DUCK']
			if self.is_set('FILTER'):
				lame_duck ='%s AND %s' % (lame_duck, self.p('FILTER')) 
		else:
			if self.is_set('FILTER'):
				lame_duck ='%s WHERE %s' % (lame_duck, self.p('FILTER')) 
		
		part=options.get('_PARTITION')
		#print part
		if part:
			part = " PARTITION (%s) T " % options['_PARTITION']
		else:
			if pp.has_key('SUBPARTITION'):
				part = " SUBPARTITION (%s) " % pp['SUBPARTITION']
		shard = ''
		if '_SHARD' in options:
			#pprint(pp['_SHARD'])
			#sys.exit(1)
			shard = "/* shard %s*/ ROWID BETWEEN '%s' AND '%s' " % (options['_SHARD'][0],options['_SHARD'][1],options['_SHARD'][2]) 
			if lame_duck:
				shard = "AND %s" % shard
			else:
				shard = "WHERE %s" % shard

		return " %s %s %s" % (part, lame_duck, shard)	
	def get_prt_set(self, to_db, to_tab, pt_mask):
		#print to_db, to_tab, pt_mask
		regexp=re.compile(r'\s?(%s)' % pt_mask)
		pq="""
		%s""" % ("SELECT PARTITION_NAME FROM ALL_TAB_PARTITIONS WHERE TABLE_OWNER='%s' AND TABLE_NAME = '%s' and REGEXP_LIKE(PARTITION_NAME, '%s');\n" % (to_tab[0],to_tab[1],pt_mask ))
		#%s""" % (200,"SELECT PARTITION_NAME FROM ALL_TAB_PARTITIONS WHERE TABLE_OWNER='%s' AND TABLE_NAME = '%s' ;\n" % (tuple(to_tab)))
		pprint(pq)
		(out, status) = self.do_query(to_db, pq,0,regexp)
		#pprint(out)
		#sys.exit(1)
		#print len(out)
		return  map(lambda x: x[0], out)	
	def get_sprt_set(self, to_db, to_tab, spt_mask):
		#print to_db, to_tab, pt_mask
		regexp=re.compile(r'\s?(.*)' )
		pq="""set heading off line %s echo off feedback off termout off feed off newpage 0 pagesize 99 serveroutput off show off
		%s""" % (200,"SELECT SUBPARTITION_NAME FROM ALL_TAB_SUBPARTITIONS WHERE TABLE_OWNER='%s' AND TABLE_NAME = '%s' and REGEXP_LIKE(SUBPARTITION_NAME, '%s');\n" % (to_tab[0],to_tab[1],spt_mask ))
		#pprint(pq)
		(out, status) = self.do_query(to_db, pq,0,regexp)
		#print 'after doq'
		#sys.exit(1)
		#print len(out)
		return  map(lambda x: x[0], out)			
	def get_tab_shards(self,nosh,from_db,from_t,options): 
		p= options.get('_PARTITION')
		sp= options.get('_SUBPARTITION')
		#pprint(p)
		#sys.exit(1)
		q =''
		if p:
		#	prtn = "AND SUBOBJECT_NAME = '%s'" % p
		#sys.exit(1)
			q="""
			select /*+parallel(R, 16) */ distinct nt||'||'||min(id)||'||'||max(id)||'||'||'%s'  
		  from ( 
		select rowid id, ntile(%s) over (order by rowid) nt 
		  from %s.%s partition(%s)  R 
			   ) 
		 group by nt;
			""" % (p,nosh,from_t[0],from_t[1],p)
		else:
			if sp:
		#	prtn = "AND SUBOBJECT_NAME = '%s'" % p
		#sys.exit(1)
				q="""
				select /*+parallel(R, 16) */ distinct nt||'||'||min(id)||'||'||max(id)||'||'||'%s'  
			  from ( 
			select rowid id, ntile(%s) over (order by rowid) nt 
			  from %s.%s subpartition(%s)  R 
				   ) 
			 group by nt;
				""" % (p,nosh,from_t[0],from_t[1],sp)
			else:
				q="""
				select /*+parallel(R,16) */ distinct nt||'||'||min(id)||'||'||max(id)||'||'||'%s'  
			  from ( 
			select rowid id, ntile(%s) over (order by rowid) nt 
			  from %s.%s R 
				   ) 
			 group by nt;
				""" % (p,nosh,from_t[0],from_t[1])			
		#print q
		#sys.exit(1)
		regexp=re.compile(r'(.*)')
		#self._pp['FROM_DB'] =self._pp['TO_DB']
		assert from_db, 'TO_DB is not set.'
		(r, status) = self.do_query(from_db, "set heading off  pagesize 0 serveroutput off feedback off echo off\n%s"  % q,0,regexp)
		#print from_db
		#pprint(r)
		#t= 
		#sys.exit(1)
		return (r, status)	

	def get_tab_shards_dbms(self,nosh,from_db,from_t,options):
		p= options.get('_PARTITION')
		#pprint(p)
		#sys.exit(1)
		prtn =''
		if p:
			prtn = "AND SUBOBJECT_NAME = '%s'" % p
		#sys.exit(1)
		q="""
		select distinct grp||'||'||min_rid||'||'||max_rid||'||'||SUBOBJECT_NAME cln
FROM (
SELECT DBMS_ROWID.rowid_create (1,
                                data_object_id,
                                lo_fno,
                                lo_block,
                                0
                               ) min_rid,
       DBMS_ROWID.rowid_create (1,
                                data_object_id,
                                hi_fno,
                                hi_block,
                                100
                               ) max_rid,grp,SUBOBJECT_NAME
  FROM (SELECT DISTINCT grp,
                        FIRST_VALUE (relative_fno) OVER (PARTITION BY grp ORDER BY relative_fno,
                         block_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
                                                                       lo_fno,
                        FIRST_VALUE (block_id) OVER (PARTITION BY grp ORDER BY relative_fno,
                         block_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
                                                                     lo_block,
                        LAST_VALUE (relative_fno) OVER (PARTITION BY grp ORDER BY relative_fno,
                         block_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
                                                                       hi_fno,
                        LAST_VALUE (block_id + blocks - 1) OVER (PARTITION BY grp ORDER BY relative_fno,
                         block_id ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
                                                                     hi_block,
                        SUM (blocks) OVER (PARTITION BY grp) sum_blocks
                   FROM (SELECT   segment_name, relative_fno, block_id,
                                  blocks,
                                  TRUNC
                                      (  (  SUM (blocks) OVER (ORDER BY relative_fno,
                                             block_id)
                                          - 0.01
                                         )
                                       / (SUM (blocks) OVER () / %d)
                                      ) grp
                             FROM dba_extents
                            WHERE segment_name =
                                             UPPER ('%s')
                              AND owner = '%s'
                         ORDER BY block_id)),
       (SELECT data_object_id, SUBOBJECT_NAME
          FROM all_objects
         WHERE object_name = UPPER ('%s') and owner='%s' and data_object_id is not null  %s)
);
		""" % (nosh,from_t[1],from_t[0],from_t[1],from_t[0],prtn)
		#print q
		#sys.exit(1)
		regexp=re.compile(r'(.*)')
		#self._pp['FROM_DB'] =self._pp['TO_DB']
		assert from_db, 'TO_DB is not set.'
		(r, status) = self.do_query(from_db, "set heading off  pagesize 0 serveroutput off feedback off echo off\n%s"  % q,0,regexp)
		#print from_db
		#pprint(r)
		#t= 
		#sys.exit(1)
		return (r, status)		

#ddl spool
echo $0
echo $1
time python data_spooler.py --pipeline_spec=pipeline/posix/pipeline_spec_ddl_spool.xml --pipeline=clients/ddl_spooler/dds_$1.xml $2 $3
 

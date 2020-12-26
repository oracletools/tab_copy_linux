echo $0 $1 $2 $3
time python tc.py --pipeline_spec=pipeline/posix/spool_pipeline_spec.xml --pipeline=clients/tab_copy/$2/tc_$1.xml  

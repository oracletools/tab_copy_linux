echo $0
echo $1
time python tab_copy.py --pipeline_spec=pipeline/posix/dq_pipeline_spec.xml --pipeline=clients/dq_tab_copy/dq_$1.xml $2 
 

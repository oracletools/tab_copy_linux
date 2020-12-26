echo $0
echo $1
time python tab_copy.py --pipeline_spec=pipeline/posix/esales_pipeline_spec.xml --pipeline=clients/tab_copy_esales/tc_$1.xml $2 

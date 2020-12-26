echo $0
echo $1
time python tc.py --pipeline_spec=pipeline/posix/pipeline_spec_gc.xml --pipeline=clients/tab_copy/$2/tc_$1.xml 

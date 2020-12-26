echo $0
echo $1
time python tc.py --pipeline_spec=pipeline/posix/pipeline_spec.xml --pipeline=clients/tab_copy/tc_$1.xml --PARTITION=$2 

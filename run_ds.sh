echo $0
echo $1
time python data_spooler.py --pipeline_spec=pipeline/posix/pipeline_spec.xml --pipeline=clients/data_spooler/tc_$1.xml $2 

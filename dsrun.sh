echo $0
echo $1
time python tc.py --pipeline_spec=pipeline/posix/ds_pipeline_spec.xml --pipeline=clients/data_spooler/ds_$1.xml  

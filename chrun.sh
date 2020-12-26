echo $0
echo $1
time python tc.py --pipeline_spec=pipeline/posix/ch_pipeline_spec.xml --pipeline=clients/convert_hierarchy/ch_$1.xml $2 

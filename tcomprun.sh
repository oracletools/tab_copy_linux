echo $0
echo $1
time python tab_copy.py --pipeline_spec=pipeline/posix/tab_compress_pipeline_spec.xml --pipeline=clients/tab_compress/tcm_$1.xml $2


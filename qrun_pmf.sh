echo $0
echo $1

time python tc_pmf_1.py --pipeline_spec=pipeline/posix/qcopy_pipeline_spec.xml --pipeline=clients/tab_copy/tab_copy/tc_uat_trd_vol_sb_mp_2.xml

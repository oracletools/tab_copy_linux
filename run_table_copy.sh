cd  /u1/apps/smart/refdata/etl/scripts/tab_copy/

. ./.ora_profile
#./run.sh cref_mt_prod2uat
./run.sh cref_mt_uat2dev release
#./run.sh cref_mt_uat2qa&
#./run.sh eref_mt_prod2uat
./run.sh eref_mt_uat2dev release
#./run.sh eref_mt_uat2qa& 

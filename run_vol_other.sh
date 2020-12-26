rm find tmp/logs/SPOOL_VOL_OTHER/* -R
./runspool.sh vol_other spool_data $1 DOGS
./runspool.sh vol_other spool_data $1 IOWA
find tmp/logs/SPOOL_VOL_OTHER/*/ -name *.data  -type f -exec du {} \;


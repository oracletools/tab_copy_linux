rm tmp/logs/SPOOL_CNS_BUYSELL/* -R
echo 'reporting year' $1
./runspool.sh cns_buysell spool_data $1 DOGS&
./runspool.sh cns_buysell  spool_data $1 IOWA&
./runspool.sh cns_buysell spool_data $1 GCS&
./runspool.sh cns_buysell spool_data $1 RADAR
#./runspool.sh cns_buysell spool_data $1 CTS
#./runspool.sh cns_buysell spool_data $1 ATLASCO
#./runspool.sh cns_buysell spool_data $1 ATLASEQ
#./runspool.sh cns_buysell spool_data $1 BRDRDGE
#./runspool.sh cns_buysell spool_data $1 CNS418
#./runspool.sh cns_buysell spool_data $1 CNS274
find tmp/logs/SPOOL_CNS_BUYSELL/*/ -name *.data  -type f -exec du {} \;

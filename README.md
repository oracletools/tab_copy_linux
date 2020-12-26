# TabCopy
TabCopy for Linux (command line)

This script is useful for ad-hoc data transfer between Oracle instances.
Copy is performed by piping data from sqlplus to sqlloader.

Run it like this:
```
run.sh pipeline_name lib_name
```

run.sh details:
```
echo $0
echo $1
time python tc.py --pipeline_spec=pipeline/posix/pipeline_spec.xml --pipeline=clients/TabCopy/$2/tc_$1.xml 
```

`--pipeline_spec` - spec file containing connect info
`--pipeline` - pipeline file


## Copy table data.
  Use `<worker>` XML element to create table copy pipeline
### Simple copy
  Create CDATA element and list source schema name (SHEMA_NAME) and source table name (TABLE_NAME).
  Here target and source schema and table names are the same.
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <![CDATA[SCHEMA_NAME.TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```
### Truncate before copy.
  Add IF_TRUNCATE `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to "1" if you want to truncate and to "0" if you want to append data into target table.
  Here target and source schema and table names are the same.
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <param name="IF_TRUNCATE" value="1"></param>
        <![CDATA[SCHEMA_NAME.TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```
### Partition copy.
  Add PARTITION `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to source partition name.
  Here target and source schema and table names are the same.
  Source and target partition names are the same (target partition is optional). 
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <param name="PARTITION" value="P20140701"></param>
        <![CDATA[SCHEMA_NAME.TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```

### Target table name is different from source.
  Add TO_TABLE `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to target table name.
  Here target schema name is the same as source.
  Source and target table names are different
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
         <param name="TO_TABLE" value="TARGET_TABLE_NAME"></param>
        <![CDATA[SCHEMA_NAME.SOURCE_TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```

### Target schema name is different from source.
  Add TO_SCHEMA `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to target schema name.
  Here target table name is the same as source.
  Source and target schema names are different
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
         <param name="TO_SCHEMA" value="TARGET_SCHEMA_NAME"></param>
        <![CDATA[SOURCE_SCHEMA_NAME.SOURCE_AND_TAGET_TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```
### Target schema and table are different from source.
  Add TO_SCHEMA `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to target schema name.
  Add TO_TABLE `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to target table name.
  
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
         <param name="TO_SCHEMA" value="TARGET_SCHEMA_NAME"></param>
         <param name="TO_TABLE" value="TARGET_TABLE_NAME"></param>
        <![CDATA[SOURCE_SCHEMA_NAME.SOURCE_TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```

### Filtering data.
  Add FILTER `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to your WHERE clause.
  Here target and source schema and table names are the same.
```
<worker name="TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
         <param name="FILTER" value=" WHERE COB_DATE = '01-JUL-14'"></param>
        <![CDATA[SOURCE_SCHEMA_NAME.SOURCE_TABLE_NAME]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```

### Sequential copy of multiple tables
  Create CDATA element and list SCHEMA_NAME.TABLE_NAME pairs.
  Here target and source schemas are the same.
```
<worker name="SEQUENTIAL_TABLE_COPY">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <![CDATA[
        SCHEMA_NAME.TABLE_NAME_1
        SCHEMA_NAME.TABLE_NAME_2
        SCHEMA_NAME.TABLE_NAME_3
        SCHEMA_NAME.TABLE_NAME_4
        SCHEMA_NAME.TABLE_NAME_5]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

```

### Parallel copy copy of multiple tables
  Add param FLOW_TYPE to `<globals>`. Set value to "ASYNC" for parallel table copy, or "SYNC" for sequential.
  Create multiple `<worker>` elements (one per each table).
  Here target and source schemas are the same.
```
<globals> 
	...
	<param name="FLOW_TYPE" value="ASYNC"></param>	
	...
</globals>

<worker name="TABLE_1">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <![CDATA[
        SCHEMA_NAME.TABLE_NAME_1
        ]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>

<worker name="TABLE_2">
  <exec_dml>
    <sqlp  method="%COPY_METHOD%" >
        <![CDATA[
        SCHEMA_NAME.TABLE_NAME_2
        ]]>
      </sql_template>
    </sqlp>
  </exec_dml>
</worker>


```



##Query copy.
  Used to copy query results between oracle instances.
  
### Simple query.
  Create CDATA element and list query.
  Add TO_TABLE `<param>` child element to `<sqlp>` spec.
  Set attribute `value` to target table name.
  Here target and source schemas are the same.
  It will not tork without TO_TABLE param.
```
<worker name="QUERY_COPY">
  <exec_query_copy>
    <table_utils 	method="%QUERY_COPY_METHOD%" >
	  <param name="TO_TABLE" value="MAN_REF_GMI_EXCH_DATA"></param>	
      <sql_template>
        <![CDATA[select * from csmartvol.MAN_REF_GMI_EXCH_DATA]]>
      </sql_template>
    </table_utils>
  </exec_query_copy>
</worker>

```
### Create target table.
  Add IF_CREATE_TARGET_TABLE `<param>` child element to `<table_utils>` spec.
  Set attribute `value` to "1" you want to create target table, and to "0" if do not.
  Here target and source schemas are the same.
  It will not tork without TO_TABLE param.
```
<worker name="QUERY_COPY">
  <exec_query_copy>
    <table_utils 	method="%QUERY_COPY_METHOD%" >
	<param name="TO_TABLE" value="MAN_REF_GMI_EXCH_DATA"></param>
	<param name="IF_CREATE_TARGET_TABLE" value="0"></param>
      <sql_template>
        <![CDATA[select * from csmartvol.MAN_REF_GMI_EXCH_DATA]]>
      </sql_template>
    </table_utils>
  </exec_query_copy>
</worker>

```

### Running multiple queries in parallel.
  Add param FLOW_TYPE to `<globals>`. Set value to "ASYNC" for parallel table copy, or "SYNC" for sequential.
  Create multiple `<worker>` elements (one per each table).
  Add TO_TABLE `<param>` child element to each `<sqlp>` spec element.
  Set attribute `value` to target table name.
  It will not tork without TO_TABLE param.
  
  Here target schema name defined by connect user
  .
```
<globals> 
	...
	<param name="FLOW_TYPE" value="ASYNC"></param>	
	...
</globals>

<worker name="QUERY_COPY_1">
  <exec_query_copy>
    <table_utils 	method="%QUERY_COPY_METHOD%" >
	  <param name="TO_TABLE" value="TO_TABLE_1"></param>	
      <sql_template>
        <![CDATA[select * from SCHEMA_NAME_1.TABLE_NAME_1]]>
      </sql_template>
    </table_utils>
  </exec_query_copy>
</worker>

<worker name="QUERY_COPY_2">
  <exec_query_copy>
    <table_utils 	method="%QUERY_COPY_METHOD%" >
	  <param name="TO_TABLE" value="TO_TABLE_2"></param>	
      <sql_template>
        <![CDATA[select * from SCHEMA_NAME_2.TABLE_NAME_2]]>
      </sql_template>
    </table_utils>
  </exec_query_copy>
</worker>

<worker name="QUERY_COPY_3">
  <exec_query_copy>
    <table_utils 	method="%QUERY_COPY_METHOD%" >
	  <param name="TO_TABLE" value="TO_TABLE_3"></param>	
      <sql_template>
        <![CDATA[select * from SCHEMA_NAME_3.TABLE_NAME_3]]>
      </sql_template>
    </table_utils>
  </exec_query_copy>
</worker>


```


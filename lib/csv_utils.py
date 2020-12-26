#!/usr/bin/python2.4
#
# Copyright 2009 . All Rights Reserved.

"""This module contains all data access/extraction routines for CSV files
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'


import extracter

class csv_extracter(extracter.Extracter):
  """A class for extracting dimension data from csv file."""

  def __init__(self, processmeta, extract_logger):
    """Initializes the extracter.  See also Extracter.__init__.

    Args:
      extract_logger: An object supporting the methods info(message),
        warning(message), and error(message) where message is a string.
        The intent of course is that we wish to log messages using the
        provided logger.
    """
    extracter.Extracter.__init__(self, processmeta, None, extract_logger)
    self._process_meta= processmeta
    self._output_files = {}

  def Run(self, etl_object):
    """Start the extraction job.

    Note that this class requires that we had already set the
    output_pipe attribute via the set_output_pipe simple setter.
    The output_pipe attribute is inherited from the Worker class
    via the Extracter class.

    Args:
      etl_object: table XML object from etlmeta
    """
    self.dump_file = self.ReadAndDump(etl_object)
    self._output_files[etl_object.table_name()] = [self.dump_file]

  def ReadAndDump(self, etl_object):
    """ Parses client etl.xml file(s) and dumps em in tmpdir """
    assert etl_object.source_extracter().export_fields()
    assert etl_object.source_extracter().export_clients()
    # define client etl files location
    file_location = "%s%s" % (self._process_meta.CSV_EXTRACT_ROOT(), 
        etl_object.source_extracter().relative_path())
    dump_file = self._process_meta.LOAD_ROOT() + etl_object.name()+ '.txt'
    #fileutil_wrapper.Copy(file_location, dump_file, self._logger)
    self._logger.info("CSV file copied successfully.")
    etl_object._logger.info("CSV file copied successfully.")
    return dump_file

    assert etl_object.source().ldapinfo().filterstr()
    filterstr = str(etl_object.source().ldapinfo().filterstr())
    user_info_rs = list(google_ldap.QueryLDAP(filterstr=filterstr))
    if len(user_info_rs)==0:
      self._logger.fatal("LDAP query for filter '%s' returns no records." % 
                         filterstr)
    # TODO: implement fingerprinting
    dump_file =self._process_meta.tmpfile_dir()   + etl_object.name()+ '.txt'
    load_root = self._process_meta.LOAD_ROOT() + etl_object.name()+ '.txt'
    delimiter = '|' 
    dialect    = csv.excel
    quotechar  = '"'
    writer = csv.writer(open(dump_file, "wb"),
                             dialect   = dialect,
                             quotechar = quotechar,
                             delimiter = delimiter)
    fields = string.split(etl_object.source_extracter().ldap_fileds(), ',') 
    for i in range(0, len(user_info_rs)):
      row =[] 
      for field in fields:
        value = user_info_rs[i].GetValue(field)
        if value:
          row.append(value)
        else:
          row.append('')
      writer.writerow(row)
      etl_object._output_data[user_info_rs[i].GetValue('employeeNumber')] = row
    self._logger.info("Ldap information extracted successfully.")
    etl_object._logger.info("Ldap information extracted successfully.")
    ## TODO: implement fingerprinter
    fileutil_wrapper.Copy(dump_file, load_root, self._logger)
    import os.path
    self._logger.info("dump file size= %d" % os.path.getsize(dump_file))
    self._logger.info("output file size= %d" % os.path.getsize(load_root))
    return dump_file
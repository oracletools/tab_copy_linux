#!/usr/bin/python2.4
#
# Copyright 2010 . All Rights Reserved.

"""Copy object pulls data out of a data source for insert.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

from worker import Worker

class Copy(Worker):
  def __init__(self, processmeta, fingerprinter, logger):
    """Initialize the Extracter.

    Args:
      fingerprinter: A fingerprint manager that tells us how to do incremental
        extract.
      processmeta - pipeline process meta 
      we extract
    """
    self._process_meta= processmeta
    self._fingerprinter = fingerprinter
    self._logger = logger
    self._num_of_records_extracted = 0

  def NumOfRecordsExtracted(self):
    return self._num_of_records_extracted

  def Run(self, args):
    """Start the extraction job in production."""
    pass

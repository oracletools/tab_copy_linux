#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""Simple utilities for working with the os.  Provides timing, logger, and
remote or local exection.  Unix-dependent."""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'



import time
import commands
import os
import string
from pprint import pprint
import logger


def RemoteMkdirWithMode(host, dir, mode, remote_user, recurse=0):
  """create the directory <dir> on <host>, assuming it's possible to ssh as
  <remote_user>.  If recurse is non-zero, creates any needed parents of <dir>.

  sets the directory access to <mode>

  returns 0 on failure, 1 on success.
  """
  if recurse:
    switch = '-p'
  else:
    switch = ''
  return RemoteExec(host,
                    "if [ ! -e %s ]; then mkdir %s %s; chmod %d %s; fi" % \
                    (dir, switch, dir, mode, dir), remote_user)


def RemoteMkdir(host, dir, remote_user, recurse=0):
  """create the directory <dir> on <host>, assuming it's possible to ssh as
  <remote_user>.  If recurse is non-zero, creates any needed parents of <dir>.

  makes the directory user-writeable

  returns 0 on failure, 1 on success.
  """
  return RemoteMkdirWithMode(host, dir, 700, remote_user, recurse)


def LocalMkdir(dir, recurse=0):
  """create the directory <dir>. If recurse is non-zero, creates any
  needed parents of <dir>.

  returns 0 on failure, 1 on success.
  """
  if recurse:
    switch = '-p'
  else:
    switch = ''
    #print
    #print os.name
    #print
    #sys.exit()
  if os.name == 'nt':
	  return LocalExec("mkdir %s "  % (dir))
  else:
	  return LocalExec("if [ ! -e %s ]; then mkdir %s %s; chmod %d %s; fi" \
					   % (dir, switch, dir, 755, dir))


def LocalMkSymlink(target, name):
  """creates the symlink name->target.

  returns 0 on failure, 1 on success.
  """
  return LocalExec("ln -s %s %s" % (target, name))


def HeuristicRMSafetyCheck(path):
  """A heuristic safety check to prevent rm -rf / and the like.

  Logs to fatal if the safety assertions are false.
  """
  path_elements = path.split('/')
  if len(path_elements) < 4: # path must have at least 4 elements.
    logger.fatal('Cannot rm -rf %s: path too shallow.' % path)

def RemoteRM(host, file, remote_user='root', recurse=0):
  """remove the file <file> on <host>.  protects against non-existence
  of <file>

  returns 0 on failure, 1 on success.
  """
  if recurse:
    HeuristicRMSafetyCheck(file)
    switches = 'rf'
  else:
    switches = 'f'
  return RemoteExec(host, 'if [ -e %s ]; then rm -%s %s; fi' % \
                    (file, switches, file), remote_user)


def LocalRM(file, recurse = 0):
  """remove the file <file> on <host>.  protects against non-existence
  of <file>

  returns 0 on failure, 1 on success.
  """
  if recurse:
    HeuristicRMSafetyCheck(file)
    switches = 'rf'
  else:
    switches = 'f'
  return LocalExec('if [ -e %s ]; then rm -%s %s; fi' % (file, switches, file))

def LocalRmdir(dir):
  from distutils import dir_util
  dir_util.remove_tree(dir)

def RemoteExec(host, command, remote_user):
  """executes <command> on <host>, assuming it's possible to ssh as
     <remote_user>.

  returns 0 on failure, 1 on success.
  """
  if host == 'localhost' and remote_user == os.getlogin():
    return LocalExec(command)
  else:
    ssh_command = string.replace(string.replace(command, '\\', '\\\\'),
                                 '"', '\\"')
    return LocalExec('ssh -1 -n %s@%s "%s"' % (remote_user, host, ssh_command))


def LocalExec(command, showable=1):
  """executes <command> and logs its output, status, and timing information.

  Args:
    command: a string type, the command to be executed. E.g. "cp fileA fileB"
    showable: an integer type, indicating if the command could be written to
      logger or not. 1 means writable in logger, 0 means not writable in logger.

  Returns:
    Execute the shell <command>, and returns 0 on failure, 1 on success.
  """

  if showable:
    logger.info('executing %s' % command, __name__)
  else:
    log_message = ('executing a command which is not showable due to sensitive',
                   ' information such as password.')
    logger.info(log_message, __name__)

  start_time = time.time()
  # The command may take a long time, so flush our log.
  logger.flush_thread_specific_logfile()

  (exitstatus, output) = commands.getstatusoutput(command)

  end_time = time.time()

  logger.info('LocalExec status: %s elapsed time: %s output: %s command: >>%s<<'
  % (exitstatus, FormatElapsedTime(end_time - start_time), output, command), __name__)

  return not exitstatus

def FormatElapsedTime(diff):
  return diff
def SCP(source_host, source_file, dest_host, dest_file, source_user,
        dest_user):
  """copy <source_host>:<source_file> to <dest_host>:<dest_file>.  assumes
  ssh access for <source_user>@<source_host> and <dest_user>@<dest_host>

  returns 0 on failure, 1 on success.
  """
  # scp is issued via a remote exec on the destination machine to ensure
  # that it will complete, even when the source machine is in prod
  # scp'ing/ssh'ing from prod to corp is not possible
  return RemoteExec(dest_host, 'scp -1 -B -C %s@%s:%s %s' % \
                    (source_user, source_host, source_file, dest_file),
                    dest_user)

def HasSSHIdentity(identity):
  """Returns 1 if the ssh-agent for the current context has the specified
  identity, 0 otherwise.

  This is useful for identifying the situation when a machine has been
  rebooted and the identity has not yet been added to the agent.
  """
  return LocalExec('ssh-add -l | grep %s' % identity)

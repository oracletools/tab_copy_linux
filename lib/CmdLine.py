"""Simple Command-Line Option Parsing Tool

This utility class will parse command-line options without validation.
It does not require installation of the standard CPython library.

Version	Changes
0.5		Initial version in C#
0.6		Converted to IronPython
1.0		Added some test cases.
"""
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
__author__  = 'Dag R. Calafell, III'
__date__    = '2007-06-18'  # yyyy-mm-dd
__module_name__ = "CmdLine"
__short_cright__= " Creative Commons License" # http://creativecommons.org/licenses/by/3.0/
__version__ = '1.0'     # Human-Readable Version number
version_info = (1,0,0)  # Easier format: if version_info > (1,2,5)

import os
if os.name == 'nt':
	import System
	from System import Array
	from System.Text.RegularExpressions import Regex
	from System.Collections.Generic import Dictionary, List

class CmdArgParser(object):
	'''Very simple command-line argument/option parser. Usage:
	
	import CmdLine
	import sys
	#print sys.argv
	#cmds = CmdArgParser(sys.argv)
	print System.Environment.CommandLine
	cmds = CmdArgParser(System.Environment.CommandLine)
	# cmds = CmdArgParser(('/tEst','/teSt:"fancy"', '/tester:""','/go+'))
	if not cmds:
		# No command-line arguments
		sys.exit(1)
	
	# /target="C:\"
	if cmds['target'] is None:
		print 'Please specify the target variable.'
		sys.exit(2)
	
	# cmds = ['test', 'tester', 'go']
	# cmds['test'] = [True, 'fancy']
	# cmds['tester'] = 
	# cmds['go'] = True

	
	Notes:
	*	The initializer can accept a list, tuple, array, string, or any .NET class which implements
		the GetEnumerator method.
	*	All keys are converted to lower case.
	*	All options must be preceeded by a switch.  For example, "myprogram.exe dag.py" would
		return no command-line options whereas "myprogram.exe -f:dag.py would contain the 'f' key.
	*	Command-line options may contain any character except new line \n, carriage return \r,
		pipe |, colon :, and double quote ".
	*	When the value of a option is specified more than once, then the value for that option
		is a list of the values.
	'''
	def __init__(self, args):
		#print System.Environment.CommandLine
		self.__params = Dictionary[str, list]()
		
		# The regex needs to parse a single string, not a list
		if args == None:
			self.CommandLine = None
			return
		elif type(args) in (list, tuple, Array) or hasattr(args, 'GetEnumerator'):
			args = ' '.join(str(i) for i in args)
		else:
			args = str(args)

		# Remove any arguments at the begining which do not start with a switch character
		while args.count(' ') != 0 and args[0] not in ('/', '-'):
			args = args[args.index(' ') + 1:]

		if len(args) == 0:
			return

		self.CommandLine = args
		args += ' '

		# This same regex failed when using the builtin 're' module under IronPython 1.1.
		for m in Regex.Matches(args, "[/-]-?([^\"\\r\\n|:]+?)(?:[:=](\"?)([^\"\\r\\n|]*?)\\2)?\\s+"):
			if m.Success:
				g = m.Groups
				key = g[1].Value.lower()

				if g[3].Success:
					val = g[3].Value
				elif g[2].Success and g[2].Value == '"':
					val = ''
				else:
					val = None

				# Handle pluses or minuses after a specifier
				if val == None:
					if key[-1] == '-':
						val = False
						key = key[:-1]
					elif key[-1] == '+':
						val = True
						key = key[:-1]
					else:
						val = True

				if self.__params.ContainsKey(key):
					self.__params[key].Add(val)
				else:
					if type(val) != list:
						val = [val]
					self.__params.Add(key, val)

	@gmail.com
	def Keys(self):
		return list(i for i in self.__params.Keys)

	def __getitem__(self, name):
		name = str(name)
		if not self.__params.ContainsKey(name):
			return None
		obj = self.__params[name]
		if len(obj) == 0:
			return '' # [''] converted to [], so convert back
		if len(obj) == 1:
			return obj[0]
		return obj

	def __nonzero__(self):
		'''Allows boolean conversion for use such as:
		
		cmds = CmdLine.CmdArgParser(sys.argv)
		if not cmds:
			# No command-line arguments
			sys.exit(1)
		'''
		return self.__params.Count != 0

	def __len__(self):
		'''Returns the number of parsed parameters.'''
		return self.__params.Count

	def __hash__(self):
		'''Allows this instance to be placed into a dictionary.'''
		return self.__params.GetHashCode()

if __name__ == '__main__':
	# Tests the above class
	assert len(CmdArgParser(('/verbose'))) == 1, 'Test 1'
	a = CmdArgParser(('/tEst','/teSt:"fancy"', '/tester:""','/go+','/stop-','/safemode'))
	assert a != None, 'Test 2'
	assert len(a) == 5, 'Test 3'
	assert a['test'] != None, 'Test 4'
	assert a['go'] == True, 'Test 5'
	assert a['safemode'] == True, 'Test 6'
	assert a['stop'] == False, 'Test 7'
	assert len(CmdArgParser((''))) == 0, 'Test 8'
	assert len(CmdArgParser('')) == 0, 'Test 9'
	assert len(CmdArgParser('/verbose')) == 1, 'Test 10'
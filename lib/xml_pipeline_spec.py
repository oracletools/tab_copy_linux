#!/usr/bin/python2.4
#
# Copyright 2009 . All Rights Reserved.

"""Metadata models the XML structure for the pipeline spec file.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import xml_loader
from xml.dom import minidom
from pprint import pprint
#import logger
import sys

#######################################################
def FromXML(path, logger=None):
	#self._logger.info( path)
	dom = minidom.parse(path)
	#print path
	#pprint (dir(dom))
	#print dom.toxml()
	for node in dom.childNodes:
		#print dir(node)
		for node1 in node.childNodes:
			#print node1
			pass
		
	#sys.exit(1)
	"""Reads the assembler from an XML file."""
	#return xml_loader.FromXML(path, tag_handler_mapper)
	return getPipelineSpec(dom,logger)

def getPipelineSpec(dom, logger=None):
	test_spec = {}
	#pprint (dir(dom))
	#test = []
	ts= dom.getElementsByTagName('test_spec')
	#print len(ts[0].childNodes)
	for node  in ts[0].childNodes: 
				#node = ts[nid]
				#print dir(node)
				#print node.nodeName
				#sys.exit(1)
				if node.nodeName == 'connector':
						connector ={}
						
						for subnode in node.childNodes:
								#_logger.info(subnode.nodeName,__name__)
								#pprint( dir(subnode))
								#print subnode.nodeName
								#pprint( subnode.nodeType)
								
								if subnode.nodeType==1: # filter out #text nodes
									if subnode.hasAttributes():
										#print dir(subnode.attributes)
										connector[subnode.nodeName]={}
										for i in subnode.attributes.items():
											#print i
											connector[subnode.nodeName][i[0]]=i[1].strip()
										#pprint((connector[subnode.nodeName]))
										#sys.exit(1)
										#connector[subnode.nodeName]={'schema':subnode.getAttribute('schema'),
										#								'pword':subnode.getAttribute('pword'),
										#								'sid':subnode.getAttribute('sid')}
						test_spec[node.nodeName]=connector
						#pprint(connector)
						#sys.exit(1)
				if node.nodeName == 'process_spec':
						#pprint(dir(node.attributes))
						test_spec[node.nodeName]={}
						for attr, attrval in node.attributes.items():
								#pprint(attr)
								test_spec[node.nodeName][attr]=attrval.strip()

				if node.nodeName == 'default':
						default ={}
						if node.hasAttributes():
							default['attr']={}
							for i in node.attributes.items():
								default['attr'][i[0]]=i[1].strip()
						for subnode in node.childNodes:
								#logger.sys(subnode.nodeName)
								#logger.sys(subnode.nodeType)
								if subnode.nodeType==1: # filter out #text nodes
									default[subnode.nodeName]={}
									if subnode.hasAttributes():

										default[subnode.nodeName]['attr']={}
										for i in subnode.attributes.items():
											default[subnode.nodeName]['attr'][i[0]]=i[1].strip()
								for subnode2 in subnode.childNodes:
									#logger.sys(subnode2.nodeName)
									#logger.sys(subnode2.nodeType)
									if subnode2.nodeType==1: # filter out #text nodes
										default[subnode.nodeName][subnode2.nodeName]={}
										if subnode2.hasAttributes():											
											default[subnode.nodeName][subnode2.nodeName]['attr']={}
											for i in subnode2.attributes.items():
												default[subnode.nodeName][subnode2.nodeName]['attr'][i[0]]=i[1].strip()
									for subnode3 in subnode2.childNodes:
										#logger.sys(subnode3.nodeName)
										#logger.sys(subnode3.nodeType)
										if subnode3.nodeType==1: # filter out #text node
											#add params
											if not default[subnode.nodeName][subnode2.nodeName].has_key(subnode3.nodeName):
												default[subnode.nodeName][subnode2.nodeName][subnode3.nodeName]={}												
											if subnode3.hasAttributes():											
												#default[subnode.nodeName][subnode2.nodeName][subnode3.nodeName]['attr']={}
												#for i in subnode3.attributes.items():
												default[subnode.nodeName][subnode2.nodeName][subnode3.nodeName][subnode3.getAttribute('name')]=subnode3.getAttribute('value').strip()											
						test_spec[node.nodeName]=default
						#logger.sys(test_spec[node.nodeName])
						#sys.exit(1)						
				if node.nodeName == 'worker':
						worker = {}
						#pprint(dir(worker))
						#sys.exit(1)
						for subnode in node.childNodes:
							#print subnode.nodeName
							#print subnode.nodeType
							#_logger.info(subnode.nodeName,__name__)
							if subnode.nodeType==1: # filter out #text nodes
								if subnode.hasAttributes():
									if not worker.has_key(subnode.nodeName):
										worker[subnode.nodeName]={}
									if not worker[subnode.nodeName].has_key(subnode.getAttribute('name')):
										worker[subnode.nodeName][subnode.getAttribute('name')]={}									
									if not worker[subnode.nodeName][subnode.getAttribute('name')].has_key('attr'):
										worker[subnode.nodeName][subnode.getAttribute('name')]['attr']={}									
									for attr, attrval in subnode.attributes.items():
										#pprint(attr)
										worker[subnode.nodeName][subnode.getAttribute('name')]['attr'][attr]=attrval.strip()

									#worker[subnode.nodeName][subnode.getAttribute('name')]={
										#'module_name':subnode.getAttribute('module_name')}
								
						test_spec[node.nodeName]=worker
						#pprint (worker)
						#sys.exit(1)
	#print test_spec
	return test_spec
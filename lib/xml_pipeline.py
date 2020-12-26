#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""Metadata models the XML structure for the pipeline spec file.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'

import sys
import xml_loader
from xml.dom import minidom
from pprint import pprint
from logger import logger

root_node = 'etldataflow'

#######################################################
def FromXML(path, spec=None):
	#print path
	out = {}
	dom = minidom.parse(path)
	

	"""Reads the etl pipeline from an XML file."""
	#print dom.firstChild.nodeName
	#pprint (dir(dom))
	cn = dom.getElementsByTagName(root_node)
	#pprint(len(cn))
	confirm( len(cn)>0,
                 'Client %s does not have <%s> node defined.' % (path,root_node))
	confirm(len(cn)==1,
                'Client %s have more than one pipeline defined in single file.' % path)
	#pprint(dir(out))	
	out=getEtlPipelineSpec(cn[0],spec)
	dom.unlink()
	#pprint(out)
	return out
	
	
def getEtlPipelineSpec(root,spec):
	pipeline = {}
	#pipeline['test_plan']=[]
	pipeline[root_node]={}
	
	for item in root.attributes.items():
		#print item
		pipeline[root_node][item[0]]=item[1]
	#sys.exit(1)
	for node in root.childNodes:
		#print node.nodeName
		if node.nodeName=='table':
			getTableSpec(pipeline, node)
		if node.nodeName=='dimension':
			getDimensionSpec(pipeline, node)
		if node.nodeName=='worker':
			getWorkerSpec(pipeline, node,spec)
		if node.nodeName=='globals':
			getGlobalSpec(pipeline, node,spec)
			#pprint(pipeline)
			#sys.exit(1)  
	#pprint(pipeline)
	#sys.exit(1)
	return pipeline
def confirm(test, testname = "Test"):
	if not test:
		msg=  "Failed: " + testname
		raise Exception( '%s (%s)' % (msg, test) )
def in_(msg):
	return '%s_' % msg

def getTableSpec(test_plan, node):
	params = {}
	sqls ={}
	pid = 1
	sid = 1
	#pprint(dir(node))
	for param in node.getElementsByTagName("procedure")[0].childNodes:
	#for param in node.getElementValues("/procedure/param"):
		if param.nodeName == 'param':
			params[pid] = {'name':param.getAttribute('name'),
						   'value':param.getAttribute('value'),
						   'in_out':param.getAttribute('in_out'),
						   'type':param.getAttribute('type')
						  }
			pid +=1
		if param.nodeName == 'sql':
			#pprint(dir(param))
			sqls[sid] = {'descr':param.getAttribute('descr'),
				 'connector':param.getAttribute('connector'),
				 'value':param.childNodes[0].data
																			  }
			sid +=1     
	sql =None
	param_source = node.getElementsByTagName("procedure")[0].getAttribute('param_source')
	if param_source=='sql':
		sql = node.getElementsByTagName("procedure")[0].getElementsByTagName("sql")[0].childNodes[0].data
	test_plan[root_node][node.getAttribute('name')]={'name':node.getAttribute('name'),
		 'procedure':{'name':node.getElementsByTagName("procedure")[0].getAttribute('name'),
					  'connector':node.getElementsByTagName("procedure")[0].getAttribute('connector'),
								  'params':params,
								  'param_source': param_source,
								  #'sql':sql,
								  'sqls':sqls,
								  'param_source':node.getElementsByTagName("procedure")[0].getAttribute('param_source')},
		 'description':node.getElementsByTagName("description")[0].childNodes[0].data,
		 'config':{'connector':node.getElementsByTagName("config")[0].getAttribute('connector'),
						   'log_dest':node.getElementsByTagName("config")[0].getAttribute('log_dest'),
						   'delim':node.getElementsByTagName("config")[0].getAttribute('delim'),
						   'file_tmpl':node.getElementsByTagName("config")[0].getAttribute('file_tmpl'),
						   'file_ext':node.getElementsByTagName("config")[0].getAttribute('file_ext')}}
	#pprint(test_plan)
	#sys.exit(1)

def getWorkerSpec(pipeline, worker, spec):
	se = {}
	dp = {}

	"""
			confirm that worker exists in pipeline specs
	"""
	for node in worker.childNodes:
		#print node.nodeName
		#print dir(node)
		if node.nodeType==node.ELEMENT_NODE:
			confirm(spec['worker'].has_key(node.nodeName), 'Worker <%s> is not listed in pipeline specs.' % node.nodeName)
			#pprint(dir(node))
			for wnode in node.childNodes:
				if wnode.nodeType==wnode.ELEMENT_NODE:
					confirm(spec['worker'][node.nodeName].has_key(wnode.nodeName),
						'<%s> worker <%s> is not listed in pipeline specs.' % (node.nodeName,wnode.nodeName))
	"""
		   confirm that sql_template node is defined
	"""
	#pprint(dir(worker.childNodes))
	confirm(worker.childNodes.length>0,'Worker type is not defined.');
	for wtype in worker.childNodes:
		if wtype.nodeType==wtype.ELEMENT_NODE:
			logger.info( 'Found worker <%s>, length = %d.' % (wtype.nodeName,wtype.childNodes.length))
			#pprint(dir(wtype.childNodes.length))
			name = wtype.nodeName[:4]
			#print name
			if wtype.nodeName[:4] =='exec':
				confirm(wtype.childNodes.length>0,'Worker %s is not defined.' % wtype.nodeName);

	if 0:
		sql_template = worker.childNodes[0].childNodes[0].childNodes[0]
		tmpl = sql_template.childNodes[0].data
		#pprint(tmpl)
		logger.info('Using sql_template:\n<%s>' % tmpl)
		"""
			   find substitutes
		"""
		import re
		p = re.compile('(\{\%[A-Za-z\_]+\%\})')
		#print p
		sub = p.findall(tmpl)
		#print sub
		#pprint (dir(sub))
		subd={}
		for match in sub:
				subd[match]=''
	"""
			Define attributes
	"""
	branch={}
	for attr, attrval in worker.attributes.items():
			if not branch.has_key('attr'):
					branch['attr']={}
			branch['attr'][attr]=attrval
	
	
	#pprint (worker.childNodes)
	#sys.exit(1)
	nid=0
	for node0 in worker.childNodes:
		#print node0.nodeName
		#sys.exit(0)
		
		if 1:
			
			if node0.nodeType==node0.ELEMENT_NODE:
				nodeName=nid
				#print nodeName, node0.tagName
				#"%s_%d" % (node0.tagName, nid)
				if not branch.has_key('node'):
						branch['node']={}            
				if not branch['node'].has_key(nodeName):
						branch['node'][nodeName]={}  
						branch['node'][nodeName]['type']=node0.tagName
				if not branch['node'][nodeName].has_key('attr'):
						branch['node'][nodeName]['attr']={}
				for attr, attrval in node0.attributes.items():
						branch['node'][nodeName]['attr'][attr]=attrval
				for node1 in node0.childNodes:
					if node1.nodeType==node1.ELEMENT_NODE:
						if not branch['node'][nodeName].has_key('node'):
								branch['node'][nodeName]['node']={}                     
						if not branch['node'][nodeName]['node'].has_key(node1.tagName):
								branch['node'][nodeName]['node'][node1.tagName]={}                
						if not branch['node'][nodeName]['node'][node1.tagName].has_key('attr'):
								branch['node'][nodeName]['node'][node1.tagName]['attr']={}
						for attr, attrval in node1.attributes.items():
								branch['node'][nodeName]['node'][node1.tagName]['attr'][attr]=attrval
						for node2 in node1.childNodes:
							if node2.nodeType==node2.ELEMENT_NODE:
								if (node2.tagName=='param'):
									if not branch['node'][nodeName]['node'][node1.tagName].has_key('node'):
											branch['node'][nodeName]['node'][node1.tagName]['node']={}                             
									if not branch['node'][nodeName]['node'][node1.tagName]['node'].has_key(node2.tagName):
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]={}                
									#if not branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName].has_key('attr'):
										   # branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]['attr']={}
									#pprint(dir(node2.attributes))
									#pprint(node2.attributes.item(0).name)
									confirm(node2.attributes.has_key('name'), 'Node %s has no attr "name"' %(node2.tagName) )
									pname=node2.attributes.getNamedItem('name').value
									if not branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName].has_key(pname):
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName][pname]={}

									#pprint(dir(pname))
									for attr, attrval in node2.attributes.items():
										#pprint((node2.attributes['name']))
										branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName][pname][attr]=attrval
										#pprint(node2.tagName)
											#if node2.childNodes.length:
													#branch['node'][nodeName]['node'][node1.tagName]['param'][node2.tagName]['value']=node2.childNodes[0].data
								else:
									if not branch['node'][nodeName]['node'][node1.tagName].has_key('node'):
											branch['node'][nodeName]['node'][node1.tagName]['node']={}                             
									if not branch['node'][nodeName]['node'][node1.tagName]['node'].has_key(node2.tagName):
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]={}                
									if not branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName].has_key('attr'):
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]['attr']={}
									for attr, attrval in node2.attributes.items():
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]['attr'][attr]=attrval
											#pprint(node2.tagName)
									if node2.childNodes.length:
										if not branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName].has_key('data'):
											branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]['data']={}
										branch['node'][nodeName]['node'][node1.tagName]['node'][node2.tagName]['data']=node2.childNodes[1].data
		nid +=1
		   
	#pprint (branch)
	#sys.exit(1)
	if not pipeline[root_node].has_key('worker'):
					pipeline[root_node]['worker']=[]
	pipeline[root_node]['worker'].append(branch)
	#pprint (dir(pipeline[root_node]['worker']))
	#sys.exit(1)

def getGlobalSpec(pipeline, globals, spec):
	se = {}
	dp = {}
	"""
		parse pipelne globals
	"""
	pipeline[root_node]['globals'] ={}
	for node in globals.childNodes:
		
			
		if node.nodeType==node.ELEMENT_NODE:
			if not pipeline[root_node]['globals'].has_key(node.nodeName):
				pipeline[root_node]['globals'][node.nodeName] ={}
			#pprint(dir(node.attributes))
			attr=dict(node.attributes.items())
			#pprint(attr)
			#pprint(dir(node.attributes.getNamedItem('name')))
			pipeline[root_node]['globals'][node.nodeName][attr['name']]=attr['value']


	#pprint(pipeline[root_node]['globals'])
	#sys.exit(1)
	

        
def getDimensionSpec(pipeline, dim):
        se = {}
        dp = {}

        pipeline[root_node][dim.getAttribute('name')]={}
        pipeline[root_node][dim.getAttribute('name')]['table_type'] = 'dimension'
        confirm(len(dim.childNodes) >= 2, 'At least source and extract nodes should be defined.')
        confirm(dim.childNodes[0].nodeName=='source', '<source> is not defined.')
        confirm(dim.childNodes[1].nodeName=='load', '<load> is not defined.')

        #for node in dim.childNodes:
            #pprint (node.nodeName)

        #define specs for dim source extracter
        source = dim.childNodes[0]
        #pprint(dir(dim))
        source=dim.getElementsByTagName('source')
        #pprint((source.length))
        
        confirm(source.length == 1, 'Single source_extracter has to be defined. %d found.' % source.length)
        source_extracter = source[0].childNodes[0]
        logger.info('Found source_extracter <%s>' % source_extracter.nodeName)
        #sys.exit(1)
        se['source_extracter_type']= source_extracter.nodeName
        if source_extracter.nodeName == 'cursor':
                # setting attributes for database fetch
                cursor = source_extracter.nodeName
                confirm(source_extracter.hasAttribute('cursor_type'), 'attribute cursor_type is not defined for source_extracter <%s>.' % source_extracter.nodeName)
                cursor_type_name= source_extracter.getAttribute('cursor_type')
                se['name']=source_extracter.nodeName
                se['cursor_type_name'] = cursor_type_name
                #pprint(dir(source_extracter))
                cursor_type = source_extracter.firstChild
                confirm(cursor_type.nodeName == cursor_type_name, 'Node %s is not of type %s' % (cursor_type_name,cursor_type.nodeName))
                if cursor_type.nodeName == 'query':
                    query = cursor_type.childNodes[0].data
                    se['query'] = query
                    logger.info('Query: %s' % query)

        pipeline[root_node][dim.getAttribute('name')]['source_extracter']=se
        #pprint (pipeline)

        load=dim.getElementsByTagName('load')
        #pprint((load.length))
        
        confirm(load.length == 1, 'Single data_publisher has to be defined. %d found.' % load.length)
        data_publisher = load[0].childNodes[0]
        logger.info('Found data_publisher <%s>' % data_publisher.nodeName)


        dp['data_publisher_type']= data_publisher.nodeName
        if data_publisher.nodeName == 'csvfile':
                #setting attributes for csv dump
                confirm(data_publisher.hasAttribute('log_dest'), 'attribute log_dest is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['log_dest'] = data_publisher.getAttribute('log_dest')
                confirm(data_publisher.hasAttribute('header_line'), 'attribute header_line is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['header_line'] = data_publisher.getAttribute('header_line')
                confirm(data_publisher.hasAttribute('file_ext'), 'attribute file_ext is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['file_ext'] = data_publisher.getAttribute('file_ext')
                confirm(data_publisher.hasAttribute('delim'), 'attribute delim is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['delim'] = data_publisher.getAttribute('delim')
                confirm(data_publisher.hasAttribute('quote'), 'attribute quote is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['quote'] = data_publisher.getAttribute('quote')
                confirm(data_publisher.hasAttribute('file_tmpl'), 'attribute file_tmpl is not defined for data_publisher <%s>.' % data_publisher.nodeName)
                dp['file_tmpl'] = data_publisher.getAttribute('file_tmpl')
        pipeline[root_node][dim.getAttribute('name')]['data_publisher']=dp
        
        #pprint (pipeline)

        
        #sys.exit(1)

        #sys.exit(1)
    
def getProcedureSpec(test_plan, node):
        params = {}
        sqls ={}
        pid = 1
        sid = 1
        #pprint(dir(node))
        for param in node.getElementsByTagName("procedure")[0].childNodes:
        #for param in node.getElementValues("/procedure/param"):
                        if param.nodeName == 'param':
                                        params[pid] = {'name':param.getAttribute('name'),
                                                       'value':param.getAttribute('value'),
                                                       'in_out':param.getAttribute('in_out'),
                                                       'type':param.getAttribute('type')
                                                      }
                                        pid +=1
                        if param.nodeName == 'sql':
                                        #pprint(dir(param))
                                        sqls[sid] = {'descr':param.getAttribute('descr'),
                                                     'connector':param.getAttribute('connector'),
                                                     'value':param.childNodes[0].data
                                                                                                                  }
                                        sid +=1     
        sql =None
        param_source = node.getElementsByTagName("procedure")[0].getAttribute('param_source')
        if param_source=='sql':
                        sql = node.getElementsByTagName("procedure")[0].getElementsByTagName("sql")[0].childNodes[0].data
        test_plan[root_node].append({node.getAttribute('name'):
                        {'name':node.getAttribute('name'),
                         'procedure':{'name':node.getElementsByTagName("procedure")[0].getAttribute('name'),
                                      'connector':node.getElementsByTagName("procedure")[0].getAttribute('connector'),
                                                  'params':params,
                                                  'param_source': param_source,
                                                  #'sql':sql,
                                                  'sqls':sqls,
                                                  'param_source':node.getElementsByTagName("procedure")[0].getAttribute('param_source')},
                         'description':node.getElementsByTagName("description")[0].childNodes[0].data,
                         'config':{'connector':node.getElementsByTagName("config")[0].getAttribute('connector'),
                                           'log_dest':node.getElementsByTagName("config")[0].getAttribute('log_dest'),
                                           'delim':node.getElementsByTagName("config")[0].getAttribute('delim'),
                                           'file_tmpl':node.getElementsByTagName("config")[0].getAttribute('file_tmpl'),
                                           'file_ext':node.getElementsByTagName("config")[0].getAttribute('file_ext')}}})

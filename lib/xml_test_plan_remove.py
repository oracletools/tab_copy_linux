#!/usr/bin/python2.4
#
# Copyright 2009 .  All Rights Reserved.
# 
# Original author AlexBuzunov@gmail.com (Alex Buzunov)

"""Metadata models the XML structure for the Test spec file.
"""

__author__ = 'AlexBuzunov@gmail.com (Alex Buzunov)'


import sys
import xml_loader
from xml.dom import minidom
from pprint import pprint
from logger import logger


#######################################################
def FromXML(path, spec=None):
	print path
	out = {}
	dom = minidom.parse(path)
	root_node = 'etldataflow'

	"""Reads the test plan from an XML file."""
	confirm( dom.firstChild.nodeName==root_node,
                 'Client %s does not have <%s> node defined.' % (path,root_node))
	confirm(dom.childNodes.length==1,
                'Client %s have more than one root node defined.' % path)
	#pprint(dir(out))	
	out=getEtlPipelineSpec(dom,spec)
	dom.unlink()
	pprint(out)
	return out
	
	
def getEtlPipelineSpec(dom,spec):
	pipeline = {}
	#pipeline['test_plan']=[]
	pipeline['etldataflow']={}
	pipeline['name']=dom.firstChild.getAttribute('name')


        for node in dom.firstChild.childNodes:
            if node.nodeName=='test':
                getProcedureSpec(pipeline, node)

            else:
                if node.nodeName=='dimension':
                        getDimensionSpec(pipeline, node)
                else:
                        if node.nodeName=='worker':
                                getWorkerSpec(pipeline, node,spec)
        #pprint(test_plan)
        #sys.exit(1)     
	return pipeline
def confirm(test, testname = "Test"):
    if not test:
        msg=  "Failed: " + testname
        raise Exception( '%s (%s)' % (msg, test) )
def in_(msg):
    return '%s_' % msg

def getWorkerSpec(pipeline, worker, spec):
        se = {}
        dp = {}
        #pprint(dir(worker))
        #pprint((spec))
        #pprint(dir(spec['worker'][worker.childNodes[0].nodeName]))
        #sys.exit(1)
        """
                confirm that worker exists in pipeline specs
        """
        confirm(spec['worker'].has_key(worker.childNodes[0].nodeName), 'Worker <%s> is not listed in pipeline specs.' % worker.childNodes[0].nodeName)
        confirm(spec['worker'][worker.childNodes[0].nodeName].has_key(worker.childNodes[0].childNodes[0].nodeName),
                '<%s> worker <%s> is not listed in pipeline specs.' % (worker.childNodes[0].nodeName,worker.childNodes[0].childNodes[0].nodeName))
        """
               confirm that sql_template node is defined
        """
        confirm(worker.childNodes[0].childNodes[0].childNodes[0].nodeName=='sql_template',
                '<%s> worker <%s> does not have sql_template node defined, <%s> found instead.' % (worker.childNodes[0].nodeName,worker.childNodes[0].childNodes[0].nodeName,worker.childNodes[0].childNodes[0].childNodes[0].nodeName))


        pipeline['etl_pipeline'][worker.getAttribute('name')]={}
        pipeline['etl_pipeline'][worker.getAttribute('name')]['node_type'] = 'worker'
        #confirm(len(dim.childNodes) >= 2, 'At least source and extract nodes should be defined.')
        #confirm(worker.childNodes[0].nodeName=='source', '<source> is not defined.')
        #confirm(worker.childNodes[1].nodeName=='load', '<load> is not defined.')

        for node in worker.childNodes:
            print 'Found node <%s>' % (node.nodeName)
        
        #define specs for dim source extracter
        #source = worker.childNodes[0]
        sql_template = worker.childNodes[0].childNodes[0].childNodes[0]
        tmpl = sql_template.childNodes[0].data
        pprint(tmpl)
        logger.info('Using sql_template:\n<%s>' % tmpl)
        
        #source=worker.getElementsByTagName('source')
        #pprint((source.length))
        
        #confirm(source.length == 1, 'Single source_extracter has to be defined. %d found.' % source.length)
        #source_extracter = source[0].childNodes[0]
        #logger.info('Found source_extracter <%s>' % source_extracter.nodeName)
        #sys.exit(1)
        #se['source_extracter_type']= source_extracter.nodeName
        """
               find substitutes
        """
        import re
        p = re.compile('(\{\%[A-Za-z\_]+\%\})')
        print p
        sub = p.findall(tmpl)
        print sub
        #pprint (dir(sub))
        subd={}
        for match in sub:
                subd[match]=''
        """
                Define attributes
        """
        branch={}
        for attr, attrval in worker.attributes.items():
                if not branch.has_key('attrib'):
                        branch['attrib']={}
                branch['attrib'][attr]=attrval
        
        
        
        for node0 in worker.childNodes:
                if not branch.has_key(node0.tagName):
                        branch[node0.tagName]={}                
                if not branch[node0.tagName].has_key('attrib'):
                        branch[node0.tagName]['attrib']={}
                for attr, attrval in node0.attributes.items():
                        branch[node0.tagName]['attrib'][attr]=attrval
                for node1 in node0.childNodes:
                        if not branch[node0.tagName].has_key(node1.tagName):
                                branch[node0.tagName][node1.tagName]={}                
                        if not branch[node0.tagName][node1.tagName].has_key('attrib'):
                                branch[node0.tagName][node1.tagName]['attrib']={}
                        for attr, attrval in node1.attributes.items():
                                branch[node0.tagName][node1.tagName]['attrib'][attr]=attrval
                        for node2 in node1.childNodes:
                                if not branch[node0.tagName][node1.tagName].has_key(node2.tagName):
                                        branch[node0.tagName][node1.tagName][node2.tagName]={}                
                                if not branch[node0.tagName][node1.tagName][node2.tagName].has_key('attrib'):
                                        branch[node0.tagName][node1.tagName][node2.tagName]['attrib']={}
                                for attr, attrval in node2.attributes.items():
                                        branch[node0.tagName][node1.tagName][node2.tagName]['attrib'][attr]=attrval
                                branch[node0.tagName][node1.tagName][node2.tagName]['value']=node2.childNodes[0].data
                                        
               
        #pprint (branch)
        pipeline['etl_pipeline'][worker.getAttribute('name')]=branch
        pprint (pipeline)


        
def getDimensionSpec(pipeline, dim):
        se = {}
        dp = {}

        pipeline['etl_pipeline'][dim.getAttribute('name')]={}
        pipeline['etl_pipeline'][dim.getAttribute('name')]['table_type'] = 'dimension'
        confirm(len(dim.childNodes) >= 2, 'At least source and extract nodes should be defined.')
        confirm(dim.childNodes[0].nodeName=='source', '<source> is not defined.')
        confirm(dim.childNodes[1].nodeName=='load', '<load> is not defined.')

        for node in dim.childNodes:
            pprint (node.nodeName)

        #define specs for dim source extracter
        source = dim.childNodes[0]
        #pprint(dir(dim))
        source=dim.getElementsByTagName('source')
        pprint((source.length))
        
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

        pipeline['etl_pipeline'][dim.getAttribute('name')]['source_extracter']=se
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
        pipeline['etl_pipeline'][dim.getAttribute('name')]['data_publisher']=dp
        
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
                        if param.tagName == 'param':
                                        params[pid] = {'name':param.getAttribute('name'),
                                                       'value':param.getAttribute('value'),
                                                       'in_out':param.getAttribute('in_out'),
                                                       'type':param.getAttribute('type')
                                                      }
                                        pid +=1
                        if param.tagName == 'sql':
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
        test_plan['etldataflow'].append({node.getAttribute('name'):
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

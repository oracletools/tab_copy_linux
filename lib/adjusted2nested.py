import os, sys
from pprint import pprint
from array import array


def parent(node):
	if node[1]:
		return ttn[node[1]]
	return None		
	
def has_children(node):
	if len(node[2]):
		return True
	return False		

ttn ={}
#--sql

				
def load_hier(root,in_fn,ttn,indexes=(0,1),column_term ='|'):
	#global ttn
	fh = open(in_fn,"r")
	#with open(in_fn,"r") as fh:
	#pprint(indexes)
	(child_col,parent_col) = indexes
	#sys.exit(1)
	if 1:
		i=0
		header_str = fh.readline().strip()
		header= header_str.split(column_term)
		print header,child_col,parent_col
		(child_idx,parent_idx) = (header.index(child_col),header.index(parent_col))
		for line in fh:
			i +=1
			#print i, line
			ln =line.split(column_term)
			ttn[ln[child_idx].strip()] = [ln[child_idx].strip(), ln[parent_idx].strip(),[],0,1,1] 
			#Branch(ln[child_idx], ln[parent_idx].strip())

		#pass
	fh.close()
	#pprint(ttn)
	
	parent_out = ttn[root][1]
	#print parent
	#sys.exit(1)
	ttn[root][1]=None
	for node in ttn.values():
		if node[1]: #.parent_key:
			#if not has_children(parent(node)):
			#	node.parent().children = []
			ttn[node[1].strip()][2] +=[ node ]
	#pprint(ttn)
	#sys.exit(1)
	#ttn.sort()
	return parent_out
	
def set_interval(node):
	(left,right) = (node[4], node[5])
	if has_children(node):
		right=left
		for child in node[2]:
			child[4] = right+1
			(left,right) = set_interval(child)
		last_child=node[2][len(node[2])-1]
		node[5]=last_child[5]+1
		return (node[4],node[5])
	else:
		node[5] =node[4]+1
		return (node[4],node[5])
	

def set_delta_old2(node, level):
	prev_level=level
	prev_left=node[4] #.left
	cnt=0
	if has_children(node):
		prev_level=level+1
		#set L/R increments for all leafs.
		if 0:
			for i in range(len(node[2])-1):
				child=node[2][i]
				if not has_children(child): 
					#left
					node[2][i+1][4]  +=i+1
					#right
					child[5] +=i+2
		for j in range(len(node[2])):
			child=node[2][j]
			cnt +=1
			if prev_level>level+1:
				child[4]  +=(prev_level-level)
				child[4]  +=prev_left
			else:
				child[4]  +=node[4] +j
			(prev_level,prev_left,prev_cnt)= set_delta(child,level+1)
			cnt +=prev_cnt
			if not has_children(child): 
				child[5]  = child[4]  +1 
		node[5] =prev_left+(prev_level-level)+1

	return (prev_level, prev_left,cnt)
	
def set_delta_old(node, level):
	prev_level=level
	prev_left=node[4] #.left
	cnt=0
	pprint(node)
	print has_children(node), parent(node)
	sys.exit(1)
	if has_children(node):
		prev_level=level+1
		if not parent(node): # it's a root
			#print 'childern', len(node[2])
			if 1:
				pprint(node[2][1:])
				
				for child in node[2][1:]:
					print 'adding +1', child[0]
					child[4] +=1
					print 'adding +1', child[0], child[4]
				pprint(node[2][1:])
				#sys.exit(1)
		else:
			for i in range(len(node[2])-1):
				child=node[2][i]
				
				if not has_children(child): # hasattr(child, 'children'):
					node[2][i+1][4]  +=i+1
		for j in range(len(node[2])):
			child=node[2][j]
			cnt +=1
			if prev_level>level+1:
				#print 'prev_level>level+1', prev_level,level, prev_left,node[0], node[4], child[0], child[4]
				child[4]  +=(prev_level-level)
				child[4]  +=prev_left
				#print '||||prev_level>level+1', prev_level,level, prev_left,node[0], node[4], child[0], child[4]
			else:
				child[4]  +=node[4] +j
				#print '--passing',child[4],child[0],node[4],node[0],j
				
			(prev_level,prev_left,prev_cnt)= set_delta(child,level+1)
			#print 'got', prev_level,prev_left,prev_cnt, child[0]
			cnt +=prev_cnt
			if not has_children(child): #hasattr(child, 'children'):
				child[5]  = child[4]  +1 
		node[5] =prev_left+(prev_level-level)+1
	#print 'returning', prev_level, prev_left,cnt
	return (prev_level, prev_left,cnt)
def traverse(title,level,parent):
	#print 'l', level
	queryNode = ttn[title] #'Clothing'
	#print 'queryNode', queryNode
	yield queryNode, level,parent
	if len(title) == 1 and 0:
		yield (title, level)
	else:
		if has_children(queryNode): #hasattr(queryNode, 'children'):
			#queryNode[2].sort()
			for child in queryNode[2]:
				#print child
				for n in traverse(child[0],level+1,queryNode):
					#print n
					yield n

def export_hier_old():
	
	fh = open('export_hier_small_nn_10.log',"w")
	for key,node in ttn.items():
		fh.write('%s|%s|%d|%d\n' % (node[0], node[1],node[4],node[5]))
		print '%s|%s|%d|%d\n' % (node[0], node[1],node[4],node[5])
	fh.close()

def export_hier(out_fn, in_fn, ttn,in_indexes, out_indexes, column_term ='|'):
	import copy
	pprint (in_indexes)
	pprint (out_indexes)
	#sys.exit(1)
	in_fh = open(in_fn,"r")
	out_fh = open(out_fn,"w")
	#with open(in_fn,"r") as fh:
	#pprint(indexes)
	(child_col,parent_col) = in_indexes
	(left_col,right_col) = out_indexes
	#sys.exit(1)
	out ={}
	if 1:
		i=0
		header_str = in_fh.readline().strip()
		header= header_str.split(column_term)
		#print header
		out_header = header_str.split(column_term)
		(child_idx,parent_idx) = (header.index(child_col),header.index(parent_col))
		out_header.extend(out_indexes)
		out_header.sort()
		#pprint(out_header)
		#pprint(header)
		
		safe ='%('
		fmt= '%s%s)s' %(safe, (')s%s%s' % (column_term, safe)).join(out_header).strip())
		fmt = '%s\n' % fmt
		
		#sys.exit(1)
		out_fh.write('%s\n' % column_term.join(out_header))
		for line in in_fh:
			i +=1
			#print i, line
			ln =line.split(column_term)
			
			for ind in range(len(header)):
				out[header[ind].strip()]=ln[ind].strip()
			#pprint (out)
			node=ttn[ln[child_idx]]
			out[left_col]=node[4]
			out[right_col]=node[5]
			out_fh.write(fmt % out)
	in_fh.close()
	out_fh.close()
	print out_fn
	return out_header
lev=lef= cnt =None

root=None
if __name__ == '__main__':
	from timeit import Timer					
	#root='Total  [L1]'

	root ='Clothing'
	root ='1'
	#queryNode = ttn[root] #	
	#lev,lef,cnt=set_delta(queryNode,1)
	#print lev, lef, queryNode.left, queryNode.right
	if 0:
		t = Timer("load_hier(ttn)", "from __main__ import load_hier, ttn")
		print 'Load time: ', t.timeit(1)

		print len(ttn)
		print ttn[root].title
		#print set_delta(ttn[root],1)

		t = Timer("set_delta(ttn[root],1)", "from __main__ import set_delta,ttn,root")
		print 'Convert time: ',t.timeit(1)

		t = Timer("export_hier()", "from __main__ import export_hier,ttn,root")
		print 'Export time: ',t.timeit(1)
	else:
		from_file = 'tmp/logs/ESMARTREF.REF_CTP_GRAND_PRNT_LIST.SPOOL/20120301_120154/data/ESMARTREF.REF_CTP_GRAND_PRNT_LIST.C160970GMAPRL.PRL_HIER_MGD_SEG.data'
		load_hier(from_file, ttn, (0,4),'|')
		set_delta(ttn[root],1)
		export_hier()
		
	if 0:	
		# export
		for key,node in ttn.items():
			print '%15s|%10s|%4d|%4s' % (node.title, node.parent_key,node.left,node.right)
					
	if 0: # show tree
		prev_lev=1
		for n in traverse(root,prev_lev, ''):
			#pprint(n[0])
			print '--'* n[1], n[0][0], '(', n[0][4],',', n[0][5],')'

	#pprint(ttn)
		
		
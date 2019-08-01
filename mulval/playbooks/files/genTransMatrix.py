#!/usr/bin/python

import MySQLdb
import copy
import csv
from datetime import datetime
import os
from pandas import *
import re
from sets import ImmutableSet
from sets import Set
import string
import sys
import yaml

inputDir = sys.argv[1]
matrixFileName = sys.argv[2]
conf_override = {}
coalesced_rules = [ ]
exploit_rules = { }
orNodes = Set([ ])
andNodes = Set([ ])
leafNodes = Set([ ])
cycleNodes = Set([ ])
irv = { }
preds = { }
leafSuccs = { } # ids of nodes this leaf points to 
leafPreds = { } # ids of leafs that point to this node
succs = { }
branchNodes = Set([ ])
nodeNames = { }

cycleDependencies = { }
cycleData = { }

paths = { }

phi = { }
psi = { }
chi = { }
delta = { }

# Variables used in Tarjan's algorithm
cycles = [ ]
stack = [ ]
indices = { }
lowlink = { }
tarjanIndex = 0

################################################################################
# Functions to return copied sets of immediate predecessors / successors
#   for a single node; also, negated sets of predecessors

# Return all immediate successors for given node
def getSuccs( node ) :
    global succs
    return succs[node].copy()

# Return all immediate predecessors for given node
def getPreds( node ) :
    global preds
    return preds[node].copy()

# Return negation of immmediate predecessors for given node
def getPredsNeg( node ) :
    global preds
    predSet = getPreds(node)
    negPredSet = Set([ ])
    for p in predSet :
        negPredSet.add( -p )
    return negPredSet

# try to convert string to number
# return 'nan' otherwise 
def is_number(s):
    try:
        return float(s)
        
    except ValueError:
        return False

# Return a copy of OR nodes
def getORs(  ) :
    global orNodes
    return orNodes.copy()

# Return copy of 'multihop' (non exploit) OR nodes
def getMHOrs(  ) :
    global orNodes
    myOrs =  copy.deepcopy(orNodes)
    MHOrs = Set ()
     
    for o in myOrs:
        for preA in preds[o]:
            ruleText = nodeNames[preA]    
            # check if we need to get exploit id/CVSS score
            #if 'multi-hop access' in ruleText:
            if any(rule in ruleText for rule in coalesced_rules):
                MHOrs.add(o)
    return MHOrs

# get the CVSS score for a cveid
def getCVSSscore( cveid):
    #score = '1'
    # This dictionary will go in a config file for hypothetical scoring
    #-- here
    score = 'null' # the score to return
    #cveDict = {} # lookup the advance score by rule text
    #cveDict['CVE-2014-9796'] = 6.8 # Ubuntu 14.04 remote code exec (PCRE)
    #cveDict['CVE-2015-7501'] = 2 # ODL remote code execution      
    #cveDict['CVE-2016-xxxx'] = 9.5 # p3_c exploit from SDN controller
#    if not conf_override:     
    #with open('/tmp/mulval_results/scoreDict.yml') as f:
    #    conf_override = yaml.safe_load(f)
    try:
        con = MySQLdb.connect('localhost', 'nvd', 'nvd', 'nvd')
        cur = con.cursor(MySQLdb.cursors.DictCursor)            
        cur.execute("select score from nvd where id = '%s'" % (cveid))
        res=cur.fetchone() # the cveid or None it 
        if res:            
            score = res['score']  
            #print 'Found cveid ' + cveid + ' with score: ' + str(score)  

        else:
            #if cveid in cveDict.keys():            
            #    score = cveDict[cveid]  
            #scoreDict = conf_override['scoreDict']
            if cveid in exploitDict.keys():
                score = exploitDict[cveid]
#                print 'Matched hypothetical score ' + cveid + ' : ' + str(score)
                    
            else:
                print 'bad cveid (result unknown): setting CVSS to 1!!!**** [' + cveid + ']'
                score = 1
    
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)
    
    finally:        
        if con:
            con.close()      
    
    return score

def writeTmatrix(filename):
    with open(filename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(tmatrixmap)
        writer.writerows(reducedtmatrix)
    

# search the given AND node looking for the type of advance. 
# If exploit return a CVE score otherwise return advance type score 
def getnodevulns( andNode ):
    # This dictionary will go in a config file for hypothetical scoring

    # here
    score = 'null' # the score to return
    #scoreDict = {} # lookup the advance score by rule text
    #scoreDict['direct network access'] = 10
    #scoreDict['NFS shell'] = 9.5
    ##scoreDict['multi-hop access'] = 9
    #scoreDict['execCode implies file access'] = 7.8
    #scoreDict['NFS semantics'] = 9.6
    #scoreDict['Trojan horse installation'] = 5   
    #scoreDict['local exploit'] = 5   
#    if not conf_override:
    #with open('/tmp/mulval_results/scoreDict.yml') as g:
    #   conf_override = yaml.safe_load(g)
    #    exploitsDict = conf_override['exploit_rules']
    
    # determine how we advance and assign a value
    ruleText = nodeNames[andNode]
    
    # check if we need to get exploit id/CVSS score
    #if 'remote exploit of a server program' in ruleText: # theres an exploit in the LEAFs
    if any(exploit in ruleText for exploit in exploitDict.keys()):  # theres an exploit in the LEAFs
        for p in leafPreds[andNode]: # look for vulnExists() LEAF
            # catch all elements for future use
            # vulnid is in group 2
            # vulExists((webServer,'CAN-2002-0392',httpd,remoteExploit,privEscalation)
            matchObj = re.match( r'vulExists\((.*),(.*),(.*),(.*),(.*)\)', nodeNames[p], re.M|re.I)
            
            # assuming only 1 vuln per AND... 
            if matchObj:
                mycveid = matchObj.group(2).strip('\'')
                #print mycveid
                score = getCVSSscore(mycveid)
            #===================================================================
            # if matchObj:
            #     print "matchObj.group() : ", matchObj.group()
            #     print "matchObj.group(1) : ", matchObj.group(1)
            #     print "matchObj.group(2) : ", matchObj.group(2)
            #     print "matchObj.group(2) : ", matchObj.group(3)
            #     print "matchObj.group(2) : ", matchObj.group(4)
            #     print "matchObj.group(2) : ", matchObj.group(5)
            # else:
            #     print "No match!!"
            #===================================================================
    else: 
        found = False # warn if we cant match this Rule
        #if not scoreDict:
        #scoreDict = conf_override['scoreDict']
        for k in exploitDict.keys():
            print '!!!!!!!!!!!!!!!!  ' + k + ' !!!!!!!!!!! '
            if k in ruleText: 
                score = exploitDict[k]
                found = True
                
        if not found:
            print '*** Couldnt find rule text (must be added) id: ' + str(andNode) + ' | ' + nodeNames[andNode]
    
    return score

################################################################################


################################################################################
################################################################################
## Main code block
################################################################################
################################################################################

if len(sys.argv) != 3:
    print '<usage> genTransMatrix.py inputdir outputfile.csv'
    sys.exit()

# configs
with open('/tmp/mulval_results/scoreDict.yml') as f:
    conf_override = yaml.safe_load(f)
    coalesced_rules = conf_override['coalesce_rules']
    exploitDict = conf_override['exploit_rules']


# Identify and initialize all AND/OR nodes    
verticesFile = open( inputDir + '/VERTICES.CSV', 'r')
while verticesFile :
    # Read line from file, split into various values
    pieces = verticesFile.readline().strip().split(',')
    count = len(pieces)
    if count == 1 : # line is empty (no more data - break from loop)
        break

    print 'pieces:', pieces
    nodeID = int(pieces[0])
    nodeText = ','.join(pieces[1:count-2]).strip('"')
    nodeType = pieces[count-2].strip('"')
    nodeVal = float(pieces[count-1])
    # If OR/AND-node, add to node sets
    if nodeType == 'OR' or nodeType == 'AND':   
        nodeNames[nodeID] = nodeText
        preds[nodeID] = Set([ ])
        succs[nodeID] = Set([ ])
        chi[nodeID] = Set([ ])
        delta[nodeID] = Set([ ])
        if nodeType == 'OR':
            orNodes.add(nodeID)          
        else : # type == '"AND"'
            andNodes.add(nodeID)
            irv[nodeID] = nodeVal            
            leafPreds[nodeID] = Set([ ])
    
    # If LEAF node add to node set 
    if nodeType == 'LEAF':
        nodeNames[nodeID] = nodeText
        leafSuccs[nodeID] = Set([ ])
        leafNodes.add(nodeID)
        
        
verticesFile.close()

# Create virtual root node, initialize values
root = 0
preds[root] = Set([ ])
succs[root] = Set([ ])
chi[root] = Set([ ])
delta[root] = Set([ ])
orNodes.add(root)

phi[root] = 1 # need to change if actually keeping graph risk value
#if root in branchNodes :
#    setPsiValue( root, root, 1 )

# Record all edges in approprioate predecessor/successor sets
arcsFile = open(inputDir + '/ARCS.CSV', 'r')
#arcsFile.readline() # ignore first line in file
while arcsFile :
    # Read line from file, split into various values
    pieces = arcsFile.readline().strip().split(',')
    count = len(pieces)
    if count == 1 : # line is empty (no more data - break from loop)
        break

    src = int(pieces[0])
    dst = int(pieces[1])
    # weight is third piece, not used currently
    if dst in ( orNodes | andNodes ) : #dst is *not* a LEAF-node
        # Reverse edges
        preds[src].add(dst)
        succs[dst].add(src)
      
    if dst in (leafNodes) : # track leaf nodes
        leafSuccs[dst].add(src)
        leafPreds[src].add(dst)
        
arcsFile.close()

# Add branches from root node
for nd in andNodes :
    if not preds[nd] : # if AND-node has no predecessors
        preds[nd].add(root) # add root as predecessor to node
        succs[root].add(nd) # add node as successor to root

# Identify all branch nodes
for n in orNodes : # consider all OR-nodes
    if len( succs[n] ) > 1 : # if more than one successor
        branchNodes.add(n) # mark as branch node
branchNodes.discard(root) # root should not be marked as a branch node


# Print collected data, for verification

#===============================================================================
# 
# print "** Nodes [" + str(len(orNodes) + len(andNodes) + len(leafNodes)) + "] ** "
# for n in orNodes :
#     print n
# for n in andNodes:
#     print str(n) + ", " + str(irv[n])
# for n in leafNodes:
#     print n
# 
# print "** Edges ** "
# for src in succs :
#     print str(src) + " -- ",
#     for dst in succs[src] :
#         print str(dst) + '  ',
#     print
# 
# for k in preds.keys():
#     print 'Predecessors of ' + str(k) + ': ' + str(preds[k])
# 
# for k in leafSuccs.keys():
#     print ' Nodes of this leaf ' + str(k) + ': ' + str(leafSuccs[k])
# 
# for k in leafPreds.keys():
#     print 'Leaves on Node ' + str(k) + ': ' + str(leafPreds[k]) 
#     for p in leafPreds[k] :
#         print 'leaf text ' + str(p) + ': ' + nodeNames[p] 
#===============================================================================


# tmatrix maintains node id by creating a nxn matrix where n 
# is the total number of nodes (ORs, ANDs, and LEAFs) in the MulVal output
# 
# tmatrix places the id of the AND node connecting 2 OR nodes
#  in the slot tmatrix[col][row] = tmatrix[parentORnode][childORnode] <- andNodeID


tmatrix = [[0 for x in range(len(nodeNames))] for x in range(len(nodeNames))]
# print 'trmatrix' + str(len(nodeNames))
for o in orNodes:
    #print str(o) + ' <- '
    for preA in preds[o]:
        print str(preA) + ' <-- '
        for preO in preds[preA]:
            print str(preO)
            # tmatrix[preO][o] = preA
     

# print DataFrame(tmatrix)

myorNodes = getORs()
print 'myorNodes: ', myorNodes
myMHOrs = getMHOrs()
print 'myMHORs: ', myMHOrs
#myorNodes.remove(0) # discard pseudo root


# Get the sink (attacker goal node)
# and add id to tmatrixmap[last slot]
# needs to happen before rm mhr's
mysink = 0
for o in myorNodes:
    print 'finding sink for o in myorNodes, succs[o]', o, myorNodes, succs[o]
    if len(succs[o]) == 0: # we have no subsequent nodes
        mysink = o
        print 'my sink node: ', mysink
#if mysink in myorNodes: myorNodes.remove(mysink)
#if mysink in myMHOrs: myMHOrs.remove(mysink)


orcount = len(myorNodes) - len(myMHOrs)# discount the pseudo root added above
if mysink in myMHOrs: orcount += 1 # add a sink slot if its in MHR
#if 0 in myorNodes: orcount += 1
print 'orcount', orcount

# reducedtmatrix will hold just the OR nodes and transition probabilities
reducedtmatrix = [[0 for x in range(orcount) ] for x in range(orcount) ]
print reducedtmatrix
# tmatrixmap holds the mapping from OR node id to reducedtmatrix index
tmatrixmap = [0 for x in range(orcount) ]
tmatrixmap[orcount - 1] = mysink


print 'myorNodes', str(myorNodes)
print 'tmatrixmap', str(tmatrixmap)



# remove MHRs from myorNodes
for mhor in myMHOrs:
    myorNodes.remove(mhor)


### Map OR nodes into tmatrixmap
print 'MAap OR nodes into tmatrixmap', str(myorNodes)

# Get the root node (attacker start node)
# and add id to tmatrixmap[0]
myroot = 0
print 'myorNodes, myroot', myorNodes, myroot
if myroot in myorNodes: myorNodes.remove(myroot)
if myroot in myMHOrs: myMHOrs.remove(myroot)
print 'myorNodes, myroot', myorNodes, myroot
for o in myorNodes:
    print myorNodes, myroot
    for preA in preds[o]: # set of parent ANDs
        for preO in preds[preA]: # set of parent ORs
            if preO == 0:
                print 'preO ==0, myroot = o', preO, o
                myroot = o
tmatrixmap[0] = myroot
print 'tmatrixmap[0] = myroot', tmatrixmap[0], myroot
print tmatrixmap
print reducedtmatrix
if myroot in myorNodes: myorNodes.remove(myroot)


# add the rest of the nodes to tmatrixmap
nodecount = len(tmatrixmap)
print 'nodecount', nodecount, tmatrixmap, myorNodes
for i in range (1, nodecount-1):
    print str(max(myorNodes))
    tmatrixmap[i]= max(myorNodes)
    myorNodes.remove(max(myorNodes))
    
print str(myorNodes)
print 'Mapping of nodeIDs to matrix indexes: ' + str(tmatrixmap)


# add edges to reducedtmatrix based on
# the new index mapping
myorNodes = getORs()
myorNodes.remove(0) # !! not sure if removing pseudoroot will break anything above
mypreds = preds.copy()
print str(preds)

# coalesce multihop nodes
myMHOrs = getMHOrs()
for mhor in myMHOrs:
    myorNodes.remove(mhor)

rtm_copy = copy.deepcopy(reducedtmatrix)

for o in myorNodes: # this OR node
    for preA in mypreds[o]: # preceeding AND nodes
        print 'preA in mypreds[o]', preA, mypreds[o], o
        for preO in mypreds[preA]: # 1st level parent OR nodes 
            print str(preO)
            theseAnds = mypreds[preO]
            print 'theseAnds = mypreds[preO]', theseAnds, mypreds[preO], preO
            isMH = False
            for a in theseAnds:
                #if 'multi-hop access' in nodeNames[a]:
                if any(rule in nodeNames[a] for rule in coalesced_rules):
                    print 'MH coalesced :' + nodeNames[a]
                    isMH = True
                
                
            if not preO == 0: # if we're not off the root (already removed)
                if not isMH: # if we're not coalescing add this to tmatrix
                    reducedtmatrix[tmatrixmap.index(preO)][tmatrixmap.index(o)] = getnodevulns(preA)
                    rtm_copy[tmatrixmap.index(preO)][tmatrixmap.index(o)] = preA
                else: # we got here from multihop (non exploit) so coalesce
                    for preA2 in mypreds[preO]:
                        print 'preA2 in mypreds[preO]', preA2, mypreds[preO], preO
                        for preO2 in mypreds[preA2]:
                            print 'preO2 in mypreds[preA2]', preO2, mypreds[preA2], preA2
                            if not preO2 == 0: # we're back home
                                reducedtmatrix[tmatrixmap.index(preO2)][tmatrixmap.index(o)] = getnodevulns(preA)
                                rtm_copy[tmatrixmap.index(preO2)][tmatrixmap.index(o)] = preA
                            

print 'Edges between vertices: '
print DataFrame(rtm_copy)
print DataFrame(reducedtmatrix)


# add diagonal entries to reducedtmatrix based on
# the simple avg of incoming AND node values
# ** separated this in case it needs attention later
for o in myorNodes:
    print 'o in myorNodes: ', o, myorNodes
    sumScores = 0 # hold incoming scores here
    for preA in mypreds[o]:
        myscore = is_number(getnodevulns(preA))
        print ' my scores: ' + str(preA) + ' : ' + str(myscore)
        if myscore: # if we get a numeric value add it to the total
            sumScores += myscore
        else: # otherwise ??? adding 1 for now
            print ' couldnt add score ' , preA
            sumScores += 1
    # take simple avg until we get a weighting strategy
    if o in mypreds:
        print ' sum scores for node: [' + str(o) + '] - ' + str(sumScores) + ' (' + str(len(mypreds[o])) + ') '
        print 'my preds[o]', mypreds[o]
        reducedtmatrix[tmatrixmap.index(o)][tmatrixmap.index(o)] = sumScores / len(mypreds[o])

    else:
        print 'o wasnt in my preds: ' , o, mypreds[o]
#print DataFrame(reducedtmatrix)


# normalize the results
# there are builtins from numpy/scikit to do this better
for i in range(0, len(reducedtmatrix)):
    rowsum =  sum(reducedtmatrix[i])
    for j in range(0, len(reducedtmatrix)):
       #print str(reducedtmatrix[i][j]) + ' / ' + str(sum(reducedtmatrix[i]))
       if rowsum == 0: reducedtmatrix[i][j] == 2
       else: reducedtmatrix[i][j] = reducedtmatrix[i][j] / rowsum

#print DataFrame(reducedtmatrix)
print getMHOrs()

writeTmatrix(matrixFileName)

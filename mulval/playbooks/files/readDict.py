#!/usr/bin/python

import yaml
with open('scoreDict.yml') as f:
    # use safe_load instead load
    conf = yaml.safe_load(f)
    scoreDict = conf_override['scoreDict']

#for key, value in scoreDict.iteritems():
for key, value in scoreDict.iteritems():
      print value
ruleText = 'any machine he has an account on will also be compromised'
found = False # warn if we cant match this Rule                                                                                            
for k, v in scoreDict.iteritems():
    print k, v
for k, v in scoreDict.iteritems():
    print '!!!!!!!!!!!!!!!!  ' + k + ' !!!!!!!!!!! '                                                                                       
    if k in ruleText:                                                                                                                      
        score = scoreDict[k]                                                                                                               
        found = True
    if not found:                                                                                                                              
        print '*** Couldnt find rule text (must be added) id: ' + ruleText

#!/usr/bin/python
import os
from dictops import DictOps

dirpath=os.getcwd()
myobj=DictOps(dirpath+'/sveeng.xdxf',dirpath+'/engsve.xdxf',dirpath+'/lp.js\
on',dirpath+'/sve-eng.json',dirpath+'/eng-sve.json',dirpath+'/xdxf.txt',dirpath\
+'/looked-up.txt',dirpath+'/localwords.json',dirpath)

myobj.readStore(myobj.corpusjson)
wordcount=len(myobj.mydict)
print("read in %d words from corpus"%wordcount)

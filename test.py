#!/usr/bin/python
import os
from dictops import DictOps

dirpath=os.getcwd()
myobj=DictOps(dirpath)
myobj.readStore(myobj.corpusjson)
wordcount=len(myobj.mydict)
print("read in %d words from corpus"%wordcount)

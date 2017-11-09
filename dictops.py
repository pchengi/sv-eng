#!/usr/bin/env python
import codecs
import xml.etree.ElementTree as ET
import sys,argparse
from collections import OrderedDict
import simplejson as json
from numbers import Number
import urllib
reload(sys)
sys.setdefaultencoding('utf-8')

#myobj=DictOps('sweeng.xdxf','lp.json','sve-eng.json','xdxf.txt','looked-up.txt')
class DictOps:
	def __init__(self,xdxfinp,lpjson,storejson,txtout,lookupout):
		self.xdxfinp=xdxfinp
		self.storejson=storejson
		self.lpjson=lpjson
		self.txtout=txtout
		self.lookupout=lookupout
		self.mydict=OrderedDict()
		self.lpdict=OrderedDict()

	def updateXdxffile(self):
		xdxffile=urllib.URLopener()
		xdxffile.retrieve('http://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xdxf','sweeng.xdxf')

	def readStore(self):
		try:
			with codecs.open(self.storejson,'r','utf-8') as infile:
				self.mydict=json.load(infile,object_pairs_hook=OrderedDict)
		except:
			print 'no json'
			donothing=1
	
	def listWordstartswith(self,tolist):
		self.readStore()
		found=0
		for word,meanings in self.mydict.iteritems():
			if tolist.startswith(word):
				found=1
				print "Possible related word %s exists in the store"%(word)
				print 'input is %s, word in store is %s'%(tolist,word)
				ctr=1
				for meaning in meanings:
					print "%d. %s"%(ctr,meaning)
					ctr+=1
		if found == 0:
			print "Word %s does not exist in the store"%(tolist)

	def translateWord(self,totrans):
		self.readStore()
		for word, meanings in self.mydict.iteritems():
			for meaning in meanings:
				if totrans == meaning:
					print "Possible match for %s: %s"%(totrans,word)
	
	def listWord(self,tolist):
		self.readStore()
		if self.mydict.__contains__(tolist.decode('utf-8')):
			print "Word %s exists in the store"%(tolist)
			self.recordLookup(tolist,self.mydict[tolist.decode('utf-8')])
			ctr=1
			for meaning in self.mydict[tolist.decode('utf-8')]:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			return(0)
		else:
			#print "Word %s does not exist in the store"%(tolist)
			return(-1)
		
	def removeWord(self,toremove):
		self.readStore()
		if self.mydict.__contains__(toremove.decode('utf-8')):
			print "Word %s exists in the store"%(toremove)
			ctr=1
			for meaning in self.mydict[toremove.decode('utf-8')]:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			resp=raw_input("Press 'R' to remove complete listing, or specify number to delete a specify meaning, any other key to quit.\n")
			if resp == '':
				return
			if resp=='R' or resp=='r':
				print 'you asked to remove the whole listing anyway'
				self.mydict.pop(toremove.decode('utf-8'))
				self.writeStore()
				return
			intresp=int(resp)
			if intresp > 0 and intresp <= len(self.mydict[toremove.decode('utf-8')]):
				popped=self.mydict[toremove.decode('utf-8')].pop(intresp-1)
				print 'Removed %s'%(popped)
			else:
				print 'ignoring'
				return
		else:
			print "Word %s does not exist in the store"%(toremove)
			return
		self.writeStore()

	def readXdxf(self):
		self.readStore()
		try:
			tree=ET.parse(self.xdxfinp)
		except:
			print "Error parsing xdxf input file. Aborting."
			sys.exit(-1)

		self.root=tree.getroot()
		for node in self.root[1]:
			if not self.mydict.__contains__(node[0].text):
				print 'new word found: %s'%(node[0].text)
				self.mydict[node[0].text]=list()
			for ele in node[1]:
				if ele.tag == 'dtrn':
					if not self.mydict[node[0].text].__contains__(ele.text):
						print 'new definition %s found for word %s'%(ele.text,node[0].text)
						self.mydict[node[0].text].append(ele.text)
		self.writeStore()
		self.writeOuttxtfile()

	def recordLookup(self,word,meanings):
		try:
			with codecs.open(self.lpjson,'r','utf-8') as infile:
				self.lpdict=json.load(infile,object_pairs_hook=OrderedDict)
		except:
			#print 'no json'
			donothing=1
		if self.lpdict.__contains__(word.decode('utf-8')):
			return
		self.lpdict[word]=meanings
		with codecs.open(self.lookupout,'w','utf-8') as outfile:
			for word,meanings in self.lpdict.iteritems():
				outfile.write(word)
				outfile.write(':\t')
				ctr=1
				for meaning in meanings:
					outfile.write("%s, "%(meaning))
					ctr+=1
				outfile.write('\n')
		with codecs.open(self.lpjson,'w','utf-8') as outfile:
			json.dump(self.lpdict,outfile)
			
		
	def writeStore(self):
		with codecs.open(self.storejson,'w','utf-8') as outfile:
			json.dump(self.mydict,outfile)
				
	def writeOuttxtfile(self):
		self.readStore()
		with codecs.open(self.txtout,'w','utf-8') as outfile:
			for key, val in self.mydict.iteritems():
				outfile.write(key)
				outfile.write('\n')
				dtrncount=1
				for meaning in val:
					outfile.write("\t %d. %s\n"%(dtrncount,meaning))
					dtrncount+=1

	def addWord(self,toadd):
		self.readStore()
		if self.mydict.__contains__(toadd.decode('utf-8')):
			print "Word %s already exists in the store"%(toadd)
			ctr=1
			for meaning in self.mydict[toadd.decode('utf-8')]:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			resp=raw_input('Do you wish to add a new meaning(N/y)\n')
			if resp=='y' or resp=='Y':
				newm=raw_input('Enter new meaning\n')
				self.mydict[toadd.decode('utf-8')].append(newm)
			else:
				return
		else:
			print "Word %s does not exist in the store"%(toadd)
			self.mydict[toadd.decode('utf-8')]=list()
			resp='y'
			while resp == 'y':
				newm=raw_input('Enter the meaning for this word\n')
				self.mydict[toadd.decode('utf-8')].append(newm)
				resp=raw_input('Do you wish to add another meaning(N/y)\n')
		self.writeStore()

myobj=DictOps('sweeng.xdxf','lp.json','sve-eng.json','xdxf.txt','looked-up.txt')
aparser=argparse.ArgumentParser()
aparser.add_argument('-r', type=str,default='none') #remove
aparser.add_argument('-m', type=str,nargs='?',default='none') #my inputs
aparser.add_argument('-x', type=str,nargs='?',default='none') #read xml and write-out txt
aparser.add_argument('-t', type=str,default='none') #translate word
aparser.add_argument('-a', type=str,default='none') #lookup and add a new word if not found
aparser.add_argument('-l', type=str,default='none') #list word meanings if found
aparser.add_argument('-e', type=str,default='none') #list word meanings if found
aparser.add_argument('-u', type=str,nargs='?',default='none') #update file
args=aparser.parse_args()
removeword=args.r
manualinp=args.m
xmlread=args.x
translateword=args.t
addword=args.a
listword=args.l
exactword=args.e
update=args.u

if update != 'none':
	myobj.updateXdxffile()

if translateword != 'none':
	myobj.translateWord(translateword)

if xmlread != 'none':
	myobj.readXdxf()

if addword != 'none':
	myobj.addWord(addword)

if removeword != 'none':
	myobj.removeWord(removeword)

if listword != 'none':
	ret=myobj.listWord(listword)
	if ret != 0:
		myobj.listWordstartswith(listword)

if exactword != 'none':
	myobj.listWord(exactword)

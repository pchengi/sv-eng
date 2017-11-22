#!/usr/bin/env python2
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
	def __init__(self,xdxfinp,lpjson,corpusjson,txtout,lookupout):
		self.xdxfinp=xdxfinp
		self.corpusjson=corpusjson
		self.lpjson=lpjson
		self.txtout=txtout
		self.lookupout=lookupout
		self.mydict=OrderedDict()
		self.lpdict=OrderedDict()

	def setupRef(self,refdict):
		refdict['source']='local'
		refdict['tense']='unspecified'
		refdict['figureofspeech']='unspecified'
		refdict['additionalattribute']='unspecified'
		refdict['definitions']=list()
		return refdict

	def updateXdxffile(self):
		xdxffile=urllib.URLopener()
		try:
			xdxffile.retrieve('http://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xdxf','sweeng.xdxf')
			print 'Successfully updated the XDXF word definitions file'
		except:
			print 'Unable to fetch XDXF file. Are you connected to the internet?'
			sys.exit(-1)

	def readStore(self):
		try:
			with codecs.open(self.corpusjson,'r','utf-8') as infile:
				self.mydict=json.load(infile,object_pairs_hook=OrderedDict)
		except:
			print 'Corpus json file sve-eng.json not found. Initializing corpus from XDXF file'
			self.readXdxf(dontread=1)
	
	def listWordstartswith(self,tolist):
		self.readStore()
		found=0
		for word,refobj in self.mydict.iteritems():
			if tolist.startswith(word):
				found=1
				print "Possible related word %s exists in the corpus"%(word)
				print 'input is %s, word in corpus is %s'%(tolist,word)
				ctr=1
				for meaning in refobj['definitions']:
					print "%d. %s"%(ctr,meaning)
					ctr+=1
		if found == 0:
			print "Word %s does not exist in the corpus"%(tolist)

	def translateWord(self,totrans):
		self.readStore()
		for word,refobj in self.mydict.iteritems():
			for meaning in refobj['definitions']:
				if totrans == meaning:
					print "Possible match for %s: %s"%(totrans,word)
	
	def listWord(self,tolist):
		self.readStore()
		if self.mydict.__contains__(tolist.decode('utf-8')):
			print "Word %s exists in the corpus"%(tolist)
			self.recordLookup(tolist,self.mydict[tolist.decode('utf-8')]['definitions'])
			ctr=1
			for meaning in self.mydict[tolist.decode('utf-8')]['definitions']:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			return(0)
		else:
			return(-1)
		
	def removeWord(self,toremove):
		self.readStore()
		decoded=toremove.decode('utf-8')
		if self.mydict.__contains__(decoded):
			print "Word %s exists in the corpus"%(decoded)
			ctr=1
			for meaning in self.mydict[decoded]['definitions']:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			resp=raw_input("Press 'R' to remove complete listing, or specify number to delete a specify meaning, any other key to quit.\n")
			if resp == '':
				return
			if resp=='R' or resp=='r':
				print 'Removing the listing entirely for %s.'%decoded
				self.mydict.pop(decoded)
				self.writeStore()
				return
			intresp=int(resp)
			if intresp > 0 and intresp <= len(self.mydict[decoded]['definitions']):
				popped=self.mydict[decoded]['definitions'].pop(intresp-1)
				print 'Removed %s.'%(popped)
			else:
				print 'Ignoring.'
				return
			if len(self.mydict[decoded]['definitions']) == 0:
				self.mydict.pop(decoded)
				print 'Removed %s as it had no remaining definitions.'%(decoded)
		else:
			print "Word %s does not exist in the corpus."%(decoded)
			return
		self.writeStore()

	def readXdxf(self,dontread=0):
		if dontread == 0:
			self.readStore()
		try:
			tree=ET.parse(self.xdxfinp)
		except:
			print "Error parsing xdxf input file. Aborting."
			sys.exit(-1)

		self.root=tree.getroot()
		for node in self.root[1]:
			self.mydict[node[0].text]['source']='lexikon'
			if not self.mydict.__contains__(node[0].text):
				print 'new word found: %s'%(node[0].text)
				refdict=OrderedDict()
				self.mydict[node[0].text]=self.setupRef(refdict)
			for ele in node[1]:
				if ele.tag == 'dtrn':
					if not self.mydict[node[0].text]['definitions'].__contains__(ele.text):
						print 'new definition %s found for word %s'%(ele.text,node[0].text)
						self.mydict[node[0].text]['definitions'].append(ele.text)
		try:
			self.writeStore()
			self.writeOuttxtfile()
			print 'Successfully wrote out de-duped word corpus and xdxf.txt file'
		except:
			print 'Could not write out word corpus or/and xdxf.txt file'

	def recordLookup(self,word,meanings):
		try:
			with codecs.open(self.lpjson,'r','utf-8') as infile:
				self.lpdict=json.load(infile,object_pairs_hook=OrderedDict)
		except:
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
		with codecs.open(self.corpusjson,'w','utf-8') as outfile:
			json.dump(self.mydict,outfile)
				
	def writeOuttxtfile(self):
		self.readStore()
		with codecs.open(self.txtout,'w','utf-8') as outfile:
			for key, refdict in self.mydict.iteritems():
				outfile.write(key)
				outfile.write('\n')
				dtrncount=1
				for meaning in refdict['definitions']:
					outfile.write("\t %d. %s\n"%(dtrncount,meaning))
					dtrncount+=1

	def addWord(self,toadd):
		self.readStore()
		if self.mydict.__contains__(toadd.decode('utf-8')):
			print "Word %s already exists in the corpus"%(toadd)
			ctr=1
			for meaning in self.mydict[toadd.decode('utf-8')]['definitions']:
				print "%d. %s"%(ctr,meaning)
				ctr+=1
			resp=raw_input('Do you wish to add a new meaning(N/y)\n')
			if resp=='y' or resp=='Y':
				newm=raw_input('Enter new meaning\n')
				self.mydict[toadd.decode('utf-8')]['definitions'].append(newm)
			else:
				return
		else:
			print "Word %s does not exist in the corpus"%(toadd)
			refdict=OrderedDict()
			self.mydict[toadd.decode('utf-8')]=self.setupRef(refdict)
			resp='y'
			while resp == 'y':
				newm=raw_input('Enter the meaning for this word\n')
				self.mydict[toadd.decode('utf-8')]['definitions'].append(newm)
				resp=raw_input('Do you wish to add another meaning(N/y)\n')
		self.writeStore()

	def listLocalwords(self):
		self.readStore()
		for key,val in self.mydict.iteritems():
			if val['source'] == 'local':
				print "Word %s is present only locally"%(key) 

myobj=DictOps('sweeng.xdxf','lp.json','sve-eng.json','xdxf.txt','looked-up.txt')
aparser=argparse.ArgumentParser(description='A tool to setup a Swedish-English dictionary and English-Swedish word translator, seeded with words from the Folkets Lexikon, provided by KTH. You can perform offline dictionary lookups (Swedish to English), translations (English to Swedish), and even add (or delete) additional words into the corpus.')
aparser.add_argument('-r', type=str,default='none',help='remove the specified word from the word corpus.') #remove
aparser.add_argument('-x', type=str,nargs='?',default='none',help='reread XDXF file and write out a new text-listing.') #read xml and write-out txt
aparser.add_argument('-t', type=str,default='none',help='translate from English to Swedish.') #translate word
aparser.add_argument('-a', type=str,default='none',help='attempt lookup and if not found, manually add to the word corpus, if it was not present already.') #lookup and add a new word if not found
aparser.add_argument('-l', type=str,default='none',help='lookup word and return even words that are a partial match. e.g looking up stenar will even return sten as a potential match. Exact matches if found are also logged to looked-up.txt, for easy reference/history') #list word meanings if found
aparser.add_argument('-e', type=str,default='none',help='lookup word and only return a result if a perfect match was found.') #list word meanings if found
aparser.add_argument('-u', type=str,nargs='?',default='none',help='update the XDXF file, from KTH. Requires a working internet connection.') #update file
aparser.add_argument('-c', type=str,nargs='?',default='none',help='list words you have added locally, that can be potentially contributed the to Lexikon project.') #update file
args=aparser.parse_args()
removeword=args.r
xmlread=args.x
translateword=args.t
addword=args.a
listword=args.l
exactword=args.e
update=args.u
contribute=args.c

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

if contribute != 'none':
	myobj.listLocalwords()

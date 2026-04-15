#!/usr/bin/env python
import codecs
import readline
import xml.etree.ElementTree as ET
import sys,argparse
from collections import OrderedDict
from hashlib import sha256
import json
from numbers import Number
import os
import urllib.request, urllib.parse, urllib.error

class DictOps:
    def __init__(self,svexdxfinp,engxdxfinp,lpjson,corpusjson,engjson,txtout,lookupout,localjson,dirpath):
        self.dirpath=dirpath
        self.svexdxfinp=svexdxfinp
        self.engxdxfinp=engxdxfinp
        self.localjson=localjson
        self.corpusjson=corpusjson
        self.engjson=engjson
        self.lpjson=lpjson
        self.txtout=txtout
        self.lookupout=lookupout
        self.mydict=OrderedDict()
        self.engdict=OrderedDict()
        self.localdict=OrderedDict()
        self.lpdict=OrderedDict()
        self.deffiles=[]
        self.deffiles.append(dirpath+'/engsve.xdxf')
        self.deffiles.append(dirpath+'/sveeng.xdxf')
        self.checksumfile=dirpath+'/sha256sums'

    def setupRef(self,refdict):
        refdict['source']='local'
        refdict['tense']='unspecified'
        refdict['figureofspeech']='unspecified'
        refdict['additionalattribute']='unspecified'
        refdict['definitions']=list()
        refdict['synonyms']=list()
        return refdict

    def updateXdxffile(self):
        try:
            sveengfile=dirpath
            engsvefile=dirpath
            engsvefile+="/engsve.xdxf"
            sveengfile+="/sveeng.xdxf"
            urllib.request.urlretrieve('http://folkets-lexikon.csc.kth.se/folkets/folkets_sv_en_public.xdxf',sveengfile)
            urllib.request.urlretrieve('http://folkets-lexikon.csc.kth.se/folkets/folkets_en_sv_public.xdxf',engsvefile)
            print('Successfully updated the XDXF word definitions file')
        except:
            print('Unable to fetch XDXF file. Are you connected to the internet?')
            sys.exit(-1)

        cksums=OrderedDict()
        try:
            with open(self.checksumfile,'r') as infile:
                lines=infile.readlines()
            for line in lines:
                cksums[line.split(' ')[1].split('\n')[0]]=line.split(' ')[0]
            changed=0
            for file in cksums:
                with open(file,'rb') as infile:
                    sha256sum=sha256(infile.read()).hexdigest()
                if cksums[file] != sha256sum:
                    print("File %s has changed!"%(file))
                    cksums[file]=sha256sum
                    changed=1
            if changed == 0:
                print("No changes found in the XDXF files")
            else:
                with open(self.checksumfile,'w') as outfile:
                    for file in cksums:
                        outfile.write("%s %s\n"%(cksums[file],file))
                self.readXdxf()
        except:
            print("Could not look up old checksums. Generating a new file")
            for filename in self.deffiles:
                with open(filename,'rb') as infile:
                    sha256sum=sha256(infile.read()).hexdigest()
                cksums[filename]=sha256sum
            with open(self.checksumfile,'w') as outfile:
                for filename in cksums:
                    outfile.write("%s %s\n"%(cksums[filename],filename))

    def readStore(self, jsonfile):
        try:
            with open(jsonfile,'r') as infile:
                if jsonfile == self.dirpath+'/sve-eng.json':
                    self.mydict=json.load(infile,object_pairs_hook=OrderedDict)
                elif jsonfile == self.dirpath+'/localwords.json':
                    self.localdict=json.load(infile,object_pairs_hook=OrderedDict)
                else:
                    self.engdict=json.load(infile,object_pairs_hook=OrderedDict)
        except:
            print('json file %s not found. Initializing from XDXF file'%(jsonfile))
            self.readXdxf(dontread=1)
    
    def listWordstartswith(self,tolist):
        self.readStore(self.corpusjson)
        found=0
        for word,refobj in self.mydict.items():
            if tolist.startswith(word):
                found=1
                print("Possible related word %s exists in the corpus"%(word))
                print('input is %s, word in corpus is %s'%(tolist,word))
                ctr=1
                for meaning in refobj['definitions']:
                    print("%d. %s"%(ctr,meaning))
                    ctr+=1
        if found == 0:
            print("Word %s does not exist in the corpus"%(tolist))

    def translateWord(self,totrans,silent):
        if self.engdict.__contains__(totrans):
            if silent:
                return(0)
            print("Word %s exists in the English to Swedish corpus"%(totrans))
            self.recordLookup(totrans,self.engdict[totrans]['definitions'])
            ctr=1
            for meaning in self.engdict[totrans]['definitions']:
                print("%d. %s"%(ctr,meaning))
                ctr+=1
            return(0)
        else:
            if silent:
                return(-1)
            for word,refobj in self.mydict.items():
                for meaning in refobj['definitions']:
                    if totrans == meaning:
                        print("Possible match for %s: %s"%(totrans,word))
            return(0)
    
    def listWord(self,tolist,silent,recurse):
        if self.mydict.__contains__(tolist):
            if silent:
                return(0)
            print("Word %s exists in the corpus"%(tolist))
            self.recordLookup(tolist,self.mydict[tolist]['definitions'])
            ctr=1
            if len(self.mydict[tolist]['definitions']) > 0:
                for meaning in self.mydict[tolist]['definitions']:
                    print("%d. %s"%(ctr,meaning))
                    ctr+=1
                if len(self.mydict[tolist]['synonyms']) > 0:
                    print("Synonyms: ")
                syns=''
                for syn in self.mydict[tolist]['synonyms']:
                    syns+="%s,"%syn
                print(syns.rstrip(','),end='')
                print()
                return(0)
            elif len(self.mydict[tolist]['synonyms']) > 0:
                for syn in self.mydict[tolist]['synonyms']:
                    print("Synonym found: %s"%syn)
                    ctr=1
                return(0)
        else:
            #if silent:
            return(-1)
            for key,val in self.mydict.items():
                if len(val['synonyms'])>0:
                    if tolist in val['synonyms']:
                        if silent:
                            return(0)
                        print("Synonym of %s."%key)
                    if recurse == 1:
                        self.listWord(term,silent,recurse=0)
                        return(0)
            return(-1)
        
    def removeWord(self,toremove,silent):
        if self.mydict.__contains__(toremove):
            if silent:
                self.mydict.pop(toremove)
                return
            print("Word %s exists in the corpus"%(toremove))
            ctr=1
            for meaning in self.mydict[toremove]['definitions']:
                print("%d. %s"%(ctr,meaning))
                ctr+=1
            resp=input("Press 'R' to remove complete listing, or specify number to delete a specify meaning, any other key to quit.\n")
            if resp == '':
                return
            if resp=='R' or resp=='r':
                print('Removing the listing entirely for %s.'%toremove)
                self.mydict.pop(toremove)
                return
            intresp=int(resp)
            if intresp > 0 and intresp <= len(self.mydict[toremove]['definitions']):
                popped=self.mydict[toremove]['definitions'].pop(intresp-1)
                print('Removed %s.'%(popped))
            else:
                print('Ignoring.')
                return
            if len(self.mydict[toremove]['definitions']) == 0:
                self.mydict.pop(toremove)
                print('Removed %s as it had no remaining definitions.'%(toremove))
        else:
            print("Word %s does not exist in the corpus."%(toremove))
            return

    def readXdxf(self, dontread=0):
        if dontread == 0:
            self.readStore(self.corpusjson)
            self.readStore(self.engjson)
        try:
            print("Reading source xml files")
            tree=ET.parse(self.svexdxfinp)
            engtree=ET.parse(self.engxdxfinp)
            
        except:
            print("Error parsing xdxf input file. Aborting.")
            sys.exit(-1)

        self.root=tree.getroot()
        self.engroot=engtree.getroot()

        for node in self.root[1]:
            if not self.mydict.__contains__(node[0].text):
                print('new word found: %s'%(node[0].text))
                refdict=OrderedDict()
                self.mydict[node[0].text]=self.setupRef(refdict)
                self.mydict[node[0].text]['source']='lexikon'
            else:
                self.mydict[node[0].text]['source']='lexikon'
            for ele in node[1]:
                if ele.tag == 'dtrn':
                    if not self.mydict[node[0].text]['definitions'].__contains__(ele.text):
                        print('new definition %s found for word %s'%(ele.text,node[0].text))
                        self.mydict[node[0].text]['definitions'].append(ele.text)
                if ele.tag == 'sr':
                    for syn in ele:
                        if syn.tag == 'kref':
                            if not self.mydict[node[0].text]['synonyms'].__contains__(syn.text):
                                print('new synonym for %s:  %s'%(node[0].text,syn.text))
                                self.mydict[node[0].text]['synonyms'].append(syn.text)

        for node in self.engroot[1]:
            if not self.engdict.__contains__(node[0].text):
                print('new word found: %s'%(node[0].text))
                refdict=OrderedDict()
                self.engdict[node[0].text]=self.setupRef(refdict)
                self.engdict[node[0].text]['source']='lexikon'
            else:
                self.engdict[node[0].text]['source']='lexikon'
            
            for ele in node[1]:
                if ele.tag == 'dtrn':
                    if not self.engdict[node[0].text]['definitions'].__contains__(ele.text):
                        print('new definition %s found for word %s'%(ele.text,node[0].text))
                        self.engdict[node[0].text]['definitions'].append(ele.text)
                if ele.tag == 'sr':
                    for syn in ele:
                        if syn.tag == 'kref':
                            if not self.engdict[node[0].text]['synonyms'].__contains__(syn.text):
                                print('new synonym for %s:  %s'%(node[0].text,syn.text))
                                self.engdict[node[0].text]['synonyms'].append(syn.text)
        try:
            self.writeStore(self.corpusjson)
            self.writeStore(self.engjson)
            self.writeOuttxtfile()
            print('Successfully wrote out de-duped word corpus and xdxf.txt file')
        except:
            print('Could not write out word corpus or/and xdxf.txt file')

    def recordLookup(self,word,meanings):
        try:
            with open(self.lpjson,'r') as infile:
                self.lpdict=json.load(infile,object_pairs_hook=OrderedDict)
        except:
            donothing=1
        if self.lpdict.__contains__(word):
            return
        self.lpdict[word]=meanings
        with open(self.lookupout,'w') as outfile:
            for word,meanings in self.lpdict.items():
                outfile.write(word)
                outfile.write(':\t')
                ctr=1
                for meaning in meanings:
                    outfile.write("%s, "%(meaning))
                    ctr+=1
                outfile.write('\n')
        with open(self.lpjson,'w') as outfile:
            json.dump(self.lpdict,outfile)
            
        
    def writeStore(self,jsonfile):
        print('jsonfile:%s'%jsonfile)
        with open(jsonfile,'w') as outfile:
            if jsonfile.endswith("sve-eng.json"):
                print("writing into sve-eng")
                json.dump(self.mydict,outfile)
            elif jsonfile.endswith("localwords.json"):
                print("writing into localwords")
                json.dump(self.localdict,outfile)
            else:
                print("writing into eng-sve")
                json.dump(self.engdict,outfile)
                
    def writeOuttxtfile(self):
        self.readStore(self.corpusjson)
        with open(self.txtout,'w') as outfile:
            for key, refdict in self.mydict.items():
                outfile.write(key)
                outfile.write('\n')
                dtrncount=1
                for meaning in refdict['definitions']:
                    outfile.write("\t %d. %s\n"%(dtrncount,meaning))
                    dtrncount+=1

    def addWord(self,toadd,meaning=None,noninteractive=False,source=None):
        if self.mydict.__contains__(toadd):
            print("Word %s already exists in the corpus"%(toadd))
            if noninteractive:
                return
            ctr=1
            for meaning in self.mydict[toadd]['definitions']:
                print("%d. %s"%(ctr,meaning))
                ctr+=1
            resp=input('Do you wish to add a new meaning(N/y)\n')
            if resp=='y' or resp=='Y':
                newm=input('Enter new meaning\n')
                self.mydict[toadd]['definitions'].append(newm)
            else:
                return
        else:
            refdict=OrderedDict()
            self.mydict[toadd]=self.setupRef(refdict)
            if source is not None:
                self.mydict[toadd]['source'] = source
            if noninteractive:
                self.mydict[toadd]['definitions'].append(meaning)
                return
            print("Word %s does not exist in the corpus"%(toadd))
            resp='y'
            while resp == 'y':
                newm=input('Enter the meaning for this word\n')
                self.mydict[toadd]['definitions'].append(newm)
                resp=input('Do you wish to add another meaning(N/y)\n')
            resp='y'
            while resp == 'y':
                resp=input("Do you wish to add a synonym to %s? (N/y)\n"%(toadd))
                if resp == 'y':
                    newsyn=input("Enter synonym for %s\n"%(toadd))
                    self.mydict[toadd]['synonyms'].append(newsyn)
            print(resp)

    def chainfeeder(self,listorfile):
        if type(listorfile) == list:
            with open(listorfile[0]) as inp:
                lines=inp.readlines()
            for line in lines:
                word=line.split('\n')[0].lower()
                yield word
        else:
            words=listorfile.split(',')
            for word in words:
                yield word
 
    def listLocalwords(self,showres=False):
        self.readStore(self.corpusjson)
        for key,val in self.mydict.items():
            if val['source'] == 'local':
                self.localdict[key]=val
                if showres:
                    print("Word %s is present only locally"%(key))

dirpath = os.path.dirname(os.path.realpath(__file__))
myobj=DictOps(dirpath+'/sveeng.xdxf',dirpath+'/engsve.xdxf',dirpath+'/lp.json',dirpath+'/sve-eng.json',dirpath+'/eng-sve.json',dirpath+'/xdxf.txt',dirpath+'/looked-up.txt',dirpath+'/localwords.json',dirpath)
aparser=argparse.ArgumentParser(description='A tool to setup a Swedish-English dictionary and English-Swedish word translator, seeded with words from the Folkets Lexikon, provided by KTH. You can perform offline dictionary lookups (Swedish to English), translations (English to Swedish), and even add (or delete) additional words into the corpus.')
aparser.add_argument('-r', type=str,default='none',help='remove the specified word from the word corpus.') #remove
aparser.add_argument('-x', type=str,nargs='?',default='none',help='reread XDXF file and write out a new text-listing.') #read xml and write-out txt
aparser.add_argument('-t', default=False,nargs='?',help='translate from English to Swedish.') #translate word
aparser.add_argument('-a', default=False,nargs='?',help='attempt lookup and if not found, manually add to the word corpus, if it was not present already. --input-file can be used for non-interactive additions') #lookup and add a new word if not found
aparser.add_argument('-l', type=str,default='none',help='lookup word and return even words that are a partial match. e.g looking up stenar will even return sten as a potential match. Exact matches if found are also logged to looked-up.txt, for easy reference/history') #list word meanings if found
aparser.add_argument('-e', '--exact-word', default=False, nargs='?',help='lookup word and only return a result if a perfect match was found.') #list word meanings if found
aparser.add_argument("-u", "--update",type=str,nargs='?',default='none',help='update the XDXF file, from KTH. Requires a working internet connection.') #update file
aparser.add_argument('-c', type=str,nargs='?',default='none',help='list words you have added locally, that can be potentially contributed the to Lexikon project.') #update file
aparser.add_argument('-s', '--silent', default=False,action='store_true')
aparser.add_argument('--backup-local', action='store_true')
aparser.add_argument('--restore-local', action='store_true')
aparser.add_argument('-b','--bulk-lookup', nargs='?', default=False)
aparser.add_argument('-i','--input-file', nargs=1, default=False)
aparser.add_argument('--invert-match', action='store_true',default=False)
aparser.add_argument('--source',default=None,nargs='?')
args=aparser.parse_args()
removeword=args.r
xmlread=args.x
translateword=args.t
addword=args.a
listword=args.l
exactword=args.exact_word
update=args.update
contribute=args.c
backuplocalwords=args.backup_local
restorelocalwords=args.restore_local
silent=args.silent
inputfile=args.input_file
bulklookup=args.bulk_lookup
invertmatch=args.invert_match
sourceval=args.source
if invertmatch:
    if not silent:
        print("--invert-match requires the usage of the --silent flag.")
        sys.exit(-1)
if bulklookup is not False:
    if bulklookup == None:
        if inputfile is False:
            print("--bulk-lookup option requires either a comma-separated list of words to lookup, or an input file, with a single word on each line, specified with the --input-file option.")
            sys.exit(-1)
        bulklookup=inputfile
        
if update != 'none':
    myobj.updateXdxffile()
    sys.exit(0)

if xmlread != 'none':
    myobj.readXdxf()
    sys.exit(0)

if addword is not False:
    myobj.readStore(myobj.corpusjson)
    if addword is None:
        if inputfile is False:
            print("-a requires a word to be specified as argument, or the --input-file option used to specify an input-file with words and meanings, for non-interactive additions.")
            sys.exit(-1)
        try:
            with open (inputfile[0],'r') as inp:
                lines=inp.readlines()
        except(FileNotFoundError):
            print("File not found: %s"%inputfile[0])
            sys.exit(-1)
        for line in lines:
            cleanedline=line.split('\n')[0]
            word,meaning=cleanedline.split(':')
            if meaning == '':
                meaning = 'placeholder_text'
            myobj.addWord(word,meaning,True,sourceval)
        myobj.writeStore(myobj.corpusjson)
        sys.exit(0)
    myobj.addWord(addword,False,sourceval)
    myobj.writeStore(myobj.corpusjson)
    sys.exit(0)

if removeword != 'none':
    myobj.readStore(myobj.corpusjson)
    myobj.removeWord(removeword,silent)
    myobj.writeStore(myobj.corpusjson)
    sys.exit(0)

if listword != 'none':
    ret=myobj.listWord(listword,silent,recurse=1)
    if ret != 0:
        myobj.listWordstartswith(listword)
    sys.exit(0)

if exactword is not False:
    if exactword is None:
        if bulklookup is False:
            print("--exact-word requires a word to be looked up, or the usage of the --bulk-lookup flag, indicating multi-word lookup.")
            sys.exit(-1)
        myobj.readStore(myobj.corpusjson)
        for lookup in myobj.chainfeeder(bulklookup):
            ret=myobj.listWord(lookup,silent,recurse=0)
            if ret == 0 and invertmatch is False:
                if silent:
                    print("%s"%lookup)
            if ret ==  -1 and invertmatch:
                if silent:
                    print("%s"%lookup)
        sys.exit(0)
    if not silent:
        print("regular single lookup of word %s"%exactword)
    myobj.readStore(myobj.corpusjson)
    ret=myobj.listWord(exactword,silent,recurse=0)
    if ret == 0 and invertmatch is False:
        if silent:
            print("%s"%exactword)
            sys.exit(ret)
        sys.exit(ret)
    if ret ==  -1 and invertmatch:
        if silent:
            print("%s"%exactword)
    sys.exit(ret)

if translateword is not False:
    if translateword is None:
        if bulklookup is False:
            print("-t requires a word to be looked up, or the usage of the --bulk-lookup flag, indicating multi-word lookup.")
            sys.exit(-1)
        myobj.readStore(myobj.engjson)
        myobj.readStore(myobj.corpusjson)
        for lookup in myobj.chainfeeder(bulklookup):
            ret=myobj.translateWord(lookup,silent)
            if ret == 0 and invertmatch is False:
                if silent:
                    print("%s"%lookup)
            if ret ==  -1 and invertmatch:
                if silent:
                    print("%s"%lookup)
        sys.exit(0)
    if not silent:
        print("regular single translation of word %s"%translateword)
    myobj.readStore(myobj.engjson)
    myobj.readStore(myobj.corpusjson)
    ret=myobj.translateWord(translateword,silent)
    if ret == 0 and invertmatch is False:
        if silent:
            print("%s"%translateword)
            sys.exit(ret)
        sys.exit(ret)
    if ret ==  -1 and invertmatch:
        if silent:
            print("%s"%translateword)
    sys.exit(ret)

if contribute != 'none':
    myobj.listLocalwords(True)
    sys.exit(0)
if backuplocalwords:
    myobj.listLocalwords()
    myobj.writeStore(myobj.localjson)
    sys.exit(0)
if restorelocalwords:
    myobj.readStore(myobj.corpusjson)
    myobj.readStore(myobj.localjson)
    for key,val in myobj.localdict.items():
        myobj.removeWord(key,True)
        myobj.mydict[key]=val
    myobj.writeStore(myobj.corpusjson)
    sys.exit(0)

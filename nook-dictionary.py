# -*- coding: utf-8 -*-

# by Jiri Orsag, 2014
# https://github.com/geoRG77/nook-dictionary
# Many thanks to Homeless Ghost for his script 'createRenateNSTdictionaryfromnookdictionarydb.py'
# which was a great source of ideas for my work

import sqlite3, sys, zipfile, zlib, os

# config
DICTIONATY_FILE = 'xdxf.txt' # input file (needed)
OUTPUT_DB = 'test.db' # output file
TEMP_DIRECTORY = './temp/' # will be deleted after successful run
STEP = 10000 # for print message

########################################################

def wordType(s):
  if s == 'n:': return 'n: podstatné jméno'
  elif s == 'v:': return 'v: sloveso'
  elif s == 'adj:': return 'adj: přídavné jméno'
  elif s == 'adv:': return 'adv: příslovce'
  elif s == 'prep:': return 'prep: předložka'
  elif s == 'conj:': return 'conj: spojka'
  elif s == 'interj:': return 'interj: citoslovce'
  elif s == 'num:': return 'num: číslovka'
  else: return s

print 'Converting dictionary...'

con = sqlite3.connect(OUTPUT_DB)
con.text_factory = str
cur = con.cursor()

index = 0
duplicateCount = 1
prevTerm = ''

try:
  if not os.path.exists(TEMP_DIRECTORY):
    os.makedirs(TEMP_DIRECTORY)

  # open dict file
  dict = open(DICTIONATY_FILE, 'r')

  # delete previous tables
  cur.execute('DROP TABLE IF EXISTS android_metadata')
  cur.execute('DROP TABLE IF EXISTS tblWords')

  # create tables
  cur.execute('CREATE TABLE "android_metadata"("locale" TEXT)')
  cur.execute('CREATE TABLE "tblWords"(_id INTEGER PRIMARY KEY AUTOINCREMENT, "term" TEXT, "description" BLOB)')

  # convert dict to sql
  for line in dict:
    if not line.startswith('\t'):
        index += 1
        term=line.split('\n')[0]
        # create HTML
        html = '<div class="entry"><b><span class="searchterm-headword">' + term + '</span></b><br/>'
        continue

    # split line
    data = line.split('\t')

    for j in range(len(data)):
      if data[j] != '':
          html += data[j].strip() + '<br/>'
    html=html.replace('</div>','')
    html += '</div>'

    # check for duplicates
    if term == prevTerm:
      duplicateCount += 1
      termEdited = term + '[' + str(duplicateCount) + ']'
    else:
      termEdited = term
      duplicateCount = 1

    # create html file
    term_stripped = termEdited.replace('/', '')
    temp_html = open(TEMP_DIRECTORY + term_stripped, 'wb')
    temp_html.write(html)
    #print html
    temp_html.close()

    # compress & save
    zf = zipfile.ZipFile('_temp', mode='w')
    zf.write(TEMP_DIRECTORY + term_stripped)
    zf.close()

    # read & insert compressed data
    temp_compressed = open('_temp', 'rb')
    compressed = temp_compressed.read()
    compvar=sqlite3.Binary(compressed)
    try:
        #print index,termEdited
        
        cur.execute('INSERT INTO tblWords (_id, term, description) VALUES(?, ?, ?)', (index, termEdited, sqlite3.Binary(compressed)))
    except:
        #print 'postfail'
        #print index,termEdited
        #print duplicateCount
        #raise
        # if duplicate then update previous row with [1]
        if duplicateCount !=1:
          cur.execute("UPDATE tblWords SET description= ?  WHERE _id= ?", (compvar,str(index )))


    os.remove(TEMP_DIRECTORY + term_stripped)
    prevTerm = term

    # print _id, term, description
    if ((index % STEP) == 0):
      print '# current line = %d' % index

    #if index == 100:
    #  break;

  # create term_index
  cur.execute('CREATE INDEX term_index on tblWords (term ASC)')
  cur.execute('SELECT * FROM tblWords order by _id LIMIT 10')

  dict.close
  os.remove('_temp')
  os.rmdir(TEMP_DIRECTORY)

except Exception, e:
  raise
else:
  pass
finally:
  pass

print 'Done. ' + str(index) + ' lines converted.'

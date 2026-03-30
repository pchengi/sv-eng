Requirements:
lxml

usage: dictops.py [-h] [-r R] [-x [X]] [-t T] [-a A] [-l L] [-e E] [-u [U]]

A tool to setup a Swedish-English dictionary and English-Swedish word
translator, seeded with words from the Folkets Lexikon, provided by KTH. You
can perform offline dictionary lookups (Swedish to English), translations
(English to Swedish), and even add (or delete) additional words into the
corpus.

optional arguments:
  -h, --help  show this help message and exit
  -r R        remove the specified word from the word corpus.
  -x [X]      reread XDXF file and write out a new text-listing.
  -t T        translate from English to Swedish.
  -a A        attempt lookup and if not found, manually add to the word
              corpus, if it was not present already.
  -l L        lookup word and return even words that are a partial match. e.g
              looking up stenar will even return sten as a potential match.
              Exact matches if found are also logged to looked-up.txt, for
              easy reference/history
  -e E        lookup word and only return a result if a perfect match was
              found.
  -u [U]      update the XDXF file, from KTH. Requires a working internet
              connection.


## Update definitions

- Execute dictops.py -u to update the XDXF files from KTH.

## Description of files used

- sveeng.xdxf: Swedish to English listing, curated by KTH under the lexin programme.
- engsve.xdxf: English to Swedish listing, curated by KTH under the lexin programme.
- lp.json: Stores words previously looked up, using dictops.
- looked-up.txt: Human-readable version of previously looked up words.
- sve-eng.json aka corpus: JSON store of Swedish word definitions, mainly comprised of words from lexikon, but also includes locally added words.
- eng-sve.json:

## Usage

- First thing to do is to download the XDXF files, which is done by dictops.py -u; this also sets up the checksum file.

- Write out the JSON files, by invoking dictops.py -x.

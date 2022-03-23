import argparse
import json
import re
from glob import glob
from subprocess import check_output

import mwxml
import nltk
from tqdm import tqdm

parser = argparse.ArgumentParser(description='extract backlinks with "main article" hints')
parser.add_argument('xmlfile', type=str, help='path to decompressed wikidump xml file')
parser.add_argument('index', type=str, help='path to wikidump index file, for counting purpose')
parser.add_argument('--folder', default=False, action="store_true",
                    help='(True | False[default]), if toggled, treat each line in xmlfiles as xml file path')
parser.add_argument('--counting', default=False, action="store_true",
                   help='(True | False[default]), if toggled, only count how many pages with "main article" hints')
parser.add_argument('-o', '--output', type=str,
                    help='path to store output file')
parser.add_argument('-f', '--frequency', type=str,
                    help='path to store heading frequency')
parser.add_argument('-w', '--words', type=str,
                    help='path to store words frequency')
parser.add_argument('-n', '--threads', type=int,
                    help='number of parallel processes')


args = parser.parse_args()
# get_ipython().system('cat {args.xmlfile} | grep "main article" | wc -l')


p = re.compile("{{[mM]ain article\|(?P<backlink>[^\<\[\}]*)}}")
h = re.compile("={2,}(?P<heading>[^\[=]*)={2,}")
heading_freq = {} # whole headings
word_freq = {} # words using in headings
main_articles = []
count = 0

def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])

pbar = tqdm(total=wc(args.index))

def map_main_article(dump, path):
    for page in dump:
        for rev in page:
            links = []
            headings = []
            if rev.text is not None:
                headings = h.findall(rev.text)            
                links = p.findall(rev.text)
                if len(links) != 0:
                    links = [e.strip() for l in links for e in l.split('|')]
            
            yield page.id, page.title, links, headings

stemmer = nltk.stem.porter.PorterStemmer()

if args.folder:
    xmlfile = glob(f"{args.xmlfile}/*.xml-*")
else:
    xmlfile = [args.xmlfile]

for id, title, links, headings in mwxml.map(map_main_article, xmlfile, threads=args.threads):
    pbar.update(1)
    
    if len(links) != 0:
        if args.counting:
            count += 1
            continue
        main_articles.append((id, title, str(links)))
    
    if len(headings) != 0:
        words = [w.strip() for hd in headings for w in hd.lower().split()]
        for each in headings:
            each = each.strip()
            if each in heading_freq:
                heading_freq[each] += 1
            else:
                heading_freq[each] = 1
        for each in words:
            if each in word_freq:
                word_freq[each] += 1
            else:
                word_freq[each] = 1

if args.counting:
    print(f'number of pages with main-article hints: {count}')
else:        
    result = sorted(main_articles, key=lambda item: item[0], reverse=False)
    with open(args.output, 'w') as f:
        for (id, title, links) in result:
            f.write(f"{id} {title} {links}\n")

    result1 = dict(sorted(heading_freq.items(), key=lambda item: item[1], reverse=True))
    with open(args.frequency, 'w') as f:
        f.write(json.dumps(result1))

    result2 = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))
    with open(args.words, 'w') as f:
        f.write(json.dumps(result2))

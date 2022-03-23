import argparse
import json
import os
import re
import string
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
parser.add_argument('--counting_only', default=False, action="store_true",
                   help='(True | False[default]), if toggled, only count how many pages with "main article" hints; It overrides all other flags and I/O options')

parser.add_argument('-o', '--output', type=str, default='output.txt',
                   help='default: output.txt | path to store output file')
parser.add_argument('-f', '--frequency', type=str, default=None,
                   help='default: None | path to store heading frequency')
parser.add_argument('-w', '--words', type=str, default=None,
                   help='default: None | path to store words frequency')
parser.add_argument('-k', '--keywords', type=str, default=None,
                   help='default: None | path to provided keyword list')
parser.add_argument('-kt', '--keywords_threshold', type=int, default=0,
                   help='default: 0 | minimal number of keywords matches for a wiki page to be counted as selected')
parser.add_argument('-n', '--threads', type=int, default=os.cpu_count()-1,
                   help='default: os.cpu_count()-1 | number of parallel processes')


args = parser.parse_args()
# get_ipython().system('cat {args.xmlfile} | grep "main article" | wc -l')

punc_space = re.compile("[^" + string.punctuation + " \t\n\r\f\v]+")
p = re.compile("{{[mM]ain article\|(?P<backlink>[^\<\[\}]*)}}")
h = re.compile("={2,}(?P<heading>[^\[=]*)={2,}")
heading_freq = {} # whole headings
word_freq = {} # words using in headings
main_articles = []
count = 0

def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])

def map_main_article(dump, path):
    for page in dump:
        for rev in page:
            links = []
            headings = []
            if rev.text is not None:
                headings = h.findall(rev.text)
                words = [w for hd in headings for w in punc_space.findall(hd.lower())] # stemmer.stem(w) will give more hits
                hit = False
                if args.keywords is not None:
                    keywords_match = 0
                    for each in words:
                        if keywords_match > args.keywords_threshold:
                            hit = True
                            break
                        if each in keywords:
                            keywords_match += 1
                
                links = p.findall(rev.text)
                if len(links) != 0:
                    links = [e.strip() for l in links for e in l.split('|')]
            
            yield page.id, page.title, links, headings, words, hit


stemmer = nltk.stem.porter.PorterStemmer()

if args.folder:
    xmlfile = glob(f"{args.xmlfile}/*.xml-*")
else:
    xmlfile = [args.xmlfile]
    
if args.keywords is not None:
    with open(args.keywords, 'r') as f:
        keywords = eval(f.read())
        stem = [stemmer.stem(x) for x in keywords]
        keywords = set(stem + keywords)
        print(f'{len(keywords)} keywords with stems provided')
        
    hits = []

pbar = tqdm(total=wc(args.index))
for id, title, links, headings, words, hit in mwxml.map(map_main_article, xmlfile, threads=args.threads):
    pbar.update(1)
    
    if len(links) != 0:
        count += 1
        if args.counting_only:
            continue
        main_articles.append((id, title, str(links)))
    
    if len(headings) != 0:
        if args.frequency is not None:
            for each in headings:
                each = each.strip()
                if each in heading_freq:
                    heading_freq[each] += 1
                else:
                    heading_freq[each] = 1

        if args.words is not None or args.keywords is not None:
            
            if args.words is not None:
                for each in words:
                    if each in word_freq:
                        word_freq[each] += 1
                    else:
                        word_freq[each] = 1
            if args.keywords is not None and hit:
                hits.append((id, title, str(links)))

print(f'number of pages with main-article hints: {count}')
if not args.counting_only:
    
    result = sorted(main_articles, key=lambda item: item[0], reverse=False)
    with open(args.output, 'w') as f:
        for (id, title, links) in result:
            f.write(f"{id} {title} {links}\n")

    if args.frequency is not None:
        result1 = dict(sorted(heading_freq.items(), key=lambda item: item[1], reverse=True))
        with open(args.frequency, 'w') as f:
            f.write(json.dumps(result1))

    if args.words is not None:
        result2 = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))
        with open(args.words, 'w') as f:
            f.write(json.dumps(result2))
    
    if args.keywords is not None:
        result3 = sorted(hits, key=lambda item: item[0], reverse=False)
        print(f'number of pages with more than {args.keywords_threshold} keywords match hints: {len(result3)}')
        with open(args.output+"-keywords-match.txt", 'w') as f:
            for (id, title, links) in result3:
                f.write(f"{id} {title} {links}\n")

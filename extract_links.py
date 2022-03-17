import re
import mwxml
import argparse
import sys
import json


parser = argparse.ArgumentParser(description='extract backlinks with "main article" hints')
parser.add_argument('xmlfile', type=str, help='path to decompressed wikidump xml file')
parser.add_argument('index', type=str, help='path to wikidump index file, for counting purpose')
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

import re
from tqdm import tqdm
from subprocess import check_output


p = re.compile("{{[mM]ain article\|(?P<backlink>[^\<\[\}]*)}}")
h = re.compile("={2,}(?P<heading>[^\[=]*)={2,}")
heading_freq = {} # whole headings
word_freq = {} # words using in headings


def wc(filename):
    return int(check_output(["wc", "-l", filename]).split()[0])

pbar = tqdm(total=wc(args.index))

def map_main_article(dump, path):
    for page in dump:
        for rev in page:
            if rev.text is not None:
                links = p.findall(rev.text)
                if len(links) != 0:
                    links = [e.strip() for l in links for e in l.split('|')]
                    headings = h.findall(rev.text)
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
            
            pbar.update(1)
            yield page.id, page.title, links

with open(args.output, 'w') as f:
    for id, title, links in mwxml.map(map_main_article, [args.xmlfile], threads=args.threads):
        if len(links) != 0:
            f.write(f"{id} {title} {str(links)}\n")

result = dict(sorted(heading_freq.items(), key=lambda item: item[1], reverse=True))
with open(args.frequency, 'w') as f:
    f.write(json.dumps(result))

result2 = dict(sorted(word_freq.items(), key=lambda item: item[1], reverse=True))
with open(args.words, 'w') as f:
    f.write(json.dumps(result2))


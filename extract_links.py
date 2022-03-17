import re
import mwxml
import argparse
import sys
import json


parser = argparse.ArgumentParser(description='extract backlinks with "main article" hints')
parser.add_argument('xmlfile', type=str, help='path to decompressed wikidump xml file')
parser.add_argument('-o', '--output', type=str,
                    help='path to store output file')
parser.add_argument('-f', '--frequency', type=str,
                    help='path to store heading frequency')
parser.add_argument('-n', '--threads', type=int,
                    help='number of parallel processes')


args = parser.parse_args()

# get_ipython().system('cat {args.xmlfile} | grep "main article" | wc -l')

p = re.compile("={2,}(?P<heading>[^\[=]*)={2,}(?:\n.*){0,2}?{{[mM]ain article\|(?P<backlink>[^\<\[\}]*)}}")
heading_freq = {}

def get_main_article(p, text):
    try:
        results = p.findall(text)
    except:
        print(text)
        results = {}
    return {t[0].strip(): t[1].split('|') for t in results}

def map_main_article(dump, path):
    for page in dump:
        for rev in page:
            main_articles = get_main_article(p, rev.text)
            for h in main_articles.keys():
                if h in heading_freq:
                    heading_freq[h] += 1
                else:
                    heading_freq[h] = 1
            yield page.id, page.title, main_articles

with open(args.output, 'w') as f:
    for id, title, article_map in mwxml.map(map_main_article, [args.xmlfile], threads=args.threads):
        if len(article_map) != 0:
            f.write(f"{id} {title} {str(article_map)}\n")

result = dict(sorted(heading_freq.items(), key=lambda item: item[1], reverse=True))
with open(args.frequency, 'w') as f:
    f.write(json.dumps(result))



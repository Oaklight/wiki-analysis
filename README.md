# Usage
```
usage: extract_links.py [-h] [--folder] [--counting_only] [-o OUTPUT] [-f FREQUENCY] [-w WORDS] [-k KEYWORDS]
                        [-kt KEYWORDS_THRESHOLD] [-n THREADS]
                        xmlfile index

extract backlinks with "main article" hints

positional arguments:
  xmlfile               path to decompressed wikidump xml file
  index                 path to wikidump index file, for counting purpose

optional arguments:
  -h, --help            show this help message and exit
  --folder              (True | False[default]), if toggled, treat each line in xmlfiles as xml file path
  --counting_only       (True | False[default]), if toggled, only count how many pages with "main article" hints; It overrides
                        all other flags and I/O options
  -o OUTPUT, --output OUTPUT
                        default: output.txt | path to store output file
  -f FREQUENCY, --frequency FREQUENCY
                        default: None | path to store heading frequency
  -w WORDS, --words WORDS
                        default: None | path to store words frequency
  -k KEYWORDS, --keywords KEYWORDS
                        default: None | path to provided keyword list
  -kt KEYWORDS_THRESHOLD, --keywords_threshold KEYWORDS_THRESHOLD
                        default: 0 | minimal number of keywords matches for a wiki page to be counted as selected
  -n THREADS, --threads THREADS
                        default: os.cpu_count()-1 | number of parallel processes
```

# examples
## 1 big dump
dump: https://dumps.wikimedia.org/enwiki/20220301/
```
2022-03-02 08:49:48 done Recombine multiple bz2 streams
enwiki-20220301-pages-articles-multistream.xml.bz2 19.2 GB         <---
enwiki-20220301-pages-articles-multistream-index.txt.bz2 228.9 MB
```

decompress after file is downloaded:
`bunzip2 enwiki-20220301-pages-articles-multistream.xml.bz2`

install dependencies, please refer to `requirements.txt`

replicate results:
`python extract_links.py enwiki-20220301-pages-articles-multistream.xml -o all-links.txt -f all-heading-freq.txt`

## sharded dumps
for faster processing, use sharded wikidump **AND** `enwiki-20220301-pages-articles-multistream-index.txt.bz2 228.9 MB` from big dump (for tqdm progress bar)
```
2022-03-02 08:29:24 done Articles, templates, media/file descriptions, and primary meta-pages, in multiple bz2 streams, 100 pages per stream
enwiki-20220301-pages-articles-multistream1.xml-p1p41242.bz2 246.2 MB
enwiki-20220301-pages-articles-multistream-index1.txt-p1p41242.bz2 221 KB
...
```
### data download
`aria2c -j3 -i index.html --deferred-input --auto-file-renaming=false`
where `index.html` is edited from https://dumps.wikimedia.org/enwiki/20220301/index.html, included in dir shards/

### decompress
decompress files with lbzip2 (faster):
`lbzip2 -d -k -f -v *.bz2`

replicate results:
`python extract_links.py ./shards/ enwiki-20220301-pages-articles-multistream-index.txt -n 40 -o all-main-articles.txt -f all-heading-freq.txt -w all-word-freq.txt --folder`

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
`python extract_links.py enwiki-20220301-pages-articles-multistream.xml -n 40 -o all-links.txt -f all-heading-freq.txt`
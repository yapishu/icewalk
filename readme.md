## IceWalk

Crawls sites and outputs contents in markdown for LLMs. Tries to fall over to selenium for JS-rendered content, runs concurrently.

Output format:

```json
     {
         "content": "# networked subject_\n\nA boutique Urbit star service.      \n\nPosts About \u20bfuy\n\nNetworked Subject\n",
         "metadata": {
             "title": "networked subject",
             "description": "",
             "language": "en-us",
             "sourceURL": "https://subject.network"
         }
     },

```

usage: `python3 crawl.py https://example.com`

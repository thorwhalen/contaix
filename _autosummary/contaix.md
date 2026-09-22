# contaix

Tools to make contexts (knowledge bases for AI agents)

### Examples

Download all articles from a markdown string and save them as PDF files:

```pycon
>>> download_articles(md_string)
```

Verify URLs in a markdown string by checking their status codes
(useful when trying to verify if AI hallucinated the urls)

```pycon
>>> verify_urls(md_string)
```

Make an md file with all the code in a directory:

```pycon
>>> md_string = code_aggregate(package_or_folder_or_github_url)
```

### Modules

| [`aggregation`](contaix.aggregation.md#module-contaix.aggregation)   | Tools for aggregating contexts                              |
|-------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| [`code`](contaix.code.md#module-contaix.code)                 | Tools to make AI contexts from code bases                   |
| [`markdown`](contaix.markdown.md#module-contaix.markdown)         | Converting things to markdown                               |
| [`skills`](contaix.skills.md#module-contaix.skills)             | Skill discovery and installation for the contaix ecosystem. |
| [`urls`](contaix.urls.md#module-contaix.urls)                 | Work with urls                                              |
| [`util`](contaix.util.md#module-contaix.util)                 | General utilities for contaix                               |
| [`web`](contaix.web.md#module-contaix.web)                   | Web content extraction and aggregation tools.               |

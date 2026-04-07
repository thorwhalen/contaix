# web.py Design Notes

## RSC (React Server Components) Flight Format

Modern documentation sites built with Next.js App Router use RSC streaming.
Understanding this format is key to extracting content without a browser.

### How RSC flight works

1. **Normal request**: Returns HTML shell with `self.__next_f.push([1, "..."])`
   script tags. These contain the RSC payload inline, but page content may be
   lazy-loaded (shows "Loading...").

2. **RSC request** (`RSC: 1` header): Returns `text/x-component` with the full
   RSC flight data, including page content.

### RSC flight line format

Each line is `key:payload`:

```
1:"$Sreact.fragment"           # React fragment reference
5:I[8729711517,[],""]          # Module import (I prefix)
0:{"b":"...","f":[...]}        # Route/layout data (JSON)
4:["$","$L16",null,{...}]      # React element (JSON array)
1d:[["$","$L23",null,{...}]]   # Content array (main page body)
61:Tde8,<pre class="shiki...   # Text chunk (T prefix, hex length)
```

### React element format

`["$", tagOrComponent, key, props]`

- `"$"` marks a React element
- Tag can be HTML (`"p"`, `"h2"`) or component reference (`"$L23"`)
- Props contain `children` (nested elements or strings)
- `$L` prefixed strings are references to other RSC keys

### T-chunks (Text chunks)

`key:Thex_length,raw_content`

Used for pre-rendered HTML (syntax-highlighted code blocks).
The content is HTML with `<pre><code><span>` structure.

## Content extraction pipeline

```
URL -> fetch RSC -> parse flight lines -> build registry
  -> find content node (longest with h1/h2/p/ul elements)
  -> resolve $L references via registry
  -> convert React tree to markdown
  -> post-process (clean $$ -> $, remove artifacts)
```

## Caching strategy

```
cache_dir/
  example.com__docs__en__intro.html       # Regular HTML (for nav extraction)
  example.com__docs__en__intro.rsc        # RSC flight data (for content)
```

The HTML cache is used for navigation extraction (first page only).
The RSC cache is used for content extraction (all pages).

## Table extraction

RSC tables are complex because rows may be defined as separate RSC nodes
referenced by `$L` keys. The extraction:
1. Walk the tree looking for `<tr>` elements
2. For each row, collect `<td>`/`<th>` cells
3. Build markdown table with header separator after first row

## Known limitations

1. **Code blocks**: CodeGroup components (`$L40` etc.) often point to
   client-side components not in the RSC stream. T-chunks contain the code
   but can't always be mapped back to the right position.

2. **Interactive elements**: Tabs, accordions, toggles are client-side.
   Only the default/first state is captured.

3. **Images**: Currently ignored in extraction. Could be preserved as
   markdown image references if URLs are available.

4. **Deeply nested references**: If a `$L` reference chain goes through
   client-side components, resolution fails silently.

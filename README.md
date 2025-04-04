# contaix

Tools to make contexts for AI

To install:	```pip install contaix```


# Markdown Conversion

This module provides tools for converting various file formats to Markdown. It supports common formats such as PDF, Word, Excel, PowerPoint, HTML, and Jupyter notebooks.

## Key Features

- Convert files to Markdown from bytes with format auto-detection
- Batch convert multiple files
- Customize output filenames and processing
- Extensible converter system

## Basic Usage

### Converting a Single File

The primary function `bytes_to_markdown` converts a file's bytes to Markdown text:

```python
from contaix import bytes_to_markdown

# Convert with explicit format
pdf_bytes = get_file_bytes('document.pdf')
markdown_text = bytes_to_markdown(pdf_bytes, "pdf")

# Or let the function detect the format from filename
markdown_text = bytes_to_markdown(file_bytes, input_format=None, key="document.docx")

# Or analyze the content to detect format (when no information is available)
markdown_text = bytes_to_markdown(
    unknown_bytes, 
    input_format=None, 
    key=None, 
    try_bytes_detection=True
)
```

### Converting Multiple Files

Use `bytes_store_to_markdown_store` to process multiple files at once:

```python
from contaix import bytes_store_to_markdown_store
from dol import Files

# Convert all files in a directory
src_files = Files('/path/to/documents')
target_store = {}
bytes_store_to_markdown_store(src_files, target_store)

# Now target_store contains {"file1.docx.md": "converted markdown...", ...}
```

## Advanced Usage

### Selective Conversion

If you only want to convert specific file types:

```python
# Filter to only include certain file types
filtered_files = {k: v for k, v in src_files.items() 
                 if k.endswith('.docx') or k.endswith('.pdf')}
bytes_store_to_markdown_store(filtered_files, target_store)
```

### Custom Output Naming

You can control how output filenames are generated:

```python
def custom_key_transform(key):
    # Remove the extension and add "-markdown.md"
    base_name = os.path.splitext(key)[0]
    return f"{base_name}-markdown.md"

bytes_store_to_markdown_store(
    src_files, 
    target_store, 
    old_to_new_key=custom_key_transform
)
```

### Content Aggregation

After conversion, you might want to combine all the markdown into a single document:

```python
def aggregate_content(store):
    """Combine all markdown content into a single document with headers."""
    result = "# Combined Markdown Document\n\n"
    
    for filename, content in store.items():
        result += f"## {filename}\n\n{content}\n\n---\n\n"
        
    return result

combined_markdown = bytes_store_to_markdown_store(
    src_files, 
    {}, 
    target_store_egress=aggregate_content
)
```

### Custom Converters

You can extend the system with your own converters:

```python
def custom_txt_converter(b):
    """A custom converter for text files."""
    text = b.decode('utf-8', errors='ignore')
    lines = text.split('\n')
    result = f"# Custom Converted Text File\n\n"
    
    for line in lines:
        if line.strip():
            result += f"> {line}\n"
    
    return result

custom_converters = {"txt": custom_txt_converter}

bytes_store_to_markdown_store(
    src_files,
    target_store,
    converters=custom_converters
)
```

## Format Detection Logic

The `bytes_to_markdown` function employs a prioritized strategy to find the right converter:

1. **Explicit Format**: If you provide `input_format`, it uses that directly
2. **Filename-Based**: If `input_format` is None but `key` (filename) is provided, it extracts the format from the extension
3. **Content-Based**: If `try_bytes_detection` is True, it analyzes the bytes to determine the format
4. **Fallback**: If no converter is found through the above methods, it uses the fallback converter

This flexible approach means you can control how formats are detected based on your specific needs.

## Performance Considerations

- If you know the file format in advance, specifying `input_format` will be faster
- To disable content-based detection (for better performance), set `try_bytes_detection=False`
- When processing large batches, filtering to only include supported formats can improve efficiency

## Supported Formats

The module currently supports the following formats:

- PDF (`.pdf`)
- Microsoft Word (`.docx`, `.doc`)
- Microsoft Excel (`.xlsx`, `.xls`)
- Microsoft PowerPoint (`.pptx`, `.ppt`)
- HTML (`.html`)
- Jupyter Notebooks (`.ipynb`)
- Plain text (`.txt`, `.md`)

Additional formats can be supported by adding custom converters.
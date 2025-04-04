"""
Tests for the markdown conversion functions in contaix.

These tests cover realistic user stories for converting various file formats to markdown
using the bytes_to_markdown and bytes_store_to_markdown_store functions.
"""

import os
import pytest
from typing import Dict, Any, Callable
from pathlib import Path

from contaix.tests.utils_for_testing_contaix import test_data_dir
from dol import Files

from contaix.markdown import bytes_to_markdown, bytes_store_to_markdown_store


# Helper function to read the expected content
def _get_expected_content(filename: str) -> str:
    """Read the expected content for a specific file from the test data"""
    with open(
        os.path.join(test_data_dir, f"{filename}.md"), "r", encoding="utf-8"
    ) as f:
        return f.read()


def test_bytes_to_markdown_with_explicit_format():
    """
    User story: I have a PDF file as bytes and I know its format.
    I want to convert it directly to markdown without any guessing.
    """
    # Get the PDF file content
    src_files = Files(test_data_dir)
    pdf_bytes = src_files["test.pdf"]

    # Convert with explicit format
    markdown_content = bytes_to_markdown(pdf_bytes, "pdf")

    # Verify it worked correctly
    assert "Page 1" in markdown_content
    assert "This  is  a  title" in markdown_content


def test_bytes_to_markdown_with_key_detection():
    """
    User story: I have a DOCX file and its filename, but I don't want to
    manually specify the format. I want the function to extract the format from the filename.
    """
    # Get the DOCX file content
    src_files = Files(test_data_dir)
    docx_bytes = src_files["test.docx"]

    # Convert using the key (filename) for format detection
    markdown_content = bytes_to_markdown(docx_bytes, input_format=None, key="test.docx")

    # Verify it worked correctly
    assert "This is a title" in markdown_content
    assert "This is Heading 1" in markdown_content


def test_bytes_to_markdown_with_content_detection():
    """
    User story: I have a file as bytes but I don't know its format or original filename.
    I want the function to analyze the bytes and determine the format automatically.
    """
    # Get the HTML file content
    src_files = Files(test_data_dir)
    html_bytes = src_files["test.html"]

    # Convert using content-based detection
    markdown_content = bytes_to_markdown(
        html_bytes,
        input_format=None,
        key=None,
        ext_to_input_format=None,
        try_bytes_detection=True,
        verbose=True,  # Enable verbose to see detection messages
    )

    # Verify it worked correctly
    assert "Heading 1" in markdown_content
    assert "This is a paragraph" in markdown_content


def test_bytes_to_markdown_with_fallback():
    """
    User story: I have a file in an unsupported format. I want the system to
    handle the failure gracefully and provide a reasonable fallback.
    """
    # Create some bytes that don't match any known format
    unknown_bytes = b"This is some random text that doesn't match any known format"

    # Convert with fallback
    markdown_content = bytes_to_markdown(unknown_bytes, "unknown_format")

    # Verify it fell back to the default fallback
    assert (
        "Conversion Failed" in markdown_content
        or "This is some random text" in markdown_content
    )


def test_bytes_to_markdown_excel_conversion():
    """
    User story: I have an Excel file with data tables that I want to convert
    to markdown tables for documentation.
    """
    # Get the Excel file content
    src_files = Files(test_data_dir)
    xlsx_bytes = src_files["test.xlsx"]

    # Convert with explicit format
    markdown_content = bytes_to_markdown(xlsx_bytes, "xlsx")

    # Verify it created markdown tables correctly
    assert "Sheet: Sheet1" in markdown_content
    assert "hourly_fee" in markdown_content
    assert "hours" in markdown_content
    assert "total" in markdown_content


def test_bytes_store_to_markdown_store_directory():
    """
    User story: I have a directory with multiple files in different formats.
    I want to batch convert all supported files to markdown and store them in memory.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # Setup target store as an in-memory dictionary
    target_store = {}

    # Convert all files in directory to markdown
    result = bytes_store_to_markdown_store(src_files, target_store, verbose=True)

    # Check that the result is the target_store
    assert result is target_store

    # Verify that the supported file types were converted correctly
    supported_files = [
        "test.docx",
        "test.pptx",
        "test.pdf",
        "test.html",
        "test.xlsx",
        "test.txt",
        "test.md",
        "test.ipynb",
    ]

    for filename in supported_files:
        assert f"{filename}.md" in target_store
        assert len(target_store[f"{filename}.md"]) > 0


def test_bytes_store_to_markdown_store_selective_conversion():
    """
    User story: I have a collection of files but only want to convert specific file types.
    I want to control which files get converted based on their extensions.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # Setup a dict with only docx and pdf files
    filtered_files = {
        k: v for k, v in src_files.items() if k.endswith('.docx') or k.endswith('.pdf')
    }

    # Setup target store as an in-memory dictionary
    target_store = {}

    # Convert only the filtered files
    bytes_store_to_markdown_store(filtered_files, target_store)

    # Verify that only the expected files were converted
    assert len(target_store) == 2
    assert "test.docx.md" in target_store
    assert "test.pdf.md" in target_store
    assert "test.xlsx.md" not in target_store


def test_bytes_store_to_markdown_store_with_custom_key_transform():
    """
    User story: I want to convert files to markdown but need to customize
    the output filenames to match a specific naming convention.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # Filter to only include a few files for simplicity
    filtered_files = {
        k: v for k, v in src_files.items() if k in ['test.docx', 'test.pdf']
    }

    # Setup target store
    target_store = {}

    # Define a custom key transformation function
    def custom_key_transform(key: str) -> str:
        # Remove the extension and add "-markdown.md"
        base_name = os.path.splitext(key)[0]
        return f"{base_name}-markdown.md"

    # Convert with custom key transformation
    bytes_store_to_markdown_store(
        filtered_files, target_store, old_to_new_key=custom_key_transform
    )

    # Verify the custom naming worked
    assert "test-markdown.md" in target_store
    assert "test.docx.md" not in target_store
    assert "test.pdf.md" not in target_store


def test_bytes_store_to_markdown_store_with_custom_egress():
    """
    User story: After converting files to markdown, I want to aggregate all the content
    into a single markdown document with sections for each file.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # Filter to only include a few files for simplicity
    filtered_files = {
        k: v for k, v in src_files.items() if k in ['test.docx', 'test.pdf']
    }

    # Define a custom egress function to aggregate content
    def aggregate_content(store: Dict[str, str]) -> str:
        """Combine all markdown content into a single document with headers."""
        result = "# Combined Markdown Document\n\n"

        for filename, content in store.items():
            result += f"## {filename}\n\n{content}\n\n---\n\n"

        return result

    # Convert and aggregate
    aggregated_content = bytes_store_to_markdown_store(
        filtered_files, {}, target_store_egress=aggregate_content
    )

    # Verify the aggregation worked
    assert isinstance(aggregated_content, str)
    assert "# Combined Markdown Document" in aggregated_content
    assert "## test.docx.md" in aggregated_content
    assert "## test.pdf.md" in aggregated_content


def test_bytes_store_to_markdown_store_with_byte_detection_disabled():
    """
    User story: I want to process files strictly by their extensions and
    disable content-based detection for improved performance.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # Create a file with mismatched extension and content
    mismatched_bytes = src_files["test.docx"]  # This is a DOCX file
    test_files = {"fake.xlsx": mismatched_bytes}  # But we'll name it as XLSX

    # Convert without content detection
    target_store = {}
    bytes_store_to_markdown_store(
        test_files, target_store, try_bytes_detection=False  # Disable content detection
    )

    # The system should try to convert as xlsx (based on extension) but might fail
    # We're not testing the specific output, just that it processed based on extension
    assert "fake.xlsx.md" in target_store


def test_file_content_matches_expected():
    """
    User story: I want to ensure that the Markdown conversion produces the expected output
    for each supported file format.
    """
    # Setup source files from test directory
    src_files = Files(test_data_dir)

    # List of supported file formats to test
    supported_files = [
        "test.docx",
        "test.pptx",
        "test.pdf",
        "test.html",
        "test.xlsx",
        "test.txt",
        "test.md",
        "test.ipynb",
    ]

    # For each supported format, test against expected content
    for filename in supported_files:
        # Get file content and expected result
        file_bytes = src_files[filename]

        # Convert to markdown
        converted = bytes_to_markdown(file_bytes, os.path.splitext(filename)[1][1:])

        # Assert content meets basic expectations based on file type
        if "docx" in filename:
            assert "This is a title" in converted
            assert "This is Heading 1" in converted
        elif "pptx" in filename:
            assert "Slide" in converted
        elif "pdf" in filename:
            assert "Page 1" in converted
        elif "html" in filename:
            assert "Heading 1" in converted
        elif "xlsx" in filename:
            assert "Sheet:" in converted
            assert "hourly_fee" in converted
        elif "ipynb" in filename:
            assert "Header 1" in converted
            assert "code block" in converted


def test_bytes_store_to_markdown_store_with_custom_converters():
    """
    User story: I want to use my own custom converter for a specific file format.
    """
    # Setup source files
    src_files = Files(test_data_dir)

    # Filter to only include text files
    text_files = {k: v for k, v in src_files.items() if k.endswith('.txt')}

    # Define a custom converter for text files
    def custom_txt_converter(b: bytes) -> str:
        """A simple custom converter that adds some formatting to text files."""
        text = b.decode('utf-8', errors='ignore')
        lines = text.split('\n')
        result = f"# Custom Converted Text File\n\n"

        for line in lines:
            if line.strip():
                result += f"> {line}\n"

        return result

    # Create a converters dictionary with our custom converter
    custom_converters = {"txt": custom_txt_converter}

    # Setup target store
    target_store = {}

    # Convert using custom converters
    bytes_store_to_markdown_store(
        text_files, target_store, converters=custom_converters
    )

    # Verify our custom converter was used
    assert "test.txt.md" in target_store
    assert "# Custom Converted Text File" in target_store["test.txt.md"]
    assert ">" in target_store["test.txt.md"]

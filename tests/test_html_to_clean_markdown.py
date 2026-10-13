"""Tests for ``contaix.web.html_to_clean_markdown`` and the html2text-free dependency set."""

import subprocess
import sys
from pathlib import Path

import pytest

from contaix.web import _extract_main_content_html, html_to_clean_markdown

ROOT = Path(__file__).resolve().parent.parent


def test_core_dependencies_exclude_copyleft_html2text():
    tomllib = pytest.importorskip("tomllib")  # py>=3.11
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
        "dependencies"
    ]
    assert not any(d.lower().startswith("html2text") for d in deps)
    assert any(d.startswith("markdownify") for d in deps)


def test_importing_contaix_web_does_not_import_html2text():
    code = "import sys, contaix.web; sys.exit('html2text' in sys.modules)"
    assert subprocess.run([sys.executable, "-I", "-c", code]).returncode == 0


def test_basic_structure():
    html = (
        "<h1>Title</h1><p>Some <b>bold</b>, <i>it</i> and <code>code</code>.</p>"
        "<ul><li>one</li><li>two</li></ul><p>Snake_case_name and a*b*c</p>"
    )
    md = html_to_clean_markdown(html)
    assert md.startswith("# Title\n\n")
    assert "**bold**" in md and "`code`" in md
    assert "* one" in md and "* two" in md
    assert "Snake_case_name" in md and "a*b*c" in md  # no escaping noise


def test_links_and_images_options():
    html = '<p><a href="http://x.org/a">link</a> <img src="i.png" alt="pic"></p>'
    assert html_to_clean_markdown(html) == "[link](http://x.org/a)"
    assert html_to_clean_markdown(html, include_links=False) == "link"
    assert "![pic](i.png)" in html_to_clean_markdown(html, ignore_images=False)


def test_non_content_tags_are_dropped():
    html = (
        "<html><head><title>T</title><style>p{}</style></head>"
        "<body><script>alert(1)</script><noscript>x</noscript><p>body</p></body></html>"
    )
    assert html_to_clean_markdown(html) == "body"


def test_blank_lines_inside_code_blocks_are_preserved():
    html = "<p>a</p><br><br><br><p>b</p><pre><code>def f():\n    pass\n\n\ndef g():\n    pass\n</code></pre>"
    md = html_to_clean_markdown(html)
    assert "\n\n\n" not in md.split("```")[0]  # collapsed outside code
    assert "pass\n\n\ndef g" in md  # PEP 8 spacing kept inside code


def test_tables_survive():
    md = html_to_clean_markdown(
        "<table><tr><th>k</th><th>v</th></tr><tr><td>a</td><td>1</td></tr></table>"
    )
    assert "| k | v |" in md and "| a | 1 |" in md


def test_entities_are_kept_as_characters():
    assert html_to_clean_markdown("<p>&copy; a&nbsp;b</p>") == "© a b"


def test_empty_input():
    assert html_to_clean_markdown("") == ""
    assert html_to_clean_markdown("   ") == ""


def test_unknown_options_raise_instead_of_being_ignored():
    with pytest.raises(TypeError, match="ignore_links"):
        html_to_clean_markdown("<p>x</p>", ignore_links=True)
    with pytest.raises(TypeError, match="unicode_snob"):
        html_to_clean_markdown("<p>x</p>", unicode_snob=True)


def test_markdownify_options_pass_through():
    assert html_to_clean_markdown("<h1>T</h1>", heading_style="UNDERLINED").startswith(
        "T\n="
    )
    assert html_to_clean_markdown("<ul><li>a</li></ul>", bullets="-") == "- a"


def test_strip_option_composes_with_flags():
    html = '<p><b>b</b> <a href="u">l</a> <img src="i.png"></p>'
    assert html_to_clean_markdown(html, strip=["b"]) == "b [l](u)"


def test_body_width_nonzero_is_rejected_zero_accepted():
    assert html_to_clean_markdown("<p>x</p>", body_width=0) == "x"
    with pytest.raises(ValueError, match="body_width"):
        html_to_clean_markdown("<p>x</p>", body_width=80)


def test_extract_main_content_prefers_article():
    filler = "word " * 40
    html = f"<nav>menu</nav><article><h1>Hi</h1><p>{filler}</p></article><footer>f</footer>"
    md = _extract_main_content_html(html)
    assert md.startswith("# Hi") and "menu" not in md and "footer" not in md


# --- regressions found by the adversarial review (omitted end tags, glued words, ...) ---


@pytest.mark.parametrize(
    "html, expected",
    [
        ("<ul><li>a<li>b<li>c</ul>", "* a\n* b\n* c"),
        ("<ol><li>one<li>two</ol>", "1. one\n2. two"),
        (
            "<table><tr><th>h1<th>h2<tr><td>a<td>b</table>",
            "| h1 | h2 |\n| --- | --- |\n| a | b |",
        ),
    ],
)
def test_omitted_end_tags_parse_like_a_browser(html, expected):
    assert html_to_clean_markdown(html) == expected


@pytest.mark.parametrize(
    "html",
    [
        "<ul>" + "<li>x" * 2000 + "</ul>",
        "<div>" * 600 + "x" + "</div>" * 600,
        "<b>x " * 700,
    ],
)
def test_deeply_nested_html_does_not_raise_recursion_error(html):
    assert "x" in html_to_clean_markdown(html)


def test_text_after_nested_list_is_not_glued_to_its_last_item():
    md = html_to_clean_markdown(
        "<ul><li>x<ul><li>next batch</li></ul>Ten sheets</li></ul>"
    )
    assert "next batchTen" not in md and "next batch" in md and "Ten sheets" in md


def test_heading_inside_link_stays_a_heading():
    assert html_to_clean_markdown('<a href="/x"><h2>Head</h2></a>') == "## [Head](/x)"
    card = html_to_clean_markdown('<a href="/c"><div><h3>T</h3><p>B</p></div></a>')
    assert card.startswith("### [T](/c)") and "B" in card


def test_code_containing_a_fence_gets_a_longer_fence():
    md = html_to_clean_markdown("<pre>```\ninner\n```</pre>")
    assert md == "````\n```\ninner\n```\n````"


def test_blank_lines_kept_in_code_nested_in_lists():
    md = html_to_clean_markdown(
        "<ul><li>x<ul><li>i<pre>a\n\n\n\nb</pre></li></ul></li></ul>"
    )
    assert "a\n\n\n\n    b" in md


def test_convert_and_string_strip_options():
    html = "<p><b>b</b><i>i</i><img src=x></p>"
    assert html_to_clean_markdown(html, convert=["b", "i", "img"]) == "**b***i*"
    assert html_to_clean_markdown("<p>a <code>c</code></p>", strip="code") == "a c"


def test_source_newlines_do_not_create_block_syntax():
    assert (
        html_to_clean_markdown("<p>Total\n# of items\n- b</p>")
        == "Total # of items - b"
    )


def test_permalink_anchors_are_dropped():
    html = '<h2>Install<a class="headerlink" href="#install">¶</a></h2>'
    assert html_to_clean_markdown(html) == "## Install"


def test_inline_content_after_a_non_nested_list_is_not_glued():
    md = html_to_clean_markdown(
        "<div><ul><li>next batch</li></ul><span>Ten sheets</span></div>"
    )
    assert "batchTen" not in md and "Ten sheets" in md


def test_only_heading_permalinks_are_dropped_not_real_section_signs():
    assert html_to_clean_markdown("<p>See <a href='#fn1'>§</a> 3 of the act</p>") == (
        "See [§](#fn1) 3 of the act"
    )
    assert html_to_clean_markdown("<p>Issue <a href='#'>#</a></p>") == "Issue <#>"


def test_link_destinations_with_spaces_and_parens_stay_valid():
    assert (
        html_to_clean_markdown('<a href="my file.html">x</a>') == "[x](my%20file.html)"
    )
    assert html_to_clean_markdown('<a href="/a)b">y</a>') == "[y](/a%29b)"


def test_deep_nesting_is_not_quadratic_in_prepare():
    import time

    start = time.perf_counter()
    html_to_clean_markdown("<p><font>x " * 600 + "end")
    assert time.perf_counter() - start < 10


def test_concurrent_deep_pages_leave_the_recursion_limit_untouched():
    import sys
    import threading

    html = "<div>" * 1500 + "x" + "</div>" * 1500
    before = sys.getrecursionlimit()
    results = []
    threads = [
        threading.Thread(target=lambda: results.append(html_to_clean_markdown(html)))
        for _ in range(4)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 4 and all("x" in r for r in results)
    assert sys.getrecursionlimit() == before

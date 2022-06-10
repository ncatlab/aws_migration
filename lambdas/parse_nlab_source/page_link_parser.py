import os
import re
import urllib.parse

import mistletoe.span_token

import latex_parser
from nlab_parsing_errors import NLabSyntaxError, NotYetSupportedError

_file_root_url = os.environ["FILE_ROOT_URL"]
_page_root_url = os.environ["PAGE_ROOT_URL"]

"""
Matches anything within [[ and ]] which does not contain a |, and converts it to
a link to page. It is assumed that page links are valid.
"""
class SimplePageLinkToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"\[\[([^\|]+?)\]\]")

    def __init__(self, match):
        self.page_name = match.group(1).strip()

    def render(self):
        if "#" in self.page_name:
            raise NotYetSupportedError("Anchors in links not supported yet")
        elif ":" in self.page_name:
            if self.page_name[-5:] == ":file" and not (
                    ":" in self.page_name[:-5]):
                return (
                    "<a class=\"file_link\" href=\"" +
                    _file_root_url +
                    urllib.parse.quote(self.page_name[:-5]) +
                    "\">" +
                    "file" +
                    "</a>")
            raise NotYetSupportedError(
                "Cross-web links, as well as image links, are not " +
                "supported yet")
        return (
            "<a class=\"page_link\" href=\"" +
            _page_root_url +
            urllib.parse.quote_plus(self.page_name) +
            "\">" +
            self.page_name +
            "</a>")

"""
Matches anything of the form [[ x | y]] which does not contain any further |,
and converts it to a link to an nLab page x with displayed text y. It is
assumed that page links are valid.
"""
class PageLinkWithDisplayTextToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"(?!\[\[([^\|]+?)\]\])\[\[([^\|]+?)\|([^\|]+?)\]\]")
    precedence = 20

    def __init__(self, match):
        self.page_name = match.group(2).strip()
        # Allow for use of LaTeX in display text
        self.display_text = re.sub(
            r"(?<!\$)\$(?!\$)(.+?)\$",
            lambda latex_match: latex_parser.render_latex(
                latex_match.group(1),
                "inline"),
            match.group(3).strip())

    def render(self):
        if "#" in self.page_name:
            raise NotYetSupportedError("Anchors in links not supported yet")
        elif ":" in self.page_name:
            raise NotYetSupportedError("Cross-web links not supported yet")
        elif ":" in self.display_text:
            if self.display_text[-5:] == ":file" and not (
                    ":" in self.page_name):
                return (
                    "<a class=\"file_link\" href=\"" +
                    _file_root_url +
                    urllib.parse.quote(self.page_name) +
                    "\">" +
                    self.display_text[:-5] +
                    "</a>")
            raise NotYetSupportedError("Image links not supported yet")
        return (
            "<a class=\"page_link\" href=\"" +
            _page_root_url +
            urllib.parse.quote_plus(self.page_name) +
            "\">" +
            self.display_text +
            "</a>")

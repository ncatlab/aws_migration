import re

import mistletoe.span_token

"""
Matches anything within [[!include and ]] and converts it to a div whose
content will be (using javascript) the rendered HTML of the page whose name is
equal to the match.
"""
class IncludeToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"\[\[\s*!include(.*?)\]\]")

    def __init__(self, match):
        self.page_to_include = match.group(1).strip()

    def render(self):
        return (
            "<div class=\"page_inclusion\"" +
            "data-page-to-include=\"{}\">\n</div>".format(
                self.page_to_include))

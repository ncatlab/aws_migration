import re

import mistletoe.span_token

import nlab_parsing_errors

def render_latex(latex, display):
    label = None
    if display == "block":
        label_regex = re.compile(r"\\label\{(.*?)\}")
        label_match = label_regex.search(latex)
        if label_match:
            label = label_match.group(1)
            latex = re.sub(label_regex, "", latex)
    if label:
        return (
            "<span class=\"latex\" data-latex=\"{}\" ".format(latex) +
            "data-display-mode='block' id='{}'></span>\n".format(label))
    elif display != "block":
        return "<span class=\"latex\" data-latex=\"{}\"></span>".format(latex)
    else:
        return (
            "<span class=\"latex\" data-latex=\"{}\" ".format(latex) +
            "data-display-mode=\"block\"></span>\n")


"""
Matches anything within $ and $, not beginning with $$, and prepares it for
processing with katex
"""
class InlineLatexToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"(?<!\$)\$(?!\$)(.+?)\$", re.DOTALL)

    def __init__(self, match):
        self.latex = match.group(1)
        if "\"" in self.latex:
            raise nlab_parsing_errors.NLabSyntaxError(
                "Use of \" not permitted in a LaTeX block. Used in: {}".format(
                    self.latex))

    def render(self):
        return (
            "<span class=\"latex\" data-latex=\"{}\"></span>".format(
            self.latex))

"""
Matches anything within $$ and $$, or within \[ and \], and prepares it for
processing with katex
"""
class StandAloneLatexToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"(\$\$(.*?)\$\$)|(\\\[(.*?)\\\])", re.DOTALL)

    def __init__(self, match):
        if match.group(2) is not None:
            self.latex = match.group(2)
        else:
            self.latex = match.group(4)
        if "\"" in self.latex:
            raise nlab_parsing_errors.NLabSyntaxError(
                "Use of \" not permitted in a LaTeX block. Used in: {}".format(
                    self.latex))

    def render(self):
        return render_latex(self.latex, "block")

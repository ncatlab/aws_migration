import re

import mistletoe.span_token

"""
Matches \ref{...} and converts to a link with no text whose href points to
# + the string inside the {...}. The text of the link (numbering of the
relevant environment or equation) will be added client-side.
"""
class EnvironmentOrEquationReferenceToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"\\ref\{(.*?)\}")

    def __init__(self, match):
        self.reference = match.group(1).strip()

    def render(self):
        return (
            "<a class=\"environment_or_equation_reference\" href=\"#" +
            self.reference +
            "\"></a>")

"""
Matches eq:something (terminating in whitespace or a right bracket) and converts
to a link with no text whose href points to
# + the string inside the {...}. The text of the link (numbering of the
relevant equation) will be added client-side.
"""
class EquationReferenceToken(mistletoe.span_token.SpanToken):
    pattern = re.compile(r"eq:(.*?)([\s|)])")

    def __init__(self, match):
        self.reference = match.group(1).strip()
        self.ending = match.group(2)

    def render(self):
        return (
            "<a class=\"environment_or_equation_reference\" href=\"#" +
            self.reference +
            "\"></a>" +
            self.ending)

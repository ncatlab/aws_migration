#!/usr/bin/python3

import json
import re

import image_from_file_parser
import latex_parser
import nlab_mistletoe
from nlab_parsing_errors import NLabSyntaxError, NotYetSupportedError

_centre_regex = re.compile(r"\\begin{centre}(.*?)\\end{centre}", re.DOTALL)
_center_regex = re.compile(r"\\begin{center}(.*?)\\end{center}", re.DOTALL)
_image_from_file_regex = re.compile(
    r"\\begin{imagefromfile}(.*?)\\end{imagefromfile}",
    re.DOTALL)

class Renderer:
    def __init__(self, top_level = True):
        self.mode = ""
        self.theorem_environment = None
        self.to_parse = []
        self.beginning_or_follows_blank = True
        self.parsed = []
        self.is_start_line = False
        self.preamble = []
        self.top_level = top_level

    def _no_mode(self, line, require_blank_lines_after):
        line = line.lstrip()
        if line.startswith("#"):
            self.beginning_or_follows_blank = False
            # Some versions of markdown allow the heading text to come
            # immediately after the ###s without any spaces, but Mistletoe does
            # not. Thus we ensure that there is a space.
            match = re.compile(r"^([#]+)(.*?)($|#)").search(line)
            if len(match.group(1)) == 1:
                raise NLabSyntaxError(
                    "Use of # (i.e. <h1>) is not permitted. Use ## for " +
                    "top-level sections.")
            self.parsed.append(
                nlab_mistletoe.render(match.group(1) +
                " " +
                match.group(2)))
            self.mode = "handled"
        elif line.lstrip().startswith("$$"):
            self.beginning_or_follows_blank = False
            self.mode = "latex_double_dollar"
            self.is_start_line = True
        elif line.startswith("\\["):
            self.beginning_or_follows_blank = False
            self.mode = "latex_square_bracket"
        elif line.startswith("[[!redirects"):
            raise NLabSyntaxError(
                "Redirects no longer handled in source editing")
        elif line.startswith("\\tableofcontents"):
            self.beginning_or_follows_blank = False
            self.preamble.append(
                "<h2 id=\"contents_header\">Contents</h2>\n" +
                "<div id=\"table_of_contents\"></div>\n")
            self.mode = "handled"
        elif line.startswith("* table of contents"):
            raise NLabSyntaxError(
                "Old syntax for table of contents no longer supported. " +
                "Use a line\n\n{}\n\ninstead.".format(
                    "\\tableofcontents"))
        elif line.startswith("category:"):
            raise NLabSyntaxError(
                "Page categories no longer handled in source editing")
        elif "<nowiki>" in line:
            raise NotYetSupportedError(
                "<nowiki>...</nowiki> not supported yet")
        elif line.startswith("+-- {: .rightHandSide}"):
            raise NLabSyntaxError(
                "Old syntax for context menus no longer supported. Use\n\n" +
                "{}\n\ninstead, replacing ... by the name of the ".format(
                    "\\context_menu[...]") +
                "context menu.")
        elif line.startswith("\\context_menu"):
            contexts = re.compile(
                r"\\context_menu\[(.*?)\]").search(line).group(1)
            html = "<div id=\"context_menu\">\n"
            for context in contexts.split(","):
                html += "<div id=\"context_" + \
                    "_".join(context.strip().split()) + \
                    "\"></div>\n"
            html += "</div>\n"
            self.preamble.append(html)
            self.mode = "handled"
        elif line.startswith("\\begin{centre}"):
            self.beginning_or_follows_blank = False
            self.mode = "centre"
        elif line.startswith("\\begin{center}"):
            self.beginning_or_follows_blank = False
            self.mode = "center"
        elif line.startswith("\\begin{imagefromfile}"):
            self.beginning_or_follows_blank = False
            self.mode = "imagefromfile"
        else:
            self.theorem_environment = \
                TheoremEnvironmentParser.match_new(line)
            if self.theorem_environment is not None:
                self.beginning_or_follows_blank = False
                self.mode = "theorem_environment_new"
                return
            self.theorem_environment = \
                TheoremEnvironmentParser.match_old(line)
            if self.theorem_environment is not None:
                raise NLabSyntaxError(
                    "Old syntax for theorem environments no longer " +
                    "supported. Use \\begin{theorem} ... \\end{theorem} " +
                    "or similar instead")
                self.beginning_or_follows_blank = False
                self.mode = "theorem_environment_old"
                return
            elif not line.strip() :
                self.beginning_or_follows_blank = True
                self.mode = "handled"
            elif (not self.beginning_or_follows_blank) and \
                    require_blank_lines_after:
                raise NLabSyntaxError(
                    "Line should be blank as it follows a markdown " +
                    "environment: " +
                    line)
            else:
                self.mode = "mistletoe"

    def render(self, source, require_blank_lines_after = True):
        for line in source.split("\n"):
            # Old-syntax page anchors
            line = re.sub(
                r"\{#(.*?)\}",
                "<span id=\"" + r"\g<1>" + "\"></span>",
                line)
            # Line breaks
            line = re.sub(r"\\linebreak", "<br>", line)
            if not self.mode:
                self._no_mode(line, require_blank_lines_after)
            if self.mode == "handled":
                self.mode = ""
                continue
            self.to_parse.append(line)
            if self.mode == "mistletoe":
                if not line.strip():
                    self.parsed.append(nlab_mistletoe.render(self.to_parse))
                    self.mode = ""
                    self.to_parse.clear()
            elif self.mode == "theorem_environment_new":
                if "\\end{" + self.theorem_environment in line:
                    self.parsed.append(
                        TheoremEnvironmentParser.render_new(
                            self.theorem_environment,
                            "\n".join(self.to_parse)))
                    self.mode = ""
                    self.to_parse.clear()
                    self.theorem_environment = None
            elif self.mode == "theorem_environment_old":
                if "=--" in line:
                    self.parsed.append(
                        TheoremEnvironmentParser.render_old(
                            self.theorem_environment,
                            "\n".join(self.to_parse)))
                    self.mode = ""
                    self.to_parse.clear()
                    self.theorem_environment = None
            elif self.mode == "latex_double_dollar":
                if self.is_start_line:
                    double_dollar_parts = line.split("$$")
                    if ((len(double_dollar_parts) > 3) or (
                            (len(double_dollar_parts) == 3) and \
                            double_dollar_parts[2].strip())):
                        raise NLabSyntaxError(
                            "Closing $$ of a stand-alone LaTeX block should " +
                            "not have anything after it on the same line. " +
                            "Line: " +
                            line)
                    elif ((len(double_dollar_parts) == 1) or (
                            (len(double_dollar_parts) == 2) and not \
                            double_dollar_parts[1].strip())):
                        self.is_start_line = False
                    else:
                        self.parsed.append(latex_parser.render_latex(
                            "\n".join(self.to_parse).replace(
                                "$$",""),
                            "block"))
                        self.mode = ""
                        self.to_parse.clear()
                        self.is_start_line = False
                elif "$$" in line:
                    self.parsed.append(latex_parser.render_latex(
                        "\n".join(self.to_parse).replace(
                            "$$",""),
                        "block"))
                    if line.split("$$")[1].rstrip():
                        raise NLabSyntaxError(
                            "Closing $$ of a stand-alone LaTeX block should " +
                            "not have anything after it on the same line. " +
                            "Line: " +
                            line)
                    self.mode = ""
                    self.to_parse.clear()
            elif self.mode == "latex_square_bracket":
                if "\\]" in line:
                    self.parsed.append(latex_parser.render_latex(
                        "\n".join(self.to_parse).replace(
                            "\\[", "").replace("\\]", ""),
                        "block"))
                    if line.split("\\]")[1].rstrip():
                        raise NLabSyntaxError(
                            "Closing \\]\\] of a stand-alone LaTeX block " +
                            "should not have anything after it on the same " +
                            "line. Line: " +
                            line)
                    self.mode = ""
                    self.to_parse.clear()
            elif self.mode == "centre":
                if "\\end{centre}" in line:
                    if line.split("\\end{centre}")[1].rstrip():
                        raise NLabSyntaxError(
                            "\\end{centre} should not have anything after " +
                            "it on the same line. Line: {}".format(line))
                    self.parsed.append("{}\n{}\n{}".format(
                        "<div class=\"centre\">",
                        "\n".join(Renderer(top_level = False).render(re.match(
                            _centre_regex,
                            "\n".join(self.to_parse)).group(1))),
                        "</div>"))
                    self.mode = ""
                    self.to_parse.clear()
            elif self.mode == "center":
                if "\\end{center}" in line:
                    if line.split("\\end{center}")[1].rstrip():
                        raise NLabSyntaxError(
                            "\\end{center} should not have anything after " +
                            "it on the same line. Line: {}".format(line))
                    self.parsed.append("{}\n{}\n{}".format(
                        "<div class=\"centre\">",
                        "\n".join(Renderer(top_level = False).render(re.match(
                            _center_regex,
                            "\n".join(self.to_parse)).group(1))),
                        "</div>"))
                    self.mode = ""
                    self.to_parse.clear()
            elif self.mode == "imagefromfile":
               if "\\end{imagefromfile}" in line:
                    if line.split("\\end{imagefromfile}")[1].rstrip():
                        raise NLabSyntaxError(
                            "\\end{imagefromfile} should not have anything " +
                            "after it on the same line. Line: {}".format(line))
                    self.parsed.append(image_from_file_parser.render(
                        re.match(
                            _image_from_file_regex,
                            "\n".join(self.to_parse)).group(1)))
                    self.mode = ""
                    self.to_parse.clear()
        if self.mode == "mistletoe":
            self.parsed.append(nlab_mistletoe.render(self.to_parse))
        elif self.mode:
            raise NLabSyntaxError(
                "The following belongs to an environment of type " +
                self.mode +
                " that was not closed: " +
                "\n".join(self.to_parse))
        if self.top_level:
            self.preamble.append("<span class=\"page_content_start\"></span>")
            self.parsed.append("<span class=\"page_content_end\"></span>")
        return self.preamble + self.parsed

# In same file to avoid issues with circular dependencies
class TheoremEnvironmentParser:
    theorem_environments = {
        "defn": ("Definition", "definition"),
        "definition": ("Definition", "definition"),
        "thm": ("Theorem", "theorem"),
        "theorem": ("Theorem", "theorem"),
        "prop": ("Proposition", "theorem"),
        "prpn": ("Proposition", "theorem"),
        "proposition": ("Proposition", "theorem"),
        "rmk": ("Remark", "definition"),
        "remark": ("Remark", "definition"),
        "cor": ("Corollary", "theorem"),
        "corollary": ("Corollary", "theorem"),
        "lem": ("Lemma", "theorem"),
        "lemma": ("Lemma", "theorem"),
        "notn": ("Notation", "definition"),
        "notation": ("Notation", "definition"),
        "terminology": ("Terminology", "definition"),
        "scholium": ("Scholium", "definition"),
        "conjecture": ("Conjecture", "theorem"),
        "conj": ("Conjecture", "theorem"),
        "example": ("Example", "definition"),
        "exercise": ("Exercise", "definition"),
        "statement": ("Statement", "theorem"),
        "assumption": ("Assumption", "theorem"),
        "assum": ("Assumption", "theorem"),
        "proof": ("Proof", "proof")
    }

    match_regex_new = re.compile(
        r"\\begin\{(" + "|".join(theorem_environments.keys()) + ")\}")

    match_regex_old = re.compile(
            r"\+-- \{: ((\.(num|un)_(defn|prop|remark|theorem|cor|example))" +
            "|(\.(proof)))\}")

    @classmethod
    def match_new(cls, line):
        match = cls.match_regex_new.match(line)
        if match is None:
            return None
        return match.group(1)

    @classmethod
    def match_old(cls, line):
        match = cls.match_regex_old.match(line)
        if match is None:
            return None
        return match.group(1)

    @classmethod
    def render_new(cls, theorem_environment, content):
        environment_regex_new = re.compile(
            r"\\begin\{" +
            theorem_environment +
            "\}(.*?)\\\end\{" +
            theorem_environment +
            "\}",
            re.DOTALL)
        content = environment_regex_new.match(content).group(1)
        rendered_content = "\n".join(
            Renderer(top_level = False).render(content))
        if rendered_content.startswith("<p>"):
            rendered_content = rendered_content[3:]
        if rendered_content.endswith("</p>"):
            rendered_content = rendered_content[:-4]
        label_regex = re.compile(r"\\label\{(.*?)\}")
        label_match = label_regex.search(rendered_content)
        if label_match:
            label = label_match.group(1)
            rendered_content = re.sub(label_regex, "", rendered_content)
        else:
            label = None
        return (
            "<div class=\"" +
            cls.theorem_environments[theorem_environment][1] +
            "_environment\"" +
            ((" id=\"" + label + "\">\n") if label else ">\n") +
            "<p><span class=\"" +
            cls.theorem_environments[theorem_environment][1] +
            "_environment\">" +
            cls.theorem_environments[theorem_environment][0] +
            "</span>\n" +
            rendered_content +
            "</p>\n</div>")

    @classmethod
    def render_old(cls, theorem_environment, content):
        if theorem_environment != ".proof":
            environment_regex_old = re.compile(
                r"\+-- \{: " +
                theorem_environment +
                "\}(.*?)=--",
                re.DOTALL)
        else:
            environment_regex_old = re.compile(
                r"\+-- \{: \.proof\}(.*?)=--",
                re.DOTALL)
        content = environment_regex_old.match(content).group(1)
        # Remove the environment heading
        content = re.sub(
            r"(######(.*?)######)(.*?)\n",
            lambda heading_match: heading_match.group(3) + "\n",
            content)
        content = re.sub(
            r"######(.*?)\n",
            "",
            content)
        rendered_content = "\n".join(
            Renderer(top_level = False).render(content))
        if rendered_content.startswith("<p>"):
            rendered_content = rendered_content[3:]
        if rendered_content.endswith("</p>"):
            rendered_content = rendered_content[:-4]
        label_regex = re.compile(r"\\label\{(.*?)\}")
        label_match = label_regex.search(rendered_content)
        if label_match:
            label = label_match.group(1)
            content = re.sub(label_regex, "", content)
        else:
            label = None
        if theorem_environment.startswith(".num_"):
            theorem_environment = theorem_environment[5:]
        elif theorem_environment.startswith(".un_"):
            theorem_environment = theorem_environment[4:]
        elif theorem_environment == ".proof":
            theorem_environment = theorem_environment[1:]
        return (
            "<div class=\"" +
            cls.theorem_environments[theorem_environment][1] +
            "_environment\"" +
            ((" id=\"" + label + "\">\n") if label else ">\n") +
            "<p><span class=\"" +
            cls.theorem_environments[theorem_environment][1] +
            "_environment\">" +
            cls.theorem_environments[theorem_environment][0] +
            "</span>\n" +
            rendered_content +
            "</p>\n</div>")

def lambda_handler(event, context):
    headers = dict()
    try:
        origin_header = event["headers"]["origin"]
        if ("nlab-pages.s3.us-east-2.amazonaws.com" in origin_header) or \
                ("ncatlab.org" in origin_header):
            headers["Access-Control-Allow-Origin"] = origin_header
            headers["Access-Control-Allow-Headers"] = "Content-Type"
            headers["Access-Control-Allow-Methods"] = "OPTIONS, PUT"
    except KeyError:
        pass
    if event["requestContext"]["http"]["method"] == "OPTIONS":
        if not headers:
            return {
                "isBase64Encoded": False,
                "statusCode": 200
            }
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers
        }
    event_body = json.loads(event["body"])
    try:
        rendered_source = "\n".join(Renderer().render(event_body["source"]))
        headers["Content-Type"] = "text/html; charset=utf-8"
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": rendered_source
        }
    except (NLabSyntaxError, NotYetSupportedError) as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": str(exception)
        }
    except Exception as exception:
        raise exception
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

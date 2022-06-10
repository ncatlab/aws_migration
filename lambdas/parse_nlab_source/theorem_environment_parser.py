import re

import nlab_mistletoe

_theorem_environments = {
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

_regex_new = re.compile(
    r"\\begin\{(" + "|".join(_theorem_environments.keys()) + ")\}")

_regex_old = re.compile(
        r"\+-- \{: \.(num|un)_(defn|prop|remark|theorem|cor|proof)\}")

def match_new(line):
    match = _regex_new.match(line)
    if match is None:
        return None
    return match.group(1)

def match_old(line):
    match = _regex_old.match(line)
    if match is None:
        return None
    return match.group(2)

def render_new(theorem_environment, content):
    regex = re.compile(
        r"\\begin\{" +
        theorem_environment +
        "\}(.*?)\\\end\{" +
        theorem_environment +
        "\}",
        re.DOTALL)
    content = regex.match(content).group(1)
    label_match = re.compile(r"\\label\{(.*?)\}").search(content)
    label = label_match.group(1) if label_match else None
    return (
        "<div class=\"" +
        _theorem_environments[theorem_environment][1] +
        "_environment\"" +
        ((" id=\"" + label + "\">\n") if label else ">\n") +
        "<h6>" + _theorem_environments[theorem_environment][0] + "</h6>\n" +
        nlab_mistletoe.render(content) +
        "</div>")

def render_old(theorem_environment, content):
    regex = re.compile(
        r"\+-- \{: \.(num|un)_" +
        theorem_environment +
        "\}(.*?)=--",
        re.DOTALL)
    content = regex.match(content).group(2)
    label_match = re.compile(r"\\label\{(.*?)\}").search(content)
    label = label_match.group(1) if label_match else None
    return (
        "<div class=\"" +
        _theorem_environments[theorem_environment][1] +
        "_environment\"" +
        ((" id=\"" + label + "\">\n") if label else ">\n") +
        "<h6>" + _theorem_environments[theorem_environment][0] + "</h6>\n" +
        nlab_mistletoe.render(content) +
        "</div>")

import glob
import json
import os
import random
import re
import string
import subprocess

_diagram_types = [ "tikz", "tikzcd", "xypic" ]
_tikz_library_regex = re.compile(r"(\\usetikzlibrary\{.*?\})")
_xymatrix_regex = re.compile(r"\\begin{(.*?)}(.*?)\\end{xymatrix}", re.DOTALL)
_blacklist = [
   r"\\def",
   r"\\loop",
   r"\\new",
   r"\\file",
   r"\\open",
   r"\\catcode",
   r"\\usepackage",
   r"\\if",
   r"\\read",
   r"\\repeat",
   r"\\closein",
   r"\\write",
   r"\\input",
   r"\\terminal",
   r"\\let",
   r"\\or",
   r"\\xdef",
   r"\\edef",
   r"\\global",
   r"\\gdef",
   r"\\globaldefs",
   r"\\dump",
   r"\\pausing",
   r"\\show",
   r"\\error",
   r"\\escape",
   r"\\include",
   r"\\immediate" ]
_blacklist_regex = re.compile("(" + "|".join(_blacklist) + ")")
_font_sizes = [
    "\\tiny",
    "\\scriptsize",
    "\\footnotesize",
    "\\small",
    "\\normalsize",
    "\\large",
    "\\Large",
    "\\LARGE",
    "\\huge",
    "\\Huge" ]

class BlacklistedException(Exception):
    def __init__(self, command):
        super().__init__()
        self.command = command

class PdfRenderingException(Exception):
    def __init__(self, message):
        super().__init__(message)

class SvgRenderingException(Exception):
    def __init__(self, message):
        super().__init__(message)

class XypicDocumentParametersException(Exception):
    def __init__(self, message):
        super().__init__(message)

def _check_against_blacklist(source):
    matches = re.search(_blacklist_regex, source)
    if matches is not None:
        raise BlacklistedException(matches.group(1))

def _diagram_id():
    return str(random.randint(10**8, (10**9) - 1))

def _extract_pdf_rendering_error(latex_output):
    error_description_begun = False
    error_description = []
    for output_line in latex_output.split("\n"):
        if output_line.strip().startswith("!"):
            error_description.append(output_line)
            error_description_begun = True
        elif output_line.strip().startswith("l.") and error_description_begun:
            try:
                identifier = output_line.strip().split(" ", 1)[1]
            except IndexError:
                break
            if identifier:
                error_description.append("Line: " + identifier)
            break
    return "\n".join(error_description)

def _extract_tikz_libraries(source):
    matches = re.search(_tikz_library_regex, source)
    if matches is None:
        return "", source
    libraries = [ matches.group(i) for i in range(1, matches.lastindex) ]
    with_libraries_removed = re.sub(_tikz_library_regex, "", source)
    return "\n".join(libraries), with_libraries_removed

def _parse_xypic_document_parameters(xypic_document_parameters):
    parameters = { "document_header_parameters": [ "12pt" ] }
    for parameter in xypic_document_parameters.split(","):
        split_at_equals = parameter.split("=")
        if len(split_at_equals) != 2:
            raise XypicDocumentParametersException(
                "The following xypic diagram parameter does not have the " +
                "expected format: {}".format(parameter))
        key = split_at_equals[0].strip()
        value = split_at_equals[1].strip()
        if key == "font":
            if value not in _font_sizes:
                raise XypicDocumentParametersException(
                    "The value {} of the xypic diagram parameter ".format(
                        value) +
                    "'font' is not recognised as a LaTeX font size")
            parameters["font_size"] = value
        elif key == "border":
            parameters["document_header_parameters"].append(parameter)
        else:
            raise XypicDocumentParametersException(
                "The key {} of the following xypic diagram parameter ".format(
                    key) +
                "is not recognised: {}".format(parameter))
    return parameters

def _extract_xypic_document_parameters(source):
    matches = re.search(
        _xymatrix_regex,
        source)
    start = matches.group(1)
    diagram = matches.group(2)
    if (start == "xymatrix"):
        parameters = {
            "document_header_parameters": ["12pt"]
        }
        diagram = "\\xymatrix@=5em{{{}}}".format(diagram)
        return parameters, diagram
    options_matches = re.search(
        r"\[(.*?)\]",
        start)
    if options_matches is None:
        parameters = {
            "document_header_parameters": ["12pt"]
        }
    else:
        parameters = _parse_xypic_document_parameters(options_matches.group(1))
        start = re.sub(r"\[(.*?)\]", "", start, count=1)
    diagram = "\\{}{{{}}}".format(start, diagram)
    return parameters, diagram

def _tikzcd_tex_source(source):
    with open("tikz_diagram_template", "r") as tikz_diagram_template_file:
        tikz_diagram_template = tikz_diagram_template_file.read()
    return string.Template(tikz_diagram_template).substitute(
        tikz_libraries = "\\usetikzlibrary{cd}",
        tikz_diagram = source)

def _tikz_tex_source(source):
    with open("tikz_diagram_template", "r") as tikz_diagram_template_file:
        tikz_diagram_template = tikz_diagram_template_file.read()
    libraries, with_libraries_removed = _extract_tikz_libraries(
        source)
    return string.Template(tikz_diagram_template).substitute(
        tikz_libraries = libraries,
        tikz_diagram = with_libraries_removed)

def _xypic_tex_source(source):
    document_parameters, source = _extract_xypic_document_parameters(source)
    try:
        font_size = document_parameters["font_size"]
    except KeyError:
        font_size = ""
    with open("xypic_diagram_template", "r") as xypic_diagram_template_file:
        xypic_diagram_template = xypic_diagram_template_file.read()
    return string.Template(xypic_diagram_template).substitute(
        document_parameters = ", ".join(
            document_parameters["document_header_parameters"]),
        font_size = font_size,
        xypic_diagram = source)

def _create_pdf(diagram_type, source, diagram_id):
    if diagram_type == "tikz":
        tex_source = _tikz_tex_source(source)
    elif diagram_type == "tikzcd":
        tex_source = _tikzcd_tex_source(source)
    else:
        tex_source = _xypic_tex_source(source)
    tex_source_file_name = "{}.tex".format(diagram_id)
    with open("/tmp/{}".format(tex_source_file_name), "w") as tex_source_file:
        tex_source_file.write(tex_source)
    try:
        pdf_subprocess = subprocess.run(
            [ "pdflatex", tex_source_file_name ],
            cwd = "/tmp",
            capture_output = True,
            timeout = 15)
    except subprocess.TimeoutExpired:
        raise PdfRenderingException("Timed out")
    if pdf_subprocess.returncode != 0:
        raise PdfRenderingException(
            _extract_pdf_rendering_error(pdf_subprocess.stdout.decode()))

def _create_svg(diagram_id):
    svg_subprocess = subprocess.run(
        [
            "pdftocairo",
            "{}.pdf".format(diagram_id),
            "{}.svg".format(diagram_id),
            "-svg",
            "-f",
            "1",
            "-l",
            "1"
        ],
        cwd = "/tmp",
        capture_output = True)
    if svg_subprocess.returncode != 0:
        raise SvgRenderingException(svg_subprocess.stderr.decode())
    with open("/tmp/{}.svg".format(diagram_id), "r") as svg_file:
        svg_diagram_lines = svg_file.read().splitlines()
    svg_diagram = "\n".join(svg_diagram_lines[1:])
    svg_diagram = svg_diagram.replace("glyph", diagram_id + "-glyph")
    svg_diagram = svg_diagram.replace(
        "id=\"clip",
        "id=\"" + diagram_id + "-clip")
    return svg_diagram.replace(
        "#clip",
        "#" + diagram_id + "-clip")

def _remove_diagram_files(diagram_id):
    for diagram_file in glob.glob("/tmp/{}*".format(diagram_id)):
        os.remove(diagram_file)

def create_diagram(diagram_type, source):
    diagram_id = _diagram_id()
    try:
        _create_pdf(diagram_type, source, diagram_id)
        return _create_svg(diagram_id)
    finally:
        _remove_diagram_files(diagram_id)

def _extract_diagram_type_and_source(event, headers):
    try:
        event_body = json.loads(event["body"])
    except json.JSONDecodeError:
        headers["Content-Type"] = "text/plain"
        return (
            {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": "Request body is invalid JSON"
            },
            None,
            None)
    try:
        return (
            None,
            event_body["type"],
            event_body["source"])
    except KeyError as exception:
        headers["Content-Type"] = "text/plain"
        return (
            {
                "isBase64Encoded": False,
                "statusCode": 400,
                "headers": headers,
                "body": "Missing parameter in request body: {}".format(
                    exception)
            },
            None,
            None)

def _handle_cors(event):
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
            return (
                {
                    "isBase64Encoded": False,
                    "statusCode": 200,
                },
                None)
        return (
            {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": headers
            },
            None)
    return None, headers

def lambda_handler(event, context):
    response, headers = _handle_cors(event)
    if response is not None:
        return response
    response, diagram_type, source = _extract_diagram_type_and_source(
        event, headers)
    if response is not None:
        return response
    if diagram_type not in _diagram_types:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": "Diagram type must be one of the following: {}". format(
                ", ".join(_diagram_types))
        }
    try:
        _check_against_blacklist(source)
    except BlacklistedException as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": (
                "Diagram source contains the following, which is not " +
                "permitted: {}".format(exception.command)
            )
        }
    try:
        svg_diagram = create_diagram(diagram_type, source)
    except PdfRenderingException as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": (
                "An error occurred when running pdflatex on the following " +
                "diagram.\n{}\n{}".format(
                    source,
                    exception)
            )
        }
    except SvgRenderingException as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": (
                "An error occurred when creating an SVG from a PDF for the " +
                "following diagram.\n{}\n{}".format(
                    source,
                    exception)
            )
        }
    except XypicDocumentParametersException as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": (
                "An error occurred when rendering the following " +
                "diagram.\n{}\nThe error was: {}".format(
                    source,
                    exception)
            )
        }
    except Exception as exception:
        raise exception
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": (
                "An unexpected error occurred when rendering the following " +
                "diagram.\n{}".format(source)
            )
        }
    headers["Content-Type"] = "image/svg+xml"
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": headers,
        "body": svg_diagram
    }


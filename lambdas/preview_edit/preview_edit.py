import json
import os
import re
import requests

_diagrams_root_url = os.environ["DIAGRAMS_ROOT_URL"]
_new_diagram_root_url = os.environ["NEW_DIAGRAM_ROOT_URL"]
_parse_source_root_url = os.environ["PARSE_SOURCE_ROOT_URL"]
_render_latex_root_url = os.environ["RENDER_LATEX_ROOT_URL"]
_render_page_root_url = os.environ["RENDER_PAGE_ROOT_URL"]

_latex_diagrams_regex = re.compile(
    r"(\\begin{tikzpicture}(.*?)\\end{tikzpicture})|" +
        r"(\\begin{tikzcd}(.*?)\\end{tikzcd})|" +
        r"(\\begin{xymatrix}(.*?)\\end{xymatrix})",
    re.DOTALL)

class FailedToRenderDiagramException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code

class FailedToParseException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code

class FailedToRenderException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code

class FailedToRenderLatexException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code

def _replace_diagram_source_with_img_tag(metadata, diagram_source_match):
    if diagram_source_match.group(1) is not None:
        diagram_type = "tikz"
        diagram = diagram_source_match.group(1)
    elif diagram_source_match.group(3) is not None:
        diagram_type = "tikzcd"
        diagram = diagram_source_match.group(3)
    elif diagram_source_match.group(5) is not None:
        diagram_type = "xypic"
        diagram = diagram_source_match.group(5)
    response = requests.post(
        _new_diagram_root_url,
        json = {
            "type": diagram_type,
            "source": diagram,
            "author": metadata["author"],
            "ip_address": metadata["ip_address"]
        }
    )
    if response.status_code != 200:
        raise FailedToRenderDiagramException(
            response.status_code,
            "An error occurred when trying to render the following " +
            "diagram.\n\n{}\n\nError: {}".format(
                diagram,
                response.text))
    diagram_id = response.text
    return "<img src=\"{}/{}\">".format(
        _diagrams_root_url,
        diagram_id)

def _render_diagrams(metadata, source):
    return re.sub(
        _latex_diagrams_regex,
        lambda match: _replace_diagram_source_with_img_tag(
            metadata,
            match),
        source)

def _render_page(source, page_name):
    response = requests.put(
        _parse_source_root_url,
        json = {
            "source": source
        })
    if response.status_code != 200:
        raise FailedToParseException(response.status_code, response.text)

    response = requests.put(
        _render_latex_root_url,
        json = {
            "source": response.text
        })
    if response.status_code != 200:
        raise FailedToRenderLatexException(response.status_code, response.text)

    response = requests.put(
        _render_page_root_url,
        json = {
            "page_name": page_name,
            "parsed_source": response.text
        })
    if response.status_code != 200:
        raise FailedToRenderException(response.status_code, response.text)
    return response.text

def _render_preview(metadata, source):
    page_name = metadata["page_name"]
    source_with_created_diagrams = _render_diagrams(metadata, source)
    return _render_page(source_with_created_diagrams, page_name)

def _render_preview_and_handle_errors(metadata, source, headers):
    try:
        rendered_page = _render_preview(
            metadata,
            source)
        headers["Content-Type"] = "text/html"
        print(rendered_page)
        return  {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": rendered_page
        }
    except (
            FailedToParseException,
            FailedToRenderDiagramException,
            FailedToRenderLatexException,
            FailedToRenderException) as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": exception.status_code,
            "headers": headers,
            "body": str(exception)
        }
    except Exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

def _extract_metadata_and_source(event, headers):
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
            {
                "page_name": event_body["page_name"],
                "author": event_body["author"],
                "ip_address": event["requestContext"]["http"]["sourceIp"]
            },
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
    response, metadata, source = \
        _extract_metadata_and_source(event, headers)
    if response is not None:
        return response
    return _render_preview_and_handle_errors(
        metadata,
        source,
        headers)

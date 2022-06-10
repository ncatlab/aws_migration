import json
import os
import requests
import string

_overall_name = os.environ["OVERALL_NAME"]
_root_url = os.environ["ROOT_URL"]
_home_page = os.environ["HOME_PAGE"]
_sanitise_root_url = os.environ["SANITISE_ROOT_URL"]
_forum_root_url = os.environ["FORUM_ROOT_URL"]

class FailedToSanitiseException(Exception):
    pass

def sanitise(parsed_source):
    response = requests.put(
        _sanitise_root_url,
        json = {
            "parsed_source": parsed_source
        })
    if response.status_code != 200:
        raise FailedToSanitiseException()
    return response.text

def render(page_name, content):
    with open("page_template", "r") as page_template_file:
        page_template = string.Template(
            page_template_file.read())
    return page_template.substitute(
        root_url = _root_url,
        home_page = _home_page,
        page_name = page_name,
        overall_name = _overall_name,
        body_content = content,
        forum_root_url = _forum_root_url)

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

def _extract_page_name_and_parsed_source(event, headers):
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
            event_body["page_name"],
            event_body["parsed_source"])
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

def lambda_handler(event, context):
    response, headers = _handle_cors(event)
    if response is not None:
        return response
    response, page_name, parsed_source = _extract_page_name_and_parsed_source(
        event, headers)
    if response is not None:
        return response
    try:
        rendered_page = render(page_name, sanitise(parsed_source))
        headers["Content-Type"] = "text/html; charset=utf-8"
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": rendered_page
        }
    except FailedToSanitiseException:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred when sanitising"
        }
    except Exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

import os
import requests
import string

_home_page = os.environ["HOME_PAGE"]
_overall_name = os.environ["OVERALL_NAME"]
_page_history_root_url = os.environ["PAGE_HISTORY_ROOT_URL"]
_root_url = os.environ["ROOT_URL"]

class NoHistoryException(Exception):
    pass

class UnexpectedError(Exception):
    pass

def _page_history(page_name):
    response = requests.get(
        "{}/{}".format(
            _page_history_root_url,
            page_name))
    if response.status_code == 404:
        raise NoHistoryException()
    elif response.status_code != 200:
        raise UnexpectedError()
    return response.json()

def _revision_list(page_name):
    page_history = _page_history(page_name)
    history_items = []
    for revision_number, revision_data in page_history.items():
        history_items.append(
            "<li>{}<br><span class=\"revision_details\">{}, by {}</span></li>".format(
                "<a class=\"revision\" href=\"../show/{}/{}\">Revision {}</a>".format(
                    page_name,
                    revision_number,
                    revision_number),
                revision_data["edit_time"],
                revision_data["author"])
        )
    return "<ul>\n" + "\n".join(reversed(history_items)) + "\n</ol>"

def render(page_name):
    with open("page_history_template", "r") as page_history_template_file:
        page_history_template = string.Template(
            page_history_template_file.read())
    return page_history_template.substitute(
        root_url = _root_url,
        home_page = _home_page,
        page_name = page_name,
        overall_name = _overall_name,
        revisions = _revision_list(page_name))

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
    page_name = event["pathParameters"]["page_name"]
    try:
        rendered_page = render(page_name)
    except NoHistoryException:
        if not headers:
            return  {
                "isBase64Encoded": False,
                "statusCode": 404
            }
        else:
            return  {
                "isBase64Encoded": False,
                "statusCode": 404,
                "headers": headers,
            }
    except Exception:
        if not headers:
            return  {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": {
                     "Content-Type": "text/plain"
                },
                "body": "An unexpected error occurred"
            }
        else:
            headers["Content-Type"] = "text/plain"
            return  {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": headers,
                "body": "An unexpected error occurred"
            }
    if not headers:
        headers = {
            "Content-Type": "text/html; charset=utf-8"
        }
    else:
        headers["Content-Type"] = "text/html; charset=utf-8"
    return  {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": headers,
        "body": rendered_page
    }

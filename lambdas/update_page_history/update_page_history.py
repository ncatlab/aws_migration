import boto3
import json
import os
import requests

_s3_client = boto3.client("s3")

_history_all_root_url = os.environ["HISTORY_ALL_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]
_render_page_history_root_url = os.environ["RENDER_PAGE_HISTORY_ROOT_URL"]

class FailedToRenderException(Exception):
    def __init__(self, message):
        super().__init__(message)

class NoHistoryException(Exception):
    pass

def _render_history_page(page_name):
    response = requests.put(
        "{}/{}".format(
            _render_page_history_root_url,
            page_name))
    if response.status_code == 404:
        raise NoHistoryException()
    elif response.status_code != 200:
        raise FailedToRenderException(response.text)
    return response.text

def _store(page_name, rendered_history_page):
    _s3_client.put_object(
        ACL = "public-read",
        Body = rendered_history_page.encode("utf-8"),
        Bucket = _pages_bucket_name,
        CacheControl = "no-cache",
        ContentType = "text/html",
        Key = "{}/{}".format(
            _history_all_root_url,
            page_name))

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
        rendered_history_page = _render_history_page(page_name)
        _store(page_name, rendered_history_page)
    except FailedToRenderException as exception:
        headers["Content-Type"] = "text/plain"
        return  {
            "isBase64Encoded": False,
            "statusCode": 502,
            "headers": headers,
            "body": str(exception)
        }
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
        return  {
            "isBase64Encoded": False,
            "statusCode": 200,
        }
    else:
        return  {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
        }

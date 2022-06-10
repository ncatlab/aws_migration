import boto3
import json
import os
import re
import string

_s3_client = boto3.client("s3")

_all_page_names_url = os.environ["ALL_PAGE_NAMES_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]

class NoSearchExpressionException(Exception):
    pass

def search(search_expression):
    all_page_names = _s3_client.get_object(
        Bucket = _pages_bucket_name,
        Key = _all_page_names_url)["Body"].read().decode("utf-8").split("\n")
    if not search_expression:
        raise NoSearchExpressionException()
    if search_expression[0] in string.ascii_letters:
        search_expression = "[{}|{}]{}".format(
            search_expression[0].lower(),
            search_expression[0].upper(),
            search_expression[1:])
    search_regex = re.compile(search_expression)
    return json.dumps([
        page_name for page_name in all_page_names if search_regex.search(
            page_name)])

def _handle_cors(event):
    headers = dict()
    try:
        origin_header = event["headers"]["origin"]
        if ("nlab-pages.s3.us-east-2.amazonaws.com" in origin_header) or \
                ("ncatlab.org" in origin_header):
            headers["Access-Control-Allow-Origin"] = origin_header
            headers["Access-Control-Allow-Headers"] = "Content-Type"
            headers["Access-Control-Allow-Methods"] = "OPTIONS, GET"
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
    search_expression = event["queryStringParameters"]["search_expression"]
    try:
        headers["Content-Type"] = "application/json; charset=utf-8"
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": search(search_expression)
        }
    except NoSearchExpressionException:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": "No search expression provided"
        }
    except Exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

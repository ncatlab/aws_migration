import boto3
import json
import os

_s3_client = boto3.client("s3")

_history_pages_root_url = os.environ["HISTORY_PAGES_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]

class NoHistoryException(Exception):
    pass

def latest_revision(page_name):
    list_response = _s3_client.list_objects_v2(
        Bucket = _pages_bucket_name,
        Prefix = "{}/{}".format(
            _history_pages_root_url,
            page_name))
    latest_revision_number = 0
    while True:
        try:
            list_response_contents = list_response["Contents"]
        except KeyError:
            raise NoHistoryException()
        for revision in list_response_contents:
            revision_number = int(revision["Key"].split("/")[-1])
            if revision_number > latest_revision_number:
                latest_revision_number = revision_number
        if not list_response["IsTruncated"]:
            return latest_revision_number
        list_response = _s3_client.list_objects_v2(
            Bucket = _pages_bucket_name,
            Prefix = "{}/{}".format(
                _history_pages_root_url,
                page_name),
            ContinuationToken = list_response["NextContinuationToken"])

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
    headers["Content-Type"] = "text/plain"
    page_name = event["pathParameters"]["page_name"]
    try:
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": str(latest_revision(page_name))
        }
    except NoHistoryException:
        del headers["Content-Type"]
        return {
            "isBase64Encoded": False,
            "statusCode": 404,
            "headers": headers
        }
    except Exception:
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

import boto3
import json
import os
import requests

_s3_client = boto3.client("s3")

_history_metadata_root_url = os.environ["HISTORY_METADATA_ROOT_URL"]
_latest_revision_root_url = os.environ["LATEST_REVISION_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]

class NoHistoryException(Exception):
    pass

class UnexpectedError(Exception):
    pass

def _latest_revision(page_name):
    response = requests.get(
        "{}/{}".format(
            _latest_revision_root_url,
            page_name))
    if response.status_code == 404:
        raise NoHistoryException()
    elif response.status_code != 200:
        raise UnexpectedError()
    return int(response.text)

def _revision_data(page_name, revision_number):
    revision_metadata = json.loads(
        _s3_client.get_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}/{}".format(
                _history_metadata_root_url,
                page_name,
                revision_number))["Body"].read())
    return {
        "author": revision_metadata["author"],
        "edit_time": revision_metadata["edit_time"]
    }

def _revisions(page_name):
    latest_revision = _latest_revision(page_name)
    return {
        i: _revision_data(page_name, i) for i in range(1, latest_revision + 1)
    }


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
    page_name = event["pathParameters"]["page_name"]
    try:
        revisions = _revisions(page_name)
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
    except Exception as exception:
        raise exception
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
            "Content-Type": "application/json"
        }
    else:
        headers["Content-Type"] = "application/json"
    return  {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(revisions, indent=2)
    }

import boto3
import datetime
import json
import os
import requests

_s3_client = boto3.client("s3")

_create_diagram_root_url = os.environ["CREATE_DIAGRAM_ROOT_URL"]
_diagrams_sources_root_url = os.environ["DIAGRAMS_SOURCES_ROOT_URL"]
_diagrams_history_root_url = os.environ["DIAGRAMS_HISTORY_ROOT_URL"]
_diagrams_history_metadata_root_url = os.environ[
    "DIAGRAMS_HISTORY_METADATA_ROOT_URL"]
_diagrams_history_sources_root_url = os.environ[
    "DIAGRAMS_HISTORY_SOURCES_ROOT_URL"]
_diagrams_root_url = os.environ["DIAGRAMS_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]

class FailedToRenderDiagramException(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code

def _diagram_id():
    return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

def _edit_time():
    return datetime.datetime.utcnow().strftime("%B %d, %Y at %H:%M:%S (UTC)")

def _render_diagram(request_body):
    response = requests.put(
        _create_diagram_root_url,
        json = request_body)
    if response.status_code != 200:
        raise FailedToRenderDiagramException(
            response.status_code,
            response.text)
    return response.text

def _store_current(diagram_id, rendered_diagram, source):
    _s3_client.put_object(
        ACL = "public-read",
        Body = rendered_diagram.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "image/svg+xml",
        Key = "{}/{}".format(_diagrams_root_url, diagram_id))
    _s3_client.put_object(
        ACL = "public-read",
        Body = source.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "text/plain",
        Key = "{}/{}".format(_diagrams_sources_root_url, diagram_id))
    return diagram_id

def _store_in_history(diagram_id, rendered_diagram, metadata_and_source):
    _s3_client.put_object(
        ACL = "public-read",
        Body = rendered_diagram.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "image/svg+xml",
        Key = "{}/{}/1".format(
            _diagrams_history_root_url,
            diagram_id))
    _s3_client.put_object(
        ACL = "public-read",
        Body = metadata_and_source["source"].encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "text/plain",
        Key = "{}/{}/1".format(
            _diagrams_history_sources_root_url,
            diagram_id))
    metadata = json.dumps(
        {
            "author": metadata_and_source["author"],
            "edit_time": _edit_time(),
            "ip_address": metadata_and_source["ip_address"],
            "type": metadata_and_source["type"]
        },
        indent = 2)
    _s3_client.put_object(
        Body = metadata.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "application/json",
        Key = "{}/{}/1".format(
            _diagrams_history_metadata_root_url,
            diagram_id))

def _store(rendered_diagram, metadata_and_source):
    diagram_id = _diagram_id()
    try:
        _store_current(
            diagram_id,
            rendered_diagram,
            metadata_and_source["source"])
        _store_in_history(diagram_id, rendered_diagram, metadata_and_source)
        return diagram_id
    except Exception as exception:
        try:
            _remove_from_history(diagram_id)
            _remove_as_current(diagram_id)
        except Exception as clean_up_exception:
            raise clean_up_exception from exception
        raise exception

def _remove_from_history(diagram_id):
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/1".format(
            _diagrams_history_root_url,
            diagram_id))
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/1".format(
            _diagrams_history_sources_root_url,
            diagram_id))
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/1".format(
            _diagrams_history_metadata_root_url,
            diagram_id))

def _remove_as_current(diagram_id):
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}".format(
            _diagrams_root_url,
            diagram_id))
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}".format(
            _diagrams_sources_root_url,
            diagram_id))

def _render_and_store_diagram(headers, metadata_and_source):
    source = metadata_and_source["source"]
    try:
        rendered_diagram = _render_diagram({
            "type": metadata_and_source["type"],
            "source": source
        })
        diagram_id = _store(rendered_diagram, metadata_and_source)
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers,
            "body": str(diagram_id)
        }
    except FailedToRenderDiagramException as exception:
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
            None)
    try:
        return (
            None,
            {
                "type": event_body["type"],
                "source": event_body["source"],
                "author": event_body["author"],
                "ip_address": event["requestContext"]["http"]["sourceIp"]
            }
        )
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
            None)

def _handle_cors(event):
    headers = dict()
    try:
        origin_header = event["headers"]["origin"]
        if ("nlab-pages.s3.us-east-2.amazonaws.com" in origin_header) or \
                ("ncatlab.org" in origin_header):
            headers["Access-Control-Allow-Origin"] = origin_header
            headers["Access-Control-Allow-Headers"] = "Content-Type"
            headers["Access-Control-Allow-Methods"] = "OPTIONS, POST"
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
    response, metadata_and_source = _extract_metadata_and_source(event, headers)
    if response is not None:
        return response
    return _render_and_store_diagram(headers, metadata_and_source)

import boto3
import botocore
import datetime
import json
import os
import pathlib
import random
import re
import requests
import urllib.parse

_s3_client = boto3.client("s3")
_cloudfront_client = boto3.client("cloudfront")

_cloudfront_distribution_id = os.environ["CLOUDFRONT_DISTRIBUTION_ID"]
_diagrams_root_url = os.environ["DIAGRAMS_ROOT_URL"]
_history_metadata_root_url = os.environ["HISTORY_METADATA_ROOT_URL"]
_history_pages_root_url = os.environ["HISTORY_PAGES_ROOT_URL"]
_history_sources_root_url = os.environ["HISTORY_SOURCES_ROOT_URL"]
_latest_revision_root_url = os.environ["LATEST_REVISION_ROOT_URL"]
_max_registered_seconds = int(os.environ["MAX_REGISTERED_SECONDS"])
_new_diagram_root_url = os.environ["NEW_DIAGRAM_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]
_pages_root_url = os.environ["PAGES_ROOT_URL"]
_parse_source_root_url = os.environ["PARSE_SOURCE_ROOT_URL"]
_render_latex_root_url = os.environ["RENDER_LATEX_ROOT_URL"]
_render_page_root_url = os.environ["RENDER_PAGE_ROOT_URL"]
_sources_root_url = os.environ["SOURCES_ROOT_URL"]

_last_check_time = datetime.datetime.now()
_latex_diagrams_regex = re.compile(
    r"(\\begin{tikzpicture}(.*?)\\end{tikzpicture})|" +
        r"(\\begin{tikzcd}(.*?)\\end{tikzcd})|" +
        r"(\\begin{xymatrix}(.*?)\\end{xymatrix})",
    re.DOTALL)

_root_submit_path = "/tmp/submitted"
pathlib.Path(_root_submit_path).mkdir(exist_ok = True)

class AuthorSyntaxException(Exception):
    def __init__(self, message):
        super().__init__(message)

class EditConflictException(Exception):
    pass

class FailedToCleanUpException(Exception):
    pass

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

def _edit_time():
    return datetime.datetime.utcnow().strftime("%B %d, %Y at %H:%M:%S (UTC)")

def _remove_too_old_submits():
    global _last_check_time
    now = datetime.datetime.now()
    if (now - _last_check_time).seconds > _max_registered_seconds:
        for filename in os.listdir(_root_submit_path):
            submit_time = datetime.datetime.fromtimestamp(os.path.getmtime(
                "{}/{}".format(_root_submit_path, filename)))
            if (now - submit_time).seconds > _max_registered_seconds:
                os.remove("{}/{}".format(_root_submit_path, filename))
    _last_check_time = now

def _validate(revision_metadata):
    if len(revision_metadata["author"]) > 100:
        raise AuthorSyntaxException(
            "At most 100 characters can be used in an author name")

def _register_submit(page_name, revision_number):
    try:
        _s3_client.head_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}/{}".format(
                _history_pages_root_url,
                page_name,
                revision_number))
        raise EditConflictException()
    except _s3_client.exceptions.ClientError:
        pass
    # The following, being backed by a filesystem, is a rigorous check,
    # but only works over the lifetime of the lambda environment, i.e. a
    # possibly relatively short period (the order of minutes) of time; it
    # is for this reason that the above check is also needed
    try:
        pathlib.Path("{}/{}-{}".format(
            _root_submit_path,
            revision_number,
            page_name)).touch(exist_ok = False)
    except FileExistsError:
        raise EditConflictException()

def _unregister_submit(page_name, revision_number):
    os.remove("{}/{}-{}".format(
        _root_submit_path,
        revision_number,
        page_name))

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
    return "\n<img src=\"{}/{}\">".format(
        _diagrams_root_url,
        diagram_id)

def _render_diagrams(revision_metadata, source):
    return re.sub(
        _latex_diagrams_regex,
        lambda match: _replace_diagram_source_with_img_tag(
            revision_metadata,
            match),
        source)

def _store_in_history(revision_metadata, rendered_page, source):
    _s3_client.put_object(
        ACL = "public-read",
        Body = rendered_page.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "text/html",
        Key = "{}/{}/{}".format(
            _history_pages_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))
    _s3_client.put_object(
        ACL = "public-read",
        Body = source.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "text/plain; charset=utf-8",
        Key = "{}/{}/{}".format(
            _history_sources_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))
    metadata = json.dumps(
        {
            "author": revision_metadata["author"],
            "edit_time": _edit_time(),
            "ip_address": revision_metadata["ip_address"]
        },
        indent = 2)
    _s3_client.put_object(
        Body = metadata.encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "application/json",
        Key = "{}/{}/{}".format(
            _history_metadata_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))

def _remove_from_history(revision_metadata):
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/{}".format(
            _history_pages_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/{}".format(
            _history_sources_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))
    _s3_client.delete_object(
        Bucket = _pages_bucket_name,
        Key = "{}/{}/{}".format(
            _history_metadata_root_url,
            revision_metadata["page_name"],
            revision_metadata["revision_number"]))

def _remove_as_current(page_name):
    response = requests.get(
        "{}/{}".format(
            _latest_revision_root_url,
            page_name))
    if response.status_code == 404:
        _s3_client.delete_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}".format(
                _pages_root_url,
                page_name))
        _s3_client.delete_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}".format(
                _sources_root_url,
                page_name))
        return
    elif response.status_code != 200:
        raise FailedToCleanUpException()
    previous_revision_number = response.text
    previous_page = _s3_client.get_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}/{}".format(
                _history_pages_root_url,
                page_name,
                previous_revision_number))["Body"].read().decode("utf-8")
    previous_source = _s3_client.get_object(
            Bucket = _pages_bucket_name,
            Key = "{}/{}/{}".format(
                _history_sources_root_url,
                page_name,
                previous_revision_number))["Body"].read().decode("utf-8")
    _store_as_current(page_name, previous_page, previous_source)

def _store_as_current(page_name, rendered_page, source):
    _s3_client.put_object(
        ACL = "public-read",
        Body = rendered_page.encode("utf-8"),
        Bucket = _pages_bucket_name,
        CacheControl = "no-cache",
        ContentType = "text/html",
        Key = "{}/{}".format(_pages_root_url, page_name))
    """
    _cloudfront_client.create_invalidation(
        DistributionId = _cloudfront_distribution_id,
        InvalidationBatch = {
            "Paths": {
                "Quantity": 1,
                "Items": [ "/{}/{}".format(
                    _pages_root_url,
                    urllib.parse.quote(page_name)) ]
            },
            "CallerReference": str(random.randrange(1, 10**6))
        }
    )
    """
    _s3_client.put_object(
        ACL = "public-read",
        Body = source,
        Bucket = _pages_bucket_name,
        CacheControl = "no-cache",
        ContentType = "text/plain; charset=utf-8",
        Key = "{}/{}".format(_sources_root_url, page_name))
    """
    _cloudfront_client.create_invalidation(
        DistributionId = _cloudfront_distribution_id,
        InvalidationBatch = {
            "Paths": {
                "Quantity": 1,
                "Items": [ "/{}/{}".format(
                    _sources_root_url,
                    urllib.parse.quote(page_name)) ]
            },
            "CallerReference": str(random.randrange(1, 10**6))
        }
    )
    """

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

def store(revision_metadata, source):
    _validate(revision_metadata)
    page_name = revision_metadata["page_name"]
    source_with_created_diagrams = _render_diagrams(revision_metadata, source)
    rendered_page = _render_page(source_with_created_diagrams, page_name)
    revision_number = revision_metadata["revision_number"]
    _register_submit(page_name, revision_number)
    try:
        if "sandbox" not in page_name.lower():
            _store_in_history(
                revision_metadata,
                rendered_page,
                source_with_created_diagrams)
        _store_as_current(
            page_name,
            rendered_page,
            source_with_created_diagrams)
    except Exception as exception:
        try:
            _remove_from_history(revision_metadata)
            _remove_as_current(page_name)
            _unregister_submit(page_name, revision_number)
        except Exception as clean_up_exception:
            raise clean_up_exception from exception
        raise exception
    _remove_too_old_submits()

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

def _extract_revision_metadata_and_source(event, headers):
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
                "revision_number": event_body["revision_number"],
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

def _render_store_and_handle_errors(revision_metadata, source, headers):
    try:
        store(
            revision_metadata,
            source)
    except AuthorSyntaxException as exception:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 400,
            "headers": headers,
            "body": str(exception)
        }
    except EditConflictException:
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 409,
            "headers": headers,
            "body": (
                "Revision {} of this page already exists. You will need to " +
                "manually merge your changes with those made in that edit " +
                "and any subsequent ones.\n\nSave the source of the page " +
                "as it is after your edits, fetch the source " +
                "of the latest edit, and merge the two (you may wish to use " +
                "a tool such as git or vimdiff for this), submitting that " +
                "merged source").format(revision_metadata["revision_number"])
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
    except Exception as exception:
        raise exception
        headers["Content-Type"] = "text/plain"
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": headers,
            "body": "An unexpected error occurred"
        }

def lambda_handler(event, context):
    response, headers = _handle_cors(event)
    if response is not None:
        return response
    response, revision_metadata, source = \
        _extract_revision_metadata_and_source(event, headers)
    if response is not None:
        return response
    response = _render_store_and_handle_errors(
        revision_metadata,
        source,
        headers)
    if response is not None:
        return response
    if not headers:
        return  {
            "isBase64Encoded": False,
            "statusCode": 200,
        }
    else:
        return  {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": headers
        }

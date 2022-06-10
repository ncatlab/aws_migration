import boto3
import os

_s3_client = boto3.client("s3")

_all_page_names_url = os.environ["ALL_PAGE_NAMES_URL"]
_pages_root_url = os.environ["PAGES_ROOT_URL"]
_pages_bucket_name = os.environ["PAGES_BUCKET_NAME"]

def _all_page_names():
    page_names = []
    list_response = _s3_client.list_objects_v2(
        Bucket = _pages_bucket_name,
        Prefix = _pages_root_url)
    while True:
        for page in list_response["Contents"]:
            page_name = page["Key"].split("/")[-1]
            page_names.append(page_name)
        if not list_response["IsTruncated"]:
            break
        list_response = _s3_client.list_objects_v2(
            Bucket = _pages_bucket_name,
            Prefix = _pages_root_url,
            ContinuationToken = list_response["NextContinuationToken"])
    return page_names

def _update_list_of_all_pages(page_names):
    _s3_client.put_object(
        Body = "\n".join(page_names).encode("utf-8"),
        Bucket = _pages_bucket_name,
        ContentType = "text/plain",
        Key = _all_page_names_url)

def lambda_handler(event, context):
    page_names = _all_page_names()
    _update_list_of_all_pages(page_names)

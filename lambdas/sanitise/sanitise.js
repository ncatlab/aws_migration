const DOMPurify = require('isomorphic-dompurify');

function handle_cors(event) {
    headers = {}
    if (event.headers && event.headers["origin"]) {
        let origin_header = event.headers.origin
        if (origin_header.includes("nlab-pages.s3.us-east-2.amazonaws.com") ||
                origin_headers.includes("ncatlab.org")) {
            headers["Access-Control-Allow-Origin"] = origin_header
            headers["Access-Control-Allow-Headers"] = "Content-Type"
            headers["Access-Control-Allow-Methods"] = "OPTIONS, PUT"
        }
    }
    if (event.requestContext.http.method == "OPTIONS") {
        if (!headers) {
             return [
		{
                    "isBase64Encoded": false,
                    "statusCode": 200
                },
		null ]
        }
        return [
	    {
                "isBase64Encoded": false,
                "statusCode": 200,
                "headers": headers
            },
            null ]
    }
    return [ null, headers]
}

function extract_parsed_source(event) {
    try {
        var event_body = JSON.parse(event.body)
    } catch (error) {
        headers["Content-Type"] = "text/plain"
        return [
	    {
                isBase64Encoded: false,
                statusCode: 400,
                headers: headers,
                body: "Request body is not valid JSON"
            },
	    null ]
    }
    if (event_body["parsed_source"]) {
        return [ null, event_body.parsed_source ]
    }
    headers["Content-Type"] = "text/plain"
    return [
        {
            isBase64Encoded: false,
            statusCode: 400,
            headers: headers,
            body: "Request body does not contain the parameter 'parsed_source'"
        },
	null ]
}

exports.handler = async (event) => {
    let [ cors_response, headers ] = handle_cors(event)
    if (cors_response) {
        return cors_response
    }
    let [ response, parsed_source ] = extract_parsed_source(event)
    if (response) {
        return response
    }
    try {
        var sanitised = DOMPurify.sanitize(parsed_source)
    } catch (error) {
        headers["Content-Type"] = "text/plain"
        return {
            isBase64Encoded: false,
            statusCode: 500,
            headers: headers,
            body: "An unexpected error occurred"
        }
    }
    headers["Content-Type"] = "text/html; charset=utf-8"
    return {
        isBase64Encoded: false,
        statusCode: 200,
        headers: headers,
        body: sanitised
    }
}

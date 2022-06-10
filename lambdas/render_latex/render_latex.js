const DOMPurify = require('isomorphic-dompurify')
const katex = require('katex')
const html_parser = require('node-html-parser')

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

function extract_source(event) {
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
    if (event_body["source"]) {
        return [ null, event_body.source ]
    }
    headers["Content-Type"] = "text/plain"
    return [
        {
            isBase64Encoded: false,
            statusCode: 400,
            headers: headers,
            body: "Request body does not contain the parameter 'source'"
        },
	null ]
}

function render_latex(source) {
    var html_source = html_parser.parse(source)
    html_source.querySelectorAll(".latex").forEach(latex_source_span => {
        var display_mode = false
        if (latex_source_span.getAttribute("data-display-mode")) {
            display_mode = true
        }
        latex_source_span.innerHTML = katex.renderToString(
            latex_source_span.getAttribute("data-latex"),
            {
                displayMode: display_mode,
                throwOnError: true
            }
        )
    })
    return html_source.innerHTML
}

exports.handler = async (event) => {
    let [ cors_response, headers ] = handle_cors(event)
    if (cors_response) {
        return cors_response
    }
    let [ response, source ] = extract_source(event)
    if (response) {
        return response
    }
    try {
        var rendered = render_latex(source)
    } catch (error) {
        headers["Content-Type"] = "text/plain; charset=utf-8"
        if (error instanceof katex.ParseError) {
            console.log(error)
            let error_message = DOMPurify.sanitize(error.message)
            return {
                isBase64Encoded: false,
                statusCode: 400,
                headers: headers,
                body: error_message
            }
        }
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
        body: rendered
    }
}

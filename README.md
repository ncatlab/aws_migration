Code for proposed AWS migration
===============================

Included here is all the source code for the AWS lambdas that were written for the migration, and all frontend javascript and CSS files. Various other bits of infrastructure, small bits of code, and tests were set up in AWS which are not included here; also not included are various scripts which were used to migrate page sources.

The architecture was as follows.

* All HTML pages served statically from an S3 bucket. This static website could be accessed directly at an AWS-generated root URL.
* A caching layer in AWS Cloudfront in front of this static website.
* All server-side processing provided via AWS Lambdas ('functions as a service') firing as required. Most of these were written in Python, but some were written in NodeJS. The AWS lambda for creating LaTeX diagrams was run in a Docker container created for this purpose (in particular, with LaTeX installed with appropriate security settings); all others were simple ZIPs. All of the lambdas were served as micro-services via AWS API Gateway endpoints (in particular, the software was able to be completely controlled via API, without a user interface).
* DNS was handled in AWS Route 53.
* SSL certification was handled in the AWS Certificate Manager (with automatic updating)
* No databases, traditional servers, or reverse proxies (nginx or similar). AWS lambdas have enough (short-lived) state to be able to handle concurrency issues.
* Essentially nothing remained from the original Instiki software; a little remained of Python code written from 2018 onwards, but most of this had been rwritten too. Even the CSS files were heavily reworked and simplified.

Some particular points of note design-wise (there were many other changes too):

* A preview functionality was added for use before submitting an edit. Edits themselves were immutable (no 30 minute window for making changes after an edit as in the old software).
* Context menus, page includes, and redirects were all now handled client-side.
* Editing of pages was completely synchronous: no pages ever needed to be edited as a consequence of editing one.
* LaTeX diagrams were made immutable, speeding up page processing.
* Page editing syntax was tightened and in some cases improved to something more concise and readable: in particular, old theorem environment and table of contents syntax was removed (leaving only the post-2018-ish LaTeX-like syntax), and context menu syntax was replaced.
* Security was handled carefully: pages had tight Content Security Policies, HTML sanitisation was thoroughly applied; each AWS lambda was isolated from all others, etc.

Everything is made available without any restrictions whatsoever, except that it is not permitted to override this unrestrictedness.

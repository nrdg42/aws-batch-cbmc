# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""ClientError exception parsing and handling methods."""

def response(exc):
    """Response attribute containing REST HTTP headers for the request
    generating the ClientError exception."""

    try:
        return exc.response
    except (KeyError, AttributeError):
        return None

def code(exc):
    """ClientError exception error code."""

    try:
        return exc.response['Error']['Code']
    except (KeyError, AttributeError):
        return None

def message(exc):
    """ClientError exception error message."""

    try:
        return exc.response['Error']['Message']
    except (KeyError, AttributeError):
        return None

def is_nosuchbucket(exc):
    """ClientError is NoSuchBucket."""

    return code(exc) == 'NoSuchBucket'

def is_bucketnotfound(exc):
    """ClientError is BucketNotFound."""

    return code(exc) == 'BucketNotFound'

def is_bucketalreadyexists(exc):
    """ClientError is "BucketAlreadyExists."""

    return code(exc) == 'BucketAlreadyExists'

def is_not_found(exc):
    """ClientError is 404 (NotFound)."""

    return code(exc) == '404'

def is_forbidden(exc):
    """ClientError is 403 (AccessDenied)."""

    return code(exc) == '403'

if __name__ == "__main__":
    print(code(None))

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Locks to control the dependencies of a CBMC job in AWS Batch."""

import re
import sys

import boto3

import s3

################################################################

def parse_bound(bound):
    """Parse a bound of the form [wd][xh][ym][zs] into seconds"""

    if bound is None:
        return sys.maxsize

    bnd = re.sub(r'\s+', "", bound)
    match = re.match('^(([0-9]+)d)?(([0-9]+)h)?(([0-9]+)m)?(([0-9]+)s)?$', bnd)
    if not match:
        raise LockException("Can't parse time bound: {}".format(bound))

    day = match.group(2) or 0
    hour = match.group(4) or 0
    minute = match.group(6) or 0
    second = match.group(8) or 0

    result = int(day)
    result = result*24 + int(hour)
    result = result*60 + int(minute)
    result = result*60 + int(second)

    return result

################################################################

class LockException(Exception):
    """Exception thrown by Lock methods."""

    def __init__(self, msg):
        super(LockException, self).__init__()
        self.message = msg

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

################################################################

BUILD = 'build.txt'
PROPERTY = 'property.txt'
COVERAGE = 'coverage.txt'
REPORT = 'report.txt'
LOCKS = [BUILD, PROPERTY, COVERAGE, REPORT]

class Lock:
    """A lock to control CBMC job dependencies."""

    def __init__(self, path, region):

        if not s3.is_path(path):
            raise LockException("Can't parse name as a bucket or an object: {}"
                                .format(path))
        self.bucket = s3.bucket_name(path)
        self.prefix = s3.key_name(path)
        self.locks = LOCKS
        self.client = boto3.client('s3', region_name=region)
        if not s3.bucket_exists(self.bucket, client=self.client):
            raise LockException("Bucket does not exist: {}".format(self.bucket))

    def get_lock_set(self):
        """The set of locks mantained."""

        return self.locks

    def lock_path(self, lock):
        """The object name for a lock"""

        if not self.prefix:
            return "{}/{}".format(self.bucket, lock)
        return "{}/{}/{}".format(self.bucket, self.prefix, lock)

    def validate_lock(self, lock):
        """Validate that lock is a known lock."""

        if lock not in self.locks:
            raise LockException("Unknown lock: {}".format(lock))


    def set(self, lock):
        """Set lock"""

        self.validate_lock(lock)
        s3.create_object(self.lock_path(lock), client=self.client)

    def unset(self, lock):
        """Unset lock"""

        self.validate_lock(lock)
        s3.delete_object(self.lock_path(lock), client=self.client)

    def is_set(self, lock):
        """Test if lock is set"""

        self.validate_lock(lock)
        return s3.object_exists(self.lock_path(lock), client=self.client)

    def is_unset(self, lock):
        """Test is lock is unset"""

        self.validate_lock(lock)
        return not s3.object_exists(self.lock_path(lock), client=self.client)

    def wait_for_set(self, lock, interval=15, bound=None):
        """Wait for lock to be set"""

        self.validate_lock(lock)
        attempts = (parse_bound(bound) // interval) + 1
        s3.wait_for_object(self.lock_path(lock), client=self.client,
                           interval=interval, attempts=attempts)

    def wait_for_unset(self, lock, interval=15, bound=None):
        """Wait for lock to be unset"""

        self.validate_lock(lock)
        attempts = (parse_bound(bound) // interval) + 1
        s3.wait_for_no_object(self.lock_path(lock), client=self.client,
                              interval=interval, attempts=attempts)

################################################################

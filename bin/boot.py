#!/usr/bin/env python3

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Copy cbmc-batch package from S3 and launch it"""

import json

import options
import package

def boot():
    """Copy cbmc-batch package from S3 and launch it"""
    opts = options.docker_options()
    print("Booting with options " + json.dumps(opts))

    package.copy('cbmc-batch', opts['pkgbucket'], opts['batchpkg'])
    package.install('cbmc-batch', opts['batchpkg'], 'cbmc-batch')
    package.launch('cbmc-batch', 'docker.py', ['--jsons', json.dumps(opts)])

if __name__ == "__main__":
    boot()

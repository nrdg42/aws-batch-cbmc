# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json

class Snapshot():
    def __init__(self, string=None, filename=None):
        # snapshot is defined by a json string or json file
        if string is None:
            if filename is None:
                raise UserWarning("No string or filename given for snapshot.")
            with open(filename) as handle:
                string = handle.read()
        self.snapshot = json.loads(string)

    def get_param(self, name=None):
        if name is None:
            return self.snapshot['parameters']
        return self.snapshot['parameters'].get(name)

    def get_cbmc(self):
        return self.snapshot.get('cbmc')

    def get_viewer(self):
        return self.snapshot.get('viewer')

    def get_batch(self):
        return self.snapshot.get('batch')

    def get_lambda(self):
        return self.snapshot.get('lambda')

    def get_docker(self):
        return self.snapshot.get('docker')

    def get_templates(self):
        return self.snapshot.get('templates')

    def get_parameter(self, name):
        return self.snapshot['parameters'][name]

    def update_snapshotid(self, string):
        self.snapshot['parameters']['SnapshotID'] = string

    def update_imagetagsuffix(self, string):
        self.snapshot['parameters']['ImageTagSuffix'] = string

    def write(self, filename):
        with open(filename, 'w') as handle:
            json.dump(self.snapshot, handle, indent=2)

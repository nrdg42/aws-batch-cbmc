# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import json

class Secrets():
    def __init__(self, session):
        self.session = session
        self.client = session.client('secretsmanager')

    def get_secret_id(self, secret_id):
        """ Return the secret associated with a secret id. """
        return self.client.get_secret_value(SecretId=secret_id)

    def get_secret_value(self, secret_id):
        """ Return the key-value pair in a secret that is a singleton list of key-value pairs. """

        secret = self.get_secret_id(secret_id)
        secretstring = secret['SecretString']

        secretpairs = json.loads(secretstring)
        assert len(secretpairs) == 1
        secretpair = secretpairs[0]

        keys = secretpair.keys()
        assert len(keys) == 1
        key = list(keys)[0]

        return (key, secretpair[key])

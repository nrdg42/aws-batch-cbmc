# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from timeit import default_timer

class Timer(object):

    def __init__(self, msg):
        self.msg = msg
        self.start()

    def start(self):
        print "Start: " + self.msg
        self.start = default_timer()

    def end(self):
        end = default_timer()
        print "End: " + self.msg + " (" + str(end - self.start) + " seconds)"

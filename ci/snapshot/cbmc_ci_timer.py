# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from timeit import default_timer

class Timer:

    def __init__(self, msg):
        self.msg = msg
        self.start()

    def start(self):
        print("Start: {}".format(self.msg))
        self.start_time = default_timer()

    def end(self):
        end_time = default_timer()
        print("End: {} ({} seconds)".format(self.msg,
                                            end_time - self.start_time))

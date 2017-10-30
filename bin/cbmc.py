# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Run CBMC"""

from pprint import pprint
import json

import clienterror
from batch import Batch

################################################################

class CBMCException(Exception):
    """Exception thrown by CBMC methods."""

    def __init__(self, msg):
        super(CBMCException, self).__init__()
        self.message = msg

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

################################################################

DEBUGGING = True

def abort(msg1, msg2=None, data=None, verbose=False):
    """Abort an CBMC method with debugging information."""
    code = clienterror.code(data)
    msgs = [msg1]
    if code is not None:
        msgs.append(" ({})".format(code))
    if msg2 is not None:
        msgs.append(": {}".format(msg2))
    msg = ''.join(msgs)
    if verbose or DEBUGGING:
        print("CBMC Exception: {}".format(msg))
        pprint(clienterror.response(data) or data)
    raise CBMCException(msg)

################################################################

class CBMC:
    """A running instance of CBMC"""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods

    def __init__(self, opts, quiet=True):
        self.srcdir = opts['srcdir']
        self.wsdir = opts['wsdir']
        self.outdir = opts['outdir']
        self.srcbucket = opts['srcbucket']
        self.wsbucket = opts['wsbucket']
        self.outbucket = opts['outbucket']
        self.jobname = opts['jobname']
        self.jobdef = opts['jobdef']
        self.jobqueue = opts['jobqueue']
        self.quiet = quiet
        self.cbmcflags = opts['cbmcflags']
        self.cflags = opts['cflags']
        self.ldflags = opts['ldflags']
        self.goto = opts['goto']
        self.build = opts['build']
        self.property = opts['property']
        self.coverage = opts['coverage']
        self.report = opts['report']

        self.opts = opts
        self.batch = Batch(
            jobname=self.jobdef, queuename=self.jobqueue,
            region=opts['region'])

    def launch_build(self, flags=None, dependson=None):
        """Build the goto program from source"""

        flags = flags or []
        jobname = "{}-build".format(self.jobname)
        full_flags = flags +  ['--dobuild', '--jobname', jobname]
        memory = self.opts['build_memory']

        return self.batch.submit_job(jobname=jobname, command=full_flags,
                                     memory=memory, dependson=dependson)

    def launch_property(self, flags=None, dependson=None):
        """Run CBMC to check program properties"""

        flags = flags or []
        jobname = "{}-property".format(self.jobname)
        full_flags = flags +  ['--doproperty', '--jobname', jobname]
        memory = self.opts['property_memory']

        return self.batch.submit_job(jobname=jobname, command=full_flags,
                                     memory=memory, dependson=dependson)

    def launch_coverage(self, flags=None, dependson=None):
        """Run CBMC to compute coverage statistics"""

        flags = flags or []
        jobname = "{}-coverage".format(self.jobname)
        full_flags = flags +  ['--docoverage', '--jobname', jobname]
        memory = self.opts['coverage_memory']

        return self.batch.submit_job(jobname=jobname, command=full_flags,
                                     memory=memory, dependson=dependson)

    def launch_report(self, flags=None, dependson=None):
        """Run cbmc-viewer to construct the final CBMC report"""

        flags = flags or []
        jobname = "{}-report".format(self.jobname)
        full_flags = flags +  ['--doreport', '--jobname', jobname]
        memory = self.opts['report_memory']

        return self.batch.submit_job(jobname=jobname, command=full_flags,
                                     memory=memory, dependson=dependson)

    def submit_jobs(self):
        """
        Submit CBMC jobs to CBMC patch
        """

        command = ['--jsons', json.dumps(self.opts)]

        build_job = {'jobid': None, 'jobname': None}
        property_job = {'jobid': None, 'jobname': None}
        coverage_job = {'jobid': None, 'jobname': None}
        report_job = {'jobid': None, 'jobname': None}
        buildjob = []
        propertyjob = []
        coveragejob = []
        if self.build:
            build_job = self.launch_build(command)
            buildjob = [build_job['jobid']]
        if self.property:
            property_job = self.launch_property(command, dependson=buildjob)
            propertyjob = [property_job['jobid']]
        if self.coverage:
            coverage_job = self.launch_coverage(command, dependson=buildjob)
            coveragejob = [coverage_job['jobid']]
        if self.report:
            report_job = self.launch_report(command,
                                            dependson=(propertyjob+coveragejob))

        results = {
            'jobname': self.jobname,
            'build': build_job,
            'property': property_job,
            'coverage': coverage_job,
            'report': report_job,
            }

        return results

################################################################

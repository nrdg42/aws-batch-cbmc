# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Monitor the status of CBMC jobs running under AWS Batch.
"""

import sys
import time
import datetime

################################################################

def abort(msg):
    """Abort monitoring a CBMC job"""

    print("CBMC status monitoring failed: {}".format(msg))
    sys.exit(1)

################################################################

def job_status(batch, jobname=None, jobid=None):
    """
    Get job status of CBMC jobs running under AWS Batch.
    """

    results = batch.job_status(jobname=jobname, jobid=jobid)
    return results

def display(jobs):
    """
    Display job status of CBMC jobs running under AWS Batch.
    """

    for job in jobs:
        print("{}: {}".format(job['jobName'], job['status']))

def current_status(batch, jobname=None, jobid=None):
    """Display current status of job"""

    jobs = job_status(batch, jobname, jobid)
    display(jobs)

def monitor_status(batch, jobname=None, jobid=None):
    """Monitor status of job"""

    status = {}

    def job_list(status):
        """Turn a dictionary of jobs into a list of jobs"""
        result = []
        for jid in status:
            result.append(status[jid])
        return result

    while True:
        jobs = job_status(batch, jobname, jobid)

        change = False
        for job in jobs:
            jobid = job['jobId']
            jobstatus = job['status']
            current = status.get(jobid, None)
            if current is None or jobstatus != current['status']:
                change = True
                status[jobid] = job
                continue
        if change:
            print()
            print(str(datetime.datetime.now()))
            print()
            display(job_list(status))

        stop = True
        for jid in status:
            stop = stop and status[jid]['status'] in ['SUCCEEDED', 'FAILED']

        if stop:
            return

        time.sleep(5)

################################################################

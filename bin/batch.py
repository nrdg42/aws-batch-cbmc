# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""A collection of methods for interacting with AWS Batch."""

import re
from pprint import pprint

import boto3
from botocore.exceptions import ClientError

import clienterror

################################################################

class BatchException(Exception):
    """Exception thrown by Batch methods."""

    def __init__(self, msg):
        super(BatchException, self).__init__()
        self.message = msg

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

DEBUGGING = True

def abort(msg1, msg2=None, data=None, verbose=False):
    """Abort a Batch method with debugging information."""
    code = clienterror.code(data)
    msgs = [msg1]
    if code is not None:
        msgs.append(" ({})".format(code))
    if msg2 is not None:
        msgs.append(": {}".format(msg2))
    msg = ''.join(msgs)
    if verbose or DEBUGGING:
        print("Batch Exception: {}".format(msg))
        pprint(clienterror.response(data) or data)
    raise BatchException(msg)

################################################################

class Batch:
    """An AWS Batch environment with methods to inspect and submit jobs."""

    def __init__(self, jobname=None, queuename=None, region=None):
        # Client is used to submit, kill, and query jobs
        self.client = boto3.client('batch', region_name=region)
        self.region = region

        # Job queue is used to submit and query jobs
        self.jobqueue = queuename
        if queuename is not None and not self.job_queue_exists(queuename):
            abort("No job queue found named {}".format(queuename))

        # Job definition is used to submit jobs
        self.jobdefinition = jobname
        if jobname is not None and not self.job_definition_exists(jobname):
            abort("No job definition found named {}".format(jobname))

    def job_definition_exists(self, jobdef=None):
        """Job definition exists (a unique, active definition of jobname)"""
        if jobdef is None:
            return False

        # Get all job definitions
        try:
            jobdefs_response = self.client.describe_job_definitions()
        except ClientError as exc:
            abort("Failed to get job definitions from Batch", data=exc)

        # Discard meta data returned with job definitions
        try:
            jobdefs = jobdefs_response['jobDefinitions']
        except KeyError:
            abort("Job definitions from Batch contained no actual definitions")

        # Confirm existence of a unique, active definition of jobdef
        found = False
        for job in jobdefs:
            name = job.get('jobDefinitionName', None)
            status = job.get('status', None)
            if name == jobdef and status == "ACTIVE":
                if found:
                    abort('Job definitions from Batch contained '
                          'multiple active definitions of {}'
                          .format(jobdef))
                found = True
        return found

    def job_queue_exists(self, jobqueue=None):
        """Job queue exists (a unique definition of jobqueue)"""
        if jobqueue is None:
            return False

        # Get all job queues
        try:
            jobqueue_response = self.client.describe_job_queues()
        except ClientError as exc:
            abort("Failed to get job queues from Batch", data=exc)

        # Discard meta data returned with job queues
        try:
            jobqueues = jobqueue_response['jobQueues']
        except KeyError:
            abort("Job queues from Batch contained no actual definitions")

        # Confirm existence of a unique definition of jobqueue
        found = False
        for job in jobqueues:
            name = job.get('jobQueueName', None)
            if name == jobqueue:
                if found:
                    abort('Job queues from Batch contained '
                          'multiple definitions of {}'
                          .format(jobqueue))
                found = True
        return found

    def submit_job(self, jobname=None, jobqueue=None, jobdefinition=None,
                   command=None, memory=None, dependson=None):
        """Run the job given by cmd in the batch environment."""

        # pylint: disable=too-many-arguments

        jobname = jobname or "cbmc"
        jobqueue = jobqueue or self.jobqueue
        jobdefinition = jobdefinition or self.jobdefinition
        # Should test that command is a list of strings
        overrides = {}
        if command is not None:
            overrides['command'] = command
            overrides['command'].extend(['--region', self.region])
        if memory is not None:
            overrides['memory'] = memory
        # Should test that depends is a list of strings
        dependson = [{'jobId': jid} for jid in dependson or []]

        try:
            result = self.client.submit_job(jobName=jobname,
                                            jobQueue=jobqueue,
                                            jobDefinition=jobdefinition,
                                            dependsOn=dependson,
                                            containerOverrides=overrides)
        except ClientError as exc:
            abort("Failed to run cbmc ('{}')".format(' '.join(command)),
                  data=exc)

        jobid = result.get('jobId', None)
        jobname = result.get('jobName', None)
        return {'jobid': jobid, 'jobname': jobname}

    def job_status(self, jobid=None, jobname=None):
        """
        Get the job status of every job matching a given job id or job name.
        """

        results = []
        for status in ['SUBMITTED', 'PENDING', 'RUNNABLE',
                       'STARTING', 'RUNNING', 'SUCCEEDED', 'FAILED']:
            try:
                response = self.client.list_jobs(
                    jobQueue=self.jobqueue,
                    jobStatus=status,
                    maxResults=1000
                    )
                for job in response['jobSummaryList']:
                    job_id = job['jobId']
                    job_name = job['jobName']
                    if (jobid and re.search(jobid, job_id) or
                            jobname and re.search(jobname, job_name)):
                        results.append({'jobId': job_id,
                                        'jobName': job_name,
                                        'status': status})
            except ClientError as exc:
                abort("Failed to list jobs on queue: {}".format(self.jobqueue),
                      data=exc)
            except KeyError as exc:
                abort("Failed to list {} jobs on queue: {}"
                      .format(status, self.jobqueue),
                      data=exc)
        return results

    def kill_job(self, jobid=None, jobname=None):
        """
        Kill every job matching a given job id or job name.
        """

        jobs = self.job_status(jobid, jobname)
        jids = [job['jobId'] for job in jobs]
        try:
            for jid in jids:
                self.client.terminate_job(jobId=jid,
                                          reason='Terminated by cbmc-batch '
                                          'command line')
        except ClientError as exc:
            abort("Failed to terminate jobs: {}".format(', '.join(jids)),
                  data=exc)

################################################################

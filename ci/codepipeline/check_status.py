# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# based on
# https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html#LambdaSample1

from __future__ import print_function

import boto3
import cbmc_status
import lambda_pipeline
import os
import pickle
import sys
import traceback


code_pipeline = boto3.client('codepipeline')


def continue_job_later(job, message, jobs):
    """Notify CodePipeline of a continuing job

    This will cause CodePipeline to invoke the function again with the
    supplied continuation token.

    Args:
        job: The JobID
        message: A message to be logged relating to the job status
        jobs: List of monitored jobs

    Raises:
        Exception: Any exception thrown by .put_job_success_result()

    """
    # Use the continuation token to keep track of any job execution state
    # This data will be available when a new job is scheduled to continue the
    # current execution
    continuation_token = pickle.dumps(jobs)

    print('Putting job continuation')
    print(message)
    code_pipeline.put_job_success_result(
            jobId=job, continuationToken=continuation_token)


def read_jobs(input_artifacts):
    """Read job information from input artifact

    Args:
        input_artifacts: job data structure describing input artifacts

    Returns:
        The list of jobs
    """
    if len(input_artifacts) != 1:
        raise Exception('Exactly one input artifact required')

    input_artifact = input_artifacts[0]
    bucket = input_artifact['location']['s3Location']['bucketName']
    key = input_artifact['location']['s3Location']['objectKey']

    s3 = boto3.client('s3')
    s3.download_file(Bucket=bucket, Key=key, Filename="jobs")
    with open("jobs", "r") as f:
        return pickle.load(f)


def batch_status(region, project_name, job_id, jobs):
    """Check status of batch jobs

    Succeeds, fails or continues the job depending on the batch status.

    Args:
        region: AWS region
        project_name: project name to use as metrics namespace
        job_id: id of Codebuild task
        jobs: list of job names

    Raises:
        Exception: An exception if no job was found, and any exception thrown
        while trying to start cbmc_status
    """
    if not jobs:
        raise Exception("No jobs found")

    all_succeeded = True
    for job in jobs:
        print(job)

        # CBMC Batch args -- require that property-checking is performed
        cbmc_status.sys.argv = ["cbmc_status", "--jobname", job]

        # Run cbmc_status
        with open("status", "w") as f:
            stdout = sys.stdout
            sys.stdout = f
            cbmc_status.main()
            sys.stdout = stdout

        with open("status", "r") as f:
            for line in f:
                print(line)
                line = line.rstrip()
                if line.endswith(": FAILED"):
                    lambda_pipeline.put_metric(
                            region, project_name, 'Failures')
                    lambda_pipeline.put_job_failure(job_id, line)
                    return
                elif not line.endswith(": SUCCEEDED"):
                    all_succeeded = False

    if all_succeeded:
        lambda_pipeline.put_metric(region, project_name, 'Successes')
        lambda_pipeline.put_job_success(job_id, "Verification successful")
    else:
        continue_job_later(job_id, "Verification in progress", jobs)


def lambda_handler(event, context):
    """
    Check the status of CBMC Batch jobs
    """
    # see
    # https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html
    # for the event dict contents
    # print(event)

    artifact_dirs = {}
    try:
        # Extract the Job ID
        job_id = event['CodePipeline.job']['id']

        # Extract the Job Data
        job_data = event['CodePipeline.job']['data']

        # Extract the params
        params = lambda_pipeline.get_user_params(job_data)

        with lambda_pipeline.make_temp_directory() as d:
            os.chdir(d)

            if 'continuationToken' in job_data:
                jobs = pickle.loads(job_data['continuationToken'])
            else:
                # Read job information from input artifact
                jobs = read_jobs(job_data['inputArtifacts'])

            # Check status of batch jobs
            batch_status(
                    params['region'], params['project_name'], job_id, jobs)

    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        print('Function failed due to exception.')
        print(e)
        traceback.print_exc()
        lambda_pipeline.put_job_failure(
                job_id, 'Function exception: ' + str(e))

    print('Function complete.')
    return "Complete."

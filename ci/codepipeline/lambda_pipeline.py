# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# based on
# https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html#LambdaSample1

from __future__ import print_function

import boto3
import contextlib
import json
import shutil
import tempfile


code_pipeline = boto3.client('codepipeline')


@contextlib.contextmanager
def make_temp_directory():
    """
    create a temporary directory and remove it once the statement completes
    """
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def put_job_success(job, message):
    """Notify CodePipeline of a successful job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_success_result()
    """
    print('Putting job success')
    print(message)
    code_pipeline.put_job_success_result(jobId=job)


def put_job_failure(job, message):
    """Notify CodePipeline of a failed job

    Args:
        job: The CodePipeline job ID
        message: A message to be logged relating to the job status

    Raises:
        Exception: Any exception thrown by .put_job_failure_result()
    """
    print('Putting job failure')
    print(message)
    code_pipeline.put_job_failure_result(
            jobId=job,
            failureDetails={'message': message, 'type': 'JobFailed'})


def get_user_params(job_data):
    """Decodes the JSON user parameters and validates the required properties.

    Args:
        job_data: The job data structure containing the UserParameters string
        which should be a valid JSON structure

    Returns:
        The JSON parameters decoded as a dictionary.

    Raises:
        Exception: The JSON can't be decoded or a property is missing.
    """
    try:
        # Get the user parameters which contain the S3 bucket and the name of
        # the source artifact
        up = job_data['actionConfiguration']['configuration']['UserParameters']
        decoded_parameters = json.loads(up)

    except Exception as e:
        # We're expecting the user parameters to be encoded as JSON
        # so we can pass multiple values. If the JSON can't be decoded
        # then fail the job with a helpful message.
        raise Exception('UserParameters could not be decoded as JSON: ' + up)

    if 'region' not in decoded_parameters:
        # Validate that the region is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('UserParameters JSON must include the region')

    if 'project_name' not in decoded_parameters:
        # Validate that the project name is provided, otherwise fail the job
        # with a helpful message.
        raise Exception(
                'UserParameters JSON must include the project name')

    return decoded_parameters


def put_metric(region, namespace, metric):
    """Put a CloudWatch metric data point

    Args:
        region: AWS region
        namespace: CloudWatch metrics namespace
        metric: CloudWatch metric
    """
    cloudwatch = boto3.client('cloudwatch', region_name=region)
    cloudwatch.put_metric_data(
        MetricData=[{'MetricName': metric, 'Unit': 'None', 'Value': 1.0}],
        Namespace=namespace
    )

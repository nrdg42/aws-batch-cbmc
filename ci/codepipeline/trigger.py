# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# based on
# https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html#LambdaSample1

from __future__ import print_function

import boto3
import cbmc_batch
import glob
import lambda_pipeline
import pickle
import os
import tarfile
import tempfile
import traceback
import zipfile


WS_DIR = "ws"
SRC_DIR = "src"


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
    decoded_parameters = lambda_pipeline.get_user_params(job_data)

    if 's3_bucket' not in decoded_parameters:
        # Validate that the stack is provided, otherwise fail the job
        # with a helpful message.
        raise Exception('UserParameters JSON must include the S3 bucket')

    if 'src_artifact' not in decoded_parameters:
        # Validate that the artifact name is provided, otherwise fail the job
        # with a helpful message.
        raise Exception(
                'UserParameters JSON must include the source artifact name')

    return decoded_parameters


def record_jobs(output_artifacts, jobs):
    """Put job information into output artifact

    Args:
        output_artifacts: job data structure describing output artifacts
        jobs: list of jobs
    """
    if len(output_artifacts) != 1:
        raise Exception('Exactly one output artifact required')

    output_artifact = output_artifacts[0]
    bucket = output_artifact['location']['s3Location']['bucketName']
    key = output_artifact['location']['s3Location']['objectKey']

    with tempfile.NamedTemporaryFile() as tmp_file:
        pickle.dump(jobs, tmp_file)
        tmp_file.flush()
        s3 = boto3.client('s3')
        s3.upload_file(Bucket=bucket, Key=key, Filename=tmp_file.name)


def extract_artifacts(artifacts, src_artifact, src_key):
    """Extract all input artifacts into newly created directories

    Downloads the artifacts from the S3 artifact store to temporary files and
    then extracts the zips

    Args:
        artifacts: Input artifacts in the job data structure
        src_artifact: Name of the input artifact containing source code
        src_key: S3 key to use to store the source tar.gz

    Raises:
        Exception: Any exception thrown while downloading the artifact or
        unzipping it
    """

    results = {}

    s3 = boto3.client('s3')
    for artifact in artifacts:
        bucket = artifact['location']['s3Location']['bucketName']
        key = artifact['location']['s3Location']['objectKey']

        source_or_workspace = WS_DIR
        if artifact['name'] == src_artifact:
            source_or_workspace = SRC_DIR
        os.mkdir(source_or_workspace)

        with tempfile.NamedTemporaryFile() as tmp_file:
            s3.download_file(Bucket=bucket, Key=key, Filename=tmp_file.name)
            with zipfile.ZipFile(tmp_file.name, 'r') as zip_file:
                zip_file.extractall(source_or_workspace)

        if source_or_workspace == SRC_DIR:
            with tarfile.open("src.tar.gz", "w:gz") as tf:
                tf.add(SRC_DIR)
            s3.upload_file(Bucket=bucket, Key=src_key, Filename="src.tar.gz")


def start_batch(region, job_id, s3_bucket):
    """Start CBMC Batch

    Succeeds, fails or continues the job depending on the batch status.

    Args:
        region: AWS region
        job_id: The CodePipeline job ID
        s3_bucket: The S3 bucket that CBMC Batch should use

    Returns:
        A list of job names

    Raises:
        Exception: An exception if no yaml file was found in the workspace, and
        any exception thrown while trying to start cbmc_batch
    """
    yamls = glob.glob(os.path.join(WS_DIR, "*.yaml"))
    print(yamls)
    if not yamls:
        raise Exception("No yaml file found in workspace")

    jobs = []
    for y in yamls:
        # strip the .yaml suffix
        task_name = os.path.basename(y)[:-5]
        job_name = job_id + "-" + task_name
        print(job_name)

        # CBMC Batch args -- require that property-checking is performed
        cbmc_batch.sys.argv = [
                "cbmc_batch",
                "--region", region,
                "--no-file-output",
                "--wsdir", WS_DIR,
                "--srcdir", SRC_DIR, "--no-copysrc",
                "--srctarfile",
                "s3://{}/{}-src.tar.gz".format(s3_bucket, job_id),
                "--bucket", s3_bucket,
                "--no-build",
                "--jobname", job_name,
                "--taskname", task_name,
                "--yaml", y]

        # Run CBMC Batch
        cbmc_batch.main()
        jobs.append(job_name)

    return jobs


def lambda_handler(event, context):
    """
    Start CBMC Batch
    """
    # see
    # https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html
    # for the event dict contents
    # print(event)

    try:
        # Extract the Job ID
        job_id = event['CodePipeline.job']['id']

        # Extract the Job Data
        job_data = event['CodePipeline.job']['data']

        if 'continuationToken' in job_data:
            # This should not be triggered to check the status
            raise Exception('Trigger should not be invoked twice')

        # Extract the params
        params = get_user_params(job_data)

        lambda_pipeline.put_metric(
                params['region'], params['project_name'], 'Attempts')

        # Get the list of artifacts passed to the function
        artifacts = job_data['inputArtifacts']

        # add the current directory to the PATH for cbmc_batch to invoke the
        # aws cli successfully
        os.environ['PATH'] = "{}:{}".format(
                os.environ['LAMBDA_TASK_ROOT'], os.environ['PATH'])

        with lambda_pipeline.make_temp_directory() as tmp_dir:
            os.chdir(tmp_dir)

            # Get the artifacts
            extract_artifacts(
                    artifacts, params['src_artifact'], job_id + "-src.tar.gz")

            # Kick off batch jobs
            jobs = start_batch(params['region'], job_id, params['s3_bucket'])

            # Put job information into output artifact
            record_jobs(job_data['outputArtifacts'], jobs)

        lambda_pipeline.put_job_success(job_id, 'CBMC Batch started')

    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail the job and log the exception message.
        print('Function failed due to exception.')
        print(e)
        traceback.print_exc()
        lambda_pipeline.put_metric(
                params['region'], params['project_name'], 'Errors')
        lambda_pipeline.put_job_failure(
                job_id, 'Function exception: ' + str(e))

    print('Function complete.')
    return "Complete."

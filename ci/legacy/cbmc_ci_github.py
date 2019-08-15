# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
from cbmc_ci_timer import Timer
from github import Github
import json
import os
import tarfile
import urllib2


def get_github_personal_access_token():
    """
    Get plaintext for GitHub Personal Access Token (needed for updating commit
    statuses)
    """
    sm = boto3.client('secretsmanager')
    s = sm.get_secret_value(SecretId='GitHubCommitStatusPAT')
    return str(json.loads(s['SecretString'])[0]['GitHubPAT'])


def update_status(status, ctx, jobname, desc, repo_id, sha):
    """Update GitHub Status

    Relevant documentation:
    https://developer.github.com/v3/repos/statuses/#create-a-status
    http://pygithub.readthedocs.io/en/latest/github_objects/Commit.html
    """
    region = os.environ['AWS_REGION']

    status_to_metric = {
            "pending": "Attempts",
            "error": "Errors",
            "success": "Successes",
            "failure": "Failures"
            }
    cloudwatch = boto3.client("cloudwatch", region_name=region)
    cloudwatch.put_metric_data(
        MetricData=[
            {
                'MetricName': status_to_metric[status],
                'Unit': 'None',
                'Value': 1.0
            },
        ],
        Namespace=os.environ['PROJECT_NAME']
    )

    timer = Timer("Updating GitHub status {} with description {}".format(
                    status, desc))
    g = Github(get_github_personal_access_token())
    try:
        ctx = "CBMC Batch: " + ctx
        if jobname:
            target_url = ("https://s3.console.aws.amazon.com/s3/buckets/" +
                          os.environ['S3_BKT'] + "/" + jobname + "/out/")
            g.get_repo(repo_id).get_commit(sha=sha).create_status(
                    state=status,
                    context=ctx,
                    description=desc,
                    target_url=target_url)
        else:
            g.get_repo(repo_id).get_commit(sha=sha).create_status(
                    state=status, context=ctx, description=desc)
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'GitHub status update succeeded',
                    'Unit': 'None',
                    'Value': 1.0
                },
            ],
            Namespace=os.environ['PROJECT_NAME']
        )
    except Exception as e:
        print "Failed to update status on GitHub: " + str(e)
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'GitHub status update failed',
                    'Unit': 'None',
                    'Value': 1.0
                },
            ],
            Namespace=os.environ['PROJECT_NAME']
        )
    timer.end()


def fetch_tar(tar_path, tar_URL):
    """
    Download tar_URL to tar_path.

    GitHub may require authorization in case of private repositories. This is
    accomplished by setting an "Authorization" HTTP header to the GitHub
    personal access (OAuth) token.
    """
    print "downloading {} to {}".format(tar_URL, tar_path)
    token = get_github_personal_access_token()
    request = urllib2.Request(
            url=tar_URL, headers={"Authorization": "token " + token})
    response = urllib2.urlopen(request)
    with open(tar_path, "w") as tar:
        tar.write(response.read())


def extract_tar(tmp_dir, tar_path):
    """
    Extract a tar archive downloaded from GitHub.

    All files in the archive should be contained in a single top-level
    directory - the code below actually checks that all files share a common
    prefix, which must be a directory. The name of that directory varies, and
    is thus found as the common prefix and returned to the caller.
    """
    print "extracting {} to {}".format(tar_path, tmp_dir)
    prefix = None
    with tarfile.open(tar_path) as tar:
        paths = tar.getnames()
        for p in paths:
            if p.startswith('/') or '..' in p:
                raise ValueError("Invalid filename")
        prefix = os.path.commonprefix(paths)
        tar.extractall(path=tmp_dir)
    print str(os.listdir(tmp_dir))
    if not prefix or not os.path.isdir(os.path.join(tmp_dir, prefix)):
        raise ValueError("No common root base directory found")
    return prefix


def get_tar(name, full_name, sha, tmp_dir):
    """Get tar containing the code for the commit"""
    timer = Timer("Get tar containing code for commit")
    tar_name = sha + ".tar.gz"
    tar_URL = "https://api.github.com/repos/{}/tarball/{}".format(
            full_name, str(sha))
    tar_file = full_name.replace('/', '-') + "-" + tar_name
    tar_path = os.path.join(tmp_dir, tar_file)
    fetch_tar(tar_path, tar_URL)
    timer.end()

    timer = Timer("Extract tar containing code for commit")
    src = extract_tar(tmp_dir, tar_path)
    timer.end()

    timer = Timer("Uploading tar containing code for commit to S3")
    s3 = boto3.client('s3')
    s3.upload_file(
            Bucket=os.environ['S3_BKT'], Key=tar_file, Filename=tar_path)
    timer.end()

    # Directory resulting from extracting the tar
    return (os.path.join(tmp_dir, src), tar_file)


def parse_repo(repo):
    """
    Get the name, full repo name, and repo ID for the repo for a GitHub commit.

    The repo structure has been extracted from the pull request or push event
    formats
    """
    name = str(repo["name"])
    full_name = str(repo["full_name"])
    repo_id = repo["id"]
    return (name, full_name, repo_id)


def parse_pr(event):
    """
    Get the source code, full repo name, repo ID, and SHA for the GitHub commit
    in the event.

    event has a format as described here:
        https://developer.github.com/v3/activity/events/types/#pullrequestevent
    """
    pr_head = event["pull_request"]["head"]
    (name, full_name, repo_id) = parse_repo(pr_head["repo"])
    (base_name, base_full_name, base_repo_id) = parse_repo(
            event["pull_request"]["base"]["repo"])
    action = event["action"]
    if action in ["opened", "synchronize"]:
        print "Pull request: {action} {from_repo} -> {to_repo}".format(
                action=action, from_repo=full_name, to_repo=base_full_name)
        sha = pr_head["sha"]
    else:
        print "Ignoring pull request with action {}".format(action)
        sha = None
    if sha is not None and full_name == base_full_name:
        print "Ignoring pull request action as base repository matches head"
        sha = None
    return (name, base_full_name, sha, base_repo_id)


def parse_push(event):
    """
    Get the source code, full repo name, repo ID, and SHA for the GitHub commit
    in the event

    event has a format as described here:
        https://developer.github.com/v3/activity/events/types/#pushevent
    """
    (name, full_name, repo_id) = parse_repo(event["repository"])
    head_commit = event["head_commit"]
    if head_commit:
        print "Push to {}: {}".format(full_name, event["ref"])
        sha = head_commit["id"]
    else:
        print "Ignoring delete-branch push event"
        sha = None
    return (name, full_name, sha, repo_id)


def parse_event(event):
    """
    Get the source code, repo ID, and SHA for the GitHub commit in the event.

    event is a json data structure containing a header and a payload.
    The header format is described here: https://developer.github.com/webhooks/
    The payload, which contains a string that can be parsed into json for the
    type of GitHub event has a format as described here:
        https://developer.github.com/v3/activity/events/types/
    We expect to handle PushEvents and PullRequestEvents
    """
    event["headers"] = {k.lower(): v for k, v in event["headers"].items()}
    event_type = event["headers"]["x-github-event"]
    body = json.loads(event["body"])
    if event_type == "pull_request":
        (name, full_name, sha, repo_id) = parse_pr(body)
    elif event_type == "push":
        (name, full_name, sha, repo_id) = parse_push(body)
    else:
        raise ValueError("Unexpected event type")

    return (name, full_name, sha, repo_id)

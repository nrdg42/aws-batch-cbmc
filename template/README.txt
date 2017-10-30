# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

AUTOMATED BATCH UPDATES
=======================

0. All AWS deployments need to be in us-west-2 (for replication from gitfarm)

1. Deploy cbmc.yaml

2. Obtain a GitHub personal access token at
   https://github.com/settings/tokens/new, with permissions "repo" and
   "admin:repo_hook". Use this token as <ACCESS_TOKEN> in the following.

3. Deploy github.yaml, using a command such as
   aws --region us-west-2 cloudformation create-stack \
     --stack-name github --template-body file://pipeline.yaml \
     --capabilities CAPABILITY_NAMED_IAM --parameters \
     ParameterKey=GitHubToken,ParameterValue=<ACCESS_TOKEN> \
     ParameterKey=NotificationAddress,ParameterValue=$USER@amazon.com

4. Create replications of CBMC-batch and CBMC-coverage at
   https://code.amazon.com/packages/CBMC-batch/replicas and
   https://code.amazon.com/packages/CBMC-coverage/replicas
   respectively with ARN
   arn:aws:iam::<AWS_ACCOUNT_ID>:role/picapica-role
   and CBMC-batch and CBMC-coverage as repo name, respectively.

5. Wait for the CodePipeline batch-build to complete successfully.

6. Use CBMC Batch with --bucket <AWS_ACCOUNT_ID>-us-west-2-cbmc-batch.


METRICS
=======

1. Deploy dashboard.yaml with a <PROJECT_NAME>:
   aws --region us-west-2 cloudformation create-stack \
     --stack-name metrics-dashboard --template-body file://dashboard.yaml \
     --parameters ParameterKey=ProjectName,ParameterValue=<PROJECT_NAME>

2. Deploy CloudWatchDashboardsWiki.template from
   https://w.amazon.com/index.php/CloudWatch/Dashboards

3. Add {{CloudWatch/Dashboard | <AWS_ACCOUNT_ID> | <PROJECT_NAME>}} to the
   project wiki page (see https://w.amazon.com/index.php/CloudWatch/Dashboards
   for details and equivalent instructions for the new wiki).

4. Put data into the specified metrics using, e.g.,
   aws --region us-west-2 cloudwatch put-metric-data \
     --namespace <PROJECT_NAME> --metric-data <DATA>

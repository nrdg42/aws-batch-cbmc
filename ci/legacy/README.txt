# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

0. All AWS deployments need to be in us-west-2 (for replication from gitfarm)

1. Verify email addresses with SES - for the first one use the same as the
   NotificationAddress used below:
   aws --region us-west-2 ses verify-email-identity --email-address \
     $USER@amazon.com
   aws --region us-west-2 ses verify-email-identity --email-address \
     issues+create+91b477f7-c17e-43b9-b5fe-7e666b0bd1c6@email.amazon.com

2. Deploy cbmc.yaml from the template/ folder:
   aws --region us-west-2 cloudformation create-stack \
     --stack-name cbmc-batch --template-body file://cbmc.yaml \
     --capabilities CAPABILITY_NAMED_IAM

3. Obtain a GitHub personal access token at
   https://github.com/settings/tokens/new, with permissions "repo" and
   "admin:repo_hook". Use this token as <ACCESS_TOKEN> in the following.

4. Pick some random string (or generate one). Use this as <SECRET> below.

5. Setup secrets in Secrets Manager:
   aws --region us-west-2 secretsmanager create-secret \
     --name GitHubCommitStatusPAT \
     --secret-string '[{"GitHubPAT":"<ACCESS_TOKEN>"}]'
   aws --region us-west-2 secretsmanager create-secret \
     --name GitHubSecret \
     --secret-string '[{"Secret":"<SECRET>"}]'

6. Deploy github.yaml with a chosen <PROJECT_NAME>, using a command such as the
   below; use the same <PROJECT_NAME> when deploying the metrics dashboard (see
   template/README.txt):
   aws --region us-west-2 cloudformation create-stack \
     --stack-name github --template-body file://github.yaml \
     --capabilities CAPABILITY_NAMED_IAM --parameters \
     ParameterKey=GitHubToken,ParameterValue=<ACCESS_TOKEN> \
     ParameterKey=NotificationAddress,ParameterValue=$USER@amazon.com \
     ParameterKey=ProjectName,ParameterValue=<PROJECT_NAME> \
     ParameterKey=GitHubRepository,ParameterValue=<ORGANIZATION/REPOSITORY> \
     ParameterKey=SIMAddress,ParameterValue=issues+create+91b477f7-c17e-43b9-b5fe-7e666b0bd1c6@email.amazon.com

7. Create replications of CBMC-batch and CBMC-coverage at
   https://code.amazon.com/packages/CBMC-batch/replicas and
   https://code.amazon.com/packages/CBMC-coverage/replicas
   respectively with ARN
   arn:aws:iam::<AWS_ACCOUNT_ID>:role/picapica-role
   and CBMC-batch and CBMC-coverage as repo name, respectively.

8. Wait for the CodePipeline batch-build to complete successfully.

9. Configure the web hook on GitHub. The required <ID> is the id listed by
   aws --region us-west-2 apigateway get-rest-apis
   With this <ID>, configure the web hook:
   https://<ID>.execute-api.us-west-2.amazonaws.com/verify
   as URL, content type application/json, and <SECRET> as secret. Select
   "Pushes" and "Pull requests" as the events triggering this webhook.

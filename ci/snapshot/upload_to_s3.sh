#!/bin/sh

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

WD=$PWD
VENV=$WD/venv
PACKAGE=$VENV/lib/python2.7/site-packages
AWS=$VENV/bin/aws
S3_BKT=s3://cbmc-batch
S3_ZIP_DEST=$S3_BKT/source
S3_CBMC_BATCH_SRC=$S3_BKT/package/cbmc-batch.tar.gz

# Install dependencies
virtualenv $VENV
source $VENV/bin/activate
pip install pyyaml
pip install pygithub
pip install awscli
pip install backports.tempfile
aws s3 cp $S3_CBMC_BATCH_SRC ./cbmc-batch.tar.gz
tar -xvf cbmc-batch.tar.gz
mv ./cbmc-batch/cbmc-batch ./cbmc-batch/cbmc_batch.py

# Package up dependencies into cbmc_ci_env.zip
mkdir ./tmp-env
cp -r $PACKAGE/* ./tmp-env
cp $AWS ./tmp-env
cp -r ./cbmc-batch/* ./tmp-env
cd ./tmp-env
firstline="#\!/usr/bin/python"
sed -i ".bak" "1s@.*@$firstline@" aws
zip -r $WD/cbmc_ci_env.zip ./*
cd $WD
rm -rf ./tmp-env

# Upload the CBMC CI Start zip to S3 Bucket
cp cbmc_ci_env.zip cbmc_ci_start.zip
zip -g cbmc_ci_start.zip cbmc_ci_github.py
zip -g cbmc_ci_start.zip cbmc_ci_timer.py
zip -g cbmc_ci_start.zip cbmc_ci_start.py
aws s3 cp cbmc_ci_start.zip $S3_ZIP_DEST/cbmc_ci_start.zip

# Upload the CBMC CI End zip to S3 Bucket
cp cbmc_ci_env.zip cbmc_ci_end.zip
zip -g cbmc_ci_end.zip cbmc_ci_github.py
zip -g cbmc_ci_end.zip cbmc_ci_timer.py
zip -g cbmc_ci_end.zip cbmc_ci_end.py
aws s3 cp cbmc_ci_end.zip $S3_ZIP_DEST/cbmc_ci_end.zip

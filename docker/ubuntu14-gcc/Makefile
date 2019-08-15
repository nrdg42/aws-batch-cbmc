# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../../Makefile.local

IMAGE = cbmc
TAG = ubuntu14-gcc

default:
	echo $(FLAGS)
	echo $(IMAGETAGSUFFIX)
	docker build $(FLAGS) --file Dockerfile --tag $(IMAGE):$(TAG) ../..
	docker tag $(IMAGE):$(TAG) $(REPO):$(TAG)$(IMAGETAGSUFFIX)

install:
	echo $(FLAGS)
	echo $(IMAGETAGSUFFIX)
	docker push $(REPO):$(TAG)$(IMAGETAGSUFFIX)

clean:
	$(RM) *~

.PHONY: default install clean



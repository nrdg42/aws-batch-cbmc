# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../Makefile.local

default:
	@echo Nothing to build

install:
	@echo Nothing to install

clean:
	$(RM) *~
	$(RM) *.pyc
	$(RM) Makefile-cbmc-2018*
	$(RM) cbmc-2018*.json cbmc-2018*.yaml

pylint:
	pylint \
	    --disable=duplicate-code \
	    --module-rgx='[a-z0-9_-]*$$' \
	  *.py cbmc-status cbmc-batch cbmc-kill

.PHONY: default install clean pylint

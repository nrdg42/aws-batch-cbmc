# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../Makefile.local

export FLAGS

.PHONY: default install clean

default:
	$(MAKE) -C ubuntu16-gcc $@

#	$(MAKE) -C ubuntu18-gcc $@
#	$(MAKE) -C ubuntu14-gcc $@

install:
	$(MAKE) -C ubuntu16-gcc $@

#	$(MAKE) -C ubuntu18-gcc $@
#	$(MAKE) -C ubuntu14-gcc $@

clean:
	$(RM) *~
	$(MAKE) -C ubuntu14-gcc $@
	$(MAKE) -C ubuntu16-gcc $@
	$(MAKE) -C ubuntu18-gcc $@

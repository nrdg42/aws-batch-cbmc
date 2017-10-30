# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../Makefile.local

.PHONY: default install clean

default:
	$(MAKE) -C ubuntu14-cbmc
	$(MAKE) -C ubuntu16-cbmc

install:
	$(MAKE) -C ubuntu14-cbmc $@
	$(MAKE) -C ubuntu16-cbmc $@

clean:
	$(RM) *~
	$(MAKE) -C ubuntu14-cbmc $@
	$(MAKE) -C ubuntu16-cbmc $@

# This is a target to simplify making a package locally
# without going through the ubuntu container
# Go to the cbmc build directory containing the src directory
# and run "make -f ..../Makefile local"

.PHONY: local

local:
	mkdir cbmc
	cp \
		src/goto-analyzer/goto-analyzer \
		src/goto-cc/goto-cc \
		src/goto-instrument/goto-instrument \
		src/goto-diff/goto-diff \
		src/cbmc/cbmc \
	cbmc
	tar fcz cbmc.tar.gz cbmc
	rm -rf cbmc

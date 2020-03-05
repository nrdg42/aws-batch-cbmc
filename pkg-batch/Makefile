# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../Makefile.local

BATCHOBJ = $(BATCHDIR)/bin/*

BIN=cbmc-batch

.PHONY: default install

default:
	$(RM) -r $(BIN)
	mkdir $(BIN)
	# Copy files to BIN. Depth is 0 because of the '*' in BATCHOBJ variable.
	find $(BATCHOBJ) -maxdepth 0 -mindepth 0 -type f -not -name '.*' -exec cp -v '{}' $(BIN)/ \;
	tar fcz $(BIN).tar.gz $(BIN)

install:
	aws s3 cp $(BIN).tar.gz $(PKGBUCKET)/$(BIN).tar.gz

clean:
	$(RM) *~
	$(RM) -r $(BIN) $(BIN).tar.gz

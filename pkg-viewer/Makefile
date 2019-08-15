# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

-include ../Makefile.local

VIEWEROBJ = $(VIEWERDIR)/*
BIN=cbmc-viewer

.PHONY: default install

default:
	$(RM) -r $(BIN)
	mkdir $(BIN)
	cp $(VIEWEROBJ) $(BIN)
	tar fcz $(BIN).tar.gz $(BIN)

install:
	aws s3 cp $(BIN).tar.gz $(PKGBUCKET)/$(BIN).tar.gz

clean:
	$(RM) *~
	$(RM) -r $(BIN) $(BIN).tar.gz

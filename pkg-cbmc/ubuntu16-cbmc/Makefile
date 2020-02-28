# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

################################################################
#
# Run "make" to build cbmc inside a container and produce a tar file
# cbmc.tar.gz that untars to a directory "cbmc" that contains the cbmc
# binaries.  This is what should be moved to the S3 bucket for cbmc-batch.
#
# Run "make clean" to clean up.
#

# Directory holding the cbmc patches.  Clone the develop branch of
# cbmc at diffblue and apply these patches before building cbmc.
# Mounted on /patches in container
#
PATCHES = $(abspath ../patches)

# Directory holding the final cbmc.tar.gz tar file.
# Mounted on /cbmc in container
#
CWD = $(abspath .)

-include ../../Makefile.local

# No changes below this line should be required

################################################################

default: tarfile owner

tarfile:
	docker run -it -v $(CWD):/cbmc -v $(PATCHES):/patches \
		--entrypoint make cbmc:ubuntu16-gcc -C /cbmc cbmc

owner:
	$(eval FOWNER = $(shell ls -ld cbmc.tar.gz | awk 'NR==1 {print $$3}' | xargs id -u))
	$(eval FGROUP = $(shell ls -ld cbmc.tar.gz | awk 'NR==1 {print $$3}' | xargs id -g))
	$(eval UID = $(shell id -u))
	$(eval GID = $(shell id -g))
	[ "$(FOWNER)" = "$(UID)" ] || sudo chown $(UID) cbmc.tar.gz
	[ "$(FGROUP)" = "$(GID)" ] || chgrp $(GID) cbmc.tar.gz
	@ls -ld cbmc.tar.gz

install:
	aws s3 cp cbmc.tar.gz $(PKGBUCKET)/cbmc-ubuntu16.tar.gz

clean:
	$(RM) cbmc.tar.gz *~

.PHONY: default tarfile owner install clean

################################################################
# Make command run from within the docker container

# paths inside container for mounting local directories
PATCHDIR = /patches
CBMCDIR = /cbmc

# paths inside container for building and installing cbmc
CBMCGIT = /tmp/git
CBMCBIN = /tmp/cbmc
CBMCOBJ = \
	$(CBMCGIT)/cbmc/src/goto-analyzer/goto-analyzer \
	$(CBMCGIT)/cbmc/src/goto-cc/goto-cc \
	$(CBMCGIT)/cbmc/src/goto-instrument/goto-instrument \
	$(CBMCGIT)/cbmc/src/goto-diff/goto-diff \
	$(CBMCGIT)/cbmc/src/cbmc/cbmc \

cbmc: cbmc-clone cbmc-patch cbmc-build cbmc-tar

cbmc-clone:
	mkdir -p $(CBMCGIT)
	cd $(CBMCGIT); \
	git clone https://github.com/diffblue/cbmc.git

cbmc-patch:
	cd $(CBMCGIT)/cbmc; \
	git checkout develop; \
	for f in $(PATCHDIR)/*; do git apply $$f; done

cbmc-build:
	make DOWNLOADER='wget' -C $(CBMCGIT)/cbmc/src minisat2-download
	make -C $(CBMCGIT)/cbmc/src CXX=g++-5 -j8

cbmc-tar:
	mkdir -p $(CBMCBIN)
	cp $(CBMCOBJ) $(CBMCBIN)
	cd $(dir $(CBMCBIN)); \
	  tar fcz cbmc.tar.gz cbmc; \
	  mv cbmc.tar.gz $(CBMCDIR)

.PHONY: cbmc cbmc-clone cbmc-patch cbmc-build cbmc-tar


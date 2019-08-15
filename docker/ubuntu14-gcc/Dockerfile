# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

FROM ubuntu:14.04

# Installing software-properties-common to get test PPA
# Installing gcc/g++ version 5 via a test PPA to build cbmc on Ubuntu 14
# Installing default-jdk to get javacc to build cbmc (java component)
# Installing emacs24-bin-common to get etags (try etags with ctags pkg)
# Installing bc for Annapurna stage1 Makefile

ENV DEBIAN_FRONTEND noninteractive
ARG UBUNTU_ARCHIVE
ENV UBUNTU_ARCHIVE ${UBUNTU_ARCHIVE:-archive.ubuntu.com}

RUN sed -i "s#/archive.ubuntu.com#/${UBUNTU_ARCHIVE}#g" \
    /etc/apt/sources.list

RUN apt-get -y update && \
    apt-get -y install software-properties-common && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install \
    bc \
    bison \
    default-jdk \
    emacs24-bin-common \
    flex \
    g++-5 \
    gcc-5 \
    git \
    libc6-dev-i386 \
    libwww-perl \
    make \
    patch \
    python \
    python-pip \
    wget \
    && apt-get clean

RUN \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-5 1; \
    update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-5 1

# Install the latest version of pip
# Install awscli and boto3 with pip and not apt-get (want python 2.7 version)
RUN pip install --upgrade pip && \
    pip install --upgrade awscli && \
    pip install --upgrade boto3 && \
    pip install future

# install libssl-dev for building the encryption SDK
RUN apt-get -y install libssl-dev

ADD bin /cbmc-batch-boot

ENV PATH "$PATH:/cbmc"
ENV PATH "$PATH:/cbmc-viewer"
ENV PATH "$PATH:/cbmc-batch"

ENTRYPOINT ["python", "/cbmc-batch-boot/boot.py"]



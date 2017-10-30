# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Copy and install packages from S3 into a docker container"""

import sys
import subprocess
import os

def abort(msg):
    """Abort package installation or launch"""
    raise RuntimeError(msg)

def copy(pkg, bkt, tar):
    """Copy package pkg from bucket bkt in file tar"""
    cmd = ['aws', 's3', 'cp', '{}/{}'.format(bkt, tar), tar]
    cmds = " ".join(cmd)
    print("Copying package {} with '{}'".format(pkg, cmds))
    sys.stdout.flush()
    try:
        subprocess.check_call(cmd)
    except Exception as exc:
        print("Error copying package {} with '{}' ({})"
              .format(pkg, cmds, exc))
        sys.stdout.flush()
        raise exc

def install(pkg, tar, bindir):
    """Intall package pkg from file tar into directory bindir"""
    cmd = ['tar', 'fx', tar]
    cmds = " ".join(cmd)
    print("Installing package {} with '{}'".format(pkg, cmds))
    sys.stdout.flush()
    try:
        subprocess.check_call(cmd)
    except Exception as exc:
        print("Error installing package {} with '{}' ({})"
              .format(pkg, cmds, exc))
        sys.stdout.flush()
        raise exc
    if not os.path.isdir(bindir):
        abort("Failed to create {} by installing package {} with '{}'"
              .format(bindir, pkg, cmds))

def launch(bindir, script, options):
    """Launch script in bindir with options"""
    cmd = ['python', '{}/{}'.format(bindir, script)] + options
    cmds = " ".join(cmd)
    print("Launching {} with '{}'".format(script, cmds))
    sys.stdout.flush()
    try:
        subprocess.check_call(cmd)
    except RuntimeError as exc:
        print("bombed")
        raise exc
    except Exception as exc:
        print("Script {} launched with '{}' returned an error code ({})"
              .format(script, cmds, exc))
        sys.stdout.flush()
        raise exc

################################################################

# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Parse and validate options from command line arguments and configuration files.
"""

import argparse
import json
import os
import time
import re
import yaml

import boto3

import s3

################################################################

def abort(msg):
    """Abort option parsing."""
    raise Exception(msg)

################################################################
# The main methods of this module

def batch_options():
    """Parse options for cbmc-batch"""

    parser = argparse.ArgumentParser(description='Run CBMC on AWS Batch')
    parser = directory_parser(parser)
    parser = bucket_parser(parser)
    parser = package_parser(parser)
    parser = phase_parser(parser)
    parser = cbmcflags_parser(parser)
    parser = build_parser(parser)
    parser = aws_batch_parser(parser)
    parser = other_parser(parser)
    parser = config_parser(parser)

    args = parser.parse_args()
    config = parse_config(args)

    opts = {}
    # Do aws_batch before bucket
    opts = aws_batch_merge(opts, args, config)
    opts = directory_merge(opts, args, config)
    opts = bucket_merge(opts, args, config)
    opts = package_merge(opts, args, config)
    opts = phase_merge(opts, args, config)
    opts = cbmcflags_merge(opts, args, config)
    opts = build_merge(opts, args, config)
    opts = other_merge(opts, args, config)

    return opts

def status_options():
    """Parse options for cbmc-status"""

    parser = argparse.ArgumentParser(description='Monitor status of CBMC jobs '
                                     'running on AWS Batch.')
    parser = cbmc_status_parser(parser)
    parser = region_parser(parser)
    parser = config_parser(parser)

    args = parser.parse_args()
    config = parse_config(args)

    opts = {}
    opts = region_merge(opts, args, config)
    opts = cbmc_status_merge(opts, args, config)

    return opts

def kill_options():
    """Parse options for cbmc-kill"""

    parser = argparse.ArgumentParser(description='Kill CBMC jobs '
                                     'running on AWS Batch.')
    parser = cbmc_status_parser(parser)
    parser = region_parser(parser)
    parser = config_parser(parser)

    args = parser.parse_args()
    config = parse_config(args)

    opts = {}
    opts = region_merge(opts, args, config)
    opts = cbmc_status_merge(opts, args, config)

    return opts

def docker_options():
    """Parse options for docker script driving the docker container"""

    parser = argparse.ArgumentParser(description='Run CBMC in a container')
    parser = directory_parser(parser)
    parser = bucket_parser(parser)
    parser = package_parser(parser)
    parser = cbmcflags_parser(parser)
    parser = build_parser(parser)
    parser = aws_batch_parser(parser)
    parser = container_parser(parser)
    parser = config_parser(parser)

    args = parser.parse_args()
    config = parse_config(args)

    opts = {}
    # Do aws_batch before bucket
    opts = aws_batch_merge(opts, args, config)
    opts = directory_merge(opts, args, config)
    opts = bucket_merge(opts, args, config)
    opts = package_merge(opts, args, config)
    opts = cbmcflags_merge(opts, args, config)
    opts = build_merge(opts, args, config)
    opts = container_merge(opts, args, config)

    return opts

################################################################
# Methods to add command line arguments to the command line parser
# together with methods to merge options from the command line, from
# the config files, and from default values.  We present these methods
# together because the needed to be maintained together.  We break
# parsing and merging into a handful of methods because different
# commands want different options.

def merge(val1, val2, val3):
    """Compute first defined source of options."""

    if val1 is not None:
        return val1
    if val2 is not None:
        return val2
    return val3

################
# Options to specify input and output directories

def directory_parser(parser):
    """Parse options giving input and output directories"""

    parser.add_argument('--srcdir', metavar="DIR",
                        help='Path to source directory')
    parser.add_argument('--wsdir', metavar="DIR",
                        help='Path to workspace directory')
    parser.add_argument('--outdir', metavar="DIR",
                        help='Path to output directory')
    parser.add_argument('--blddir', metavar="DIR",
                        help='Path to source directory to build goto')
    return parser

def directory_merge(opts, args, config):
    """Merge options giving input and output directories"""

    opts['srcdir'] = args.srcdir or config.get('srcdir')
    opts['wsdir'] = args.wsdir or config.get('wsdir')

    if opts['srcdir'] is None or opts['wsdir'] is None:
        abort("Must specify both --srcdir and --wsdir")

    opts['outdir'] = (args.outdir or config.get('outdir') or
                      opts['wsdir'])

    opts['srcdir'] = os.path.abspath(opts['srcdir'])
    opts['wsdir'] = os.path.abspath(opts['wsdir'])
    opts['outdir'] = os.path.abspath(opts['outdir'])

    opts['blddir'] = args.blddir or config.get('blddir') or opts['srcdir']

    return opts

################
# Options to specify S3 buckets and paths

def bucket_parser(parser):
    """Parse options giving S3 bucket and object names"""

    parser.add_argument('--bucket', metavar="BKT",
                        help='S3 path to bucket for directories')
    parser.add_argument('--srcbucket', metavar="BKT",
                        help='S3 path to bucket for source directory')
    parser.add_argument('--wsbucket', metavar="BKT",
                        help='S3 path to bucket for workspace directory')
    parser.add_argument('--outbucket', metavar="BKT",
                        help='S3 path to bucket for output directory')
    parser.add_argument('--srctarfile', metavar="OBJ",
                        help='S3 path to tar file for source directory')
    return parser

def bucket_merge(opts, args, config):
    """Merge options giving S3 bucket and object names"""

    opts['bucket'] = args.bucket or config.get('bucket', None) or 'cbmc'
    opts['srcbucket'] = (args.srcbucket or config.get('srcbucket', None) or
                         "{}/{}/src".format(opts['bucket'], opts['jobname']))
    opts['wsbucket'] = (args.wsbucket or config.get('wsbucket', None) or
                        "{}/{}/ws".format(opts['bucket'], opts['jobname']))
    opts['outbucket'] = (args.outbucket or config.get('outbucket', None) or
                         "{}/{}/out".format(opts['bucket'], opts['jobname']))
    opts['srctarfile'] = args.srctarfile or config.get('srctarfile', None)

    if not s3.is_path(opts['srcbucket']):
        abort("Not a valid S3 bucket or object: {}"
              .format(opts['srcbucket']))
    if not s3.is_path(opts['wsbucket']):
        abort("Not a valid S3 bucket or object: {}"
              .format(opts['wsbucket']))
    if not s3.is_path(opts['outbucket']):
        abort("Not a valid S3 bucket or object: {}"
              .format(opts['outbucket']))

    bkt = s3.bucket_name(opts['srcbucket'])
    if not s3.bucket_exists(bkt, region=opts['region']):
        abort("Bucket does not exist: {}".format(bkt))
    bkt = s3.bucket_name(opts['wsbucket'])
    if not s3.bucket_exists(bkt, region=opts['region']):
        abort("Bucket does not exist: {}".format(bkt))
    bkt = s3.bucket_name(opts['outbucket'])
    if not s3.bucket_exists(bkt, region=opts['region']):
        abort("Bucket does not exist: {}".format(bkt))

    opts['srcbucket'] = s3.path_url(opts['srcbucket'])
    opts['wsbucket'] = s3.path_url(opts['wsbucket'])
    opts['outbucket'] = s3.path_url(opts['outbucket'])

    return opts

################
# Packages

def package_parser(parser):
    """Parse options giving package locations"""
    parser.add_argument('--pkgbucket', metavar="BKT",
                        help='Path to S3 bucket for cbmc packages')

    parser.add_argument('--cbmcpkg', metavar="PKG",
                        help='Name of cbmc package in package bucket')
    parser.add_argument('--batchpkg', metavar="PKG",
                        help='Name of cbmc-batch package in package bucket')
    parser.add_argument('--viewerpkg', metavar="PKG",
                        help='Name of cbmc-viewer package in package bucket')

    return parser

def package_merge(opts, args, config):
    """Merge options giving package locations"""

    opts['pkgbucket'] = (args.pkgbucket or config.get('pkgbucket', None) or
                         "{}/package".format(opts['bucket']))

    if not s3.is_path(opts['pkgbucket']):
        abort("Not a valid S3 bucket or object: {}"
              .format(opts['pkgbucket']))

    bkt = s3.bucket_name(opts['pkgbucket'])
    if not s3.bucket_exists(bkt, region=opts['region']):
        abort("Bucket does not exist: {}".format(bkt))
    opts['pkgbucket'] = s3.path_url(opts['pkgbucket'])

    opts['cbmcpkg'] = \
      args.cbmcpkg or config.get('cbmcpkg', None) or 'cbmc'
    opts['batchpkg'] = \
      args.batchpkg or config.get('batchpkg', None) or 'cbmc-batch'
    opts['viewerpkg'] = \
      args.viewerpkg or config.get('viewerpkg', None) or 'cbmc-viewer'

    if not re.search(r'(\.tar$|\.tar\.)', opts['cbmcpkg'], re.IGNORECASE):
        opts['cbmcpkg'] += ".tar.gz"
    if not re.search(r'(\.tar$|\.tar\.)', opts['batchpkg'], re.IGNORECASE):
        opts['batchpkg'] += ".tar.gz"
    if not re.search(r'(\.tar$|\.tar\.)', opts['viewerpkg'], re.IGNORECASE):
        opts['viewerpkg'] += ".tar.gz"

    path = '{}/{}'.format(opts['pkgbucket'], opts['cbmcpkg'])
    if not s3.path_exists(path, region=opts['region']):
        abort("S3 package not found: {}".format(path))
    path = '{}/{}'.format(opts['pkgbucket'], opts['batchpkg'])
    if not s3.path_exists(path, region=opts['region']):
        abort("S3 package not found: {}".format(path))
    path = '{}/{}'.format(opts['pkgbucket'], opts['viewerpkg'])
    if not s3.path_exists(path, region=opts['region']):
        abort("S3 package not found: {}".format(path))

    return opts

################
# Options to CBMC

def cbmcflags_parser(parser):
    """Parse options for CBMC itself"""

    parser.add_argument('--goto', metavar="GOTO",
                        help='Name for the goto program for CBMC')
    parser.add_argument('--cbmcflags', metavar="OPTS",
                        help='Command line options for CBMC (encoded)')
    return parser

def cbmcflags_merge(opts, args, config):
    """Merge options for CBMC itself"""

    opts['goto'] = args.goto or config.get('goto', None) or "main.goto"

    options = args.cbmcflags or config.get('cbmcflags', None)
    if options is None or isinstance(options, dict):
        opts['cbmcflags'] = options
    else:
        opts['cbmcflags'] = options_str2dict(options.strip('='))
    return opts

################
# Options to specify goto build flags

def build_parser(parser):
    """Parse options for building the goto program"""

    parser.add_argument('--cflags', metavar="STR",
                        help='Compiler flags to build the goto program')
    parser.add_argument('--ldflags', metavar="STR",
                        help='Load flags to build the goto program')
    return parser

def build_merge(opts, args, config):
    """Merge options for building the goto program"""

    cflags = args.cflags or config.get('cflags', None)
    ldflags = args.ldflags or config.get('ldflags', None)
    if cflags is None or isinstance(cflags, dict):
        opts['cflags'] = cflags
    else:
        opts['cflags'] = options_str2dict(cflags.strip('='))
    if ldflags is None or isinstance(ldflags, dict):
        opts['ldflags'] = ldflags
    else:
        opts['ldflags'] = options_str2dict(ldflags.strip('='))
    return opts

################
# Options to specify AWS Batch resources

def job_name_parser(parser):
    """Parse AWS Batch job name options"""

    parser.add_argument('--jobname', metavar="NAME",
                        help='AWS Batch job name')
    parser.add_argument('--jobprefix', metavar="STR",
                        help='Prefix for constructing AWS Batch job name')
    parser.add_argument('--taskname', metavar="STR",
                        help='Verification task identifier across runs')
    return parser

def job_definition_parser(parser):
    """Parse AWS Batch job defitions options"""

    parser.add_argument('--jobdef', metavar="DFN",
                        help='AWS Batch job definition name')
    parser.add_argument('--jobos', metavar="OS",
                        help='Default operating system for batch job')
    parser.add_argument('--jobcc', metavar="CC",
                        help='Default C compiler for batch job')
    return parser

def job_queue_parser(parser):
    """Parse AWS Batch job queue options"""

    parser.add_argument('--jobqueue', metavar="QUEUE",
                        help='AWS Batch job queue name')
    return parser

def region_parser(parser):
    """Parse AWS region option"""

    parser.add_argument('--region', metavar='REGION',
                        dest='region',
                        help="Region that AWS Batch is running in")

    return parser

def aws_batch_parser(parser):
    """Parse options for running AWS Batch"""

    job_name_parser(parser)
    job_definition_parser(parser)
    job_queue_parser(parser)

    parser.add_argument('--build-memory', metavar='MB',
                        dest='build_memory',
                        help="Memory in MB for the CBMC build phase")
    parser.add_argument('--property-memory', metavar='MB',
                        dest='property_memory',
                        help="Memory in MB for the CBMC property phase")
    parser.add_argument('--coverage-memory', metavar='MB',
                        dest='coverage_memory',
                        help="Memory in MB for the CBMC coverage phase")
    parser.add_argument('--report-memory', metavar='MB',
                        dest='report_memory',
                        help="Memory in MB for the CBMC report phase")

    region_parser(parser)

    return parser

def job_name_merge(opts, args, config):
    """Merge AWS Batch job name options"""

    def timestamp():
        """Generate a printable timestamp for job names"""

        gmt = time.gmtime()
        return ("{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}"
                .format(gmt.tm_year, gmt.tm_mon, gmt.tm_mday,
                        gmt.tm_hour, gmt.tm_min, gmt.tm_sec))

    opts['jobprefix'] = (args.jobprefix or config.get('jobprefix', None) or
                         'cbmc')
    opts['jobname'] = (args.jobname or config.get('jobname', None) or
                       '{}-{}'.format(opts['jobprefix'], timestamp()))
    opts['taskname'] = (args.taskname or config.get('taskname') or
                        opts['jobname'])
    return opts

def job_definition_merge(opts, args, config):
    """Merge AWS Batch job definition options"""

    # The operating system and compiler determine the job definition to use
    opts['jobdef'] = args.jobdef or config.get('jobdef', None)
    opts['jobos'] = args.jobos or config.get('jobos', None) or 'ubuntu14'
    opts['jobcc'] = args.jobcc or config.get('jobcc', None) or 'gcc'

    if opts['jobdef'] is None or opts['jobdef'] == "default":
        opts['jobdef'] = "{}-{}".format(opts['jobos'], opts['jobcc'])

    # Translate nicknames for job definitions into real names
    if opts['jobdef'] == "ubuntu14-gcc":
        opts['jobdef'] = "CBMCJobUbuntu14Gcc"
    elif opts['jobdef'] == "ubuntu14":
        opts['jobdef'] = "CBMCJobUbuntu14Gcc"
    if opts['jobdef'] == "ubuntu16-gcc":
        opts['jobdef'] = "CBMCJobUbuntu16Gcc"
    elif opts['jobdef'] == "ubuntu16":
        opts['jobdef'] = "CBMCJobUbuntu16Gcc"

    return opts

def job_queue_merge(opts, args, config):
    """Merge AWS Batch job queue options"""

    opts['jobqueue'] = args.jobqueue or config.get('jobqueue', None)

    # Translate nicknames for job queues into real names
    if opts['jobqueue'] is None or opts['jobqueue'] == "default":
        opts['jobqueue'] = "CBMCJobQueue"

    return opts

def region_merge(opts, args, config):
    """Merge AWS region options"""

    default_region = boto3.session.Session().region_name
    if default_region is None:
        default_region = 'us-east-1'
    opts['region'] = merge(args.region, config.get('region'), default_region)

    return opts

def aws_batch_merge(opts, args, config):
    """Merge options for running AWS Batch"""

    opts = job_name_merge(opts, args, config)
    opts = job_definition_merge(opts, args, config)
    opts = job_queue_merge(opts, args, config)

    opts['build_memory'] = int(merge(args.build_memory,
                                     config.get('build_memory'),
                                     8000))
    opts['property_memory'] = int(merge(args.property_memory,
                                        config.get('property_memory'),
                                        16000))
    opts['coverage_memory'] = int(merge(args.coverage_memory,
                                        config.get('coverage_memory'),
                                        16000))
    opts['report_memory'] = int(merge(args.report_memory,
                                      config.get('report_memory'),
                                      8000))

    opts = region_merge(opts, args, config)

    return opts

################
# Options to specify a config file

def config_parser(parser):
    """Parse options giving configuration file name"""

    parser.add_argument('--json', metavar="FILE",
                        help='JSON file of command line options')
    parser.add_argument('--yaml', metavar="FILE",
                        help='YAML file of command line options')
    parser.add_argument('--jsons', metavar="STR",
                        help='JSON string of command line options')
    return parser

# Nothing to merge because these read the configuration files giving
# the values to merge with command line options

################
# Options specific to the cbmc-status script

def cbmc_status_parser(parser):
    """Parse options specific to the cbmc-status program"""

    parser.add_argument('--monitor', default=False, action="store_true",
                        help='Monitor job status continuously until done')
    parser.add_argument('--jobid', metavar="ID",
                        help='AWS Batch job id')
    job_name_parser(parser)
    job_queue_parser(parser)
    return parser

def cbmc_status_merge(opts, args, config):
    """Merge options specific to the cbmc-status program"""

    opts['monitor'] = merge(args.monitor, config.get('monitor', None), False)
    opts['jobid'] = args.jobid or config.get('jobid', None)
    opts = job_name_merge(opts, args, config)
    opts = job_queue_merge(opts, args, config)
    return opts

################
# Options specific to the docker script run in the container
# Options should be renamed from dobuild to dockerbuild, etc.

def container_parser(parser):
    """Parse options specific to the docker script run in the container"""

    parser.add_argument('--dobuild', action="store_true", default=None,
                        help='Do the CBMC build phase')
    parser.add_argument('--doproperty', action="store_true", default=None,
                        help='Do the CBMC property phase')
    parser.add_argument('--docoverage', action="store_true", default=None,
                        help='Do the CBMC coverage phase')
    parser.add_argument('--doreport', action="store_true", default=None,
                        help='Do the CBMC report phase')

    return parser

def container_merge(opts, args, config):
    """Merge options specific to the docker script run in the container"""

    def more_than_one_set(bits):
        """Test for more than one boolean value True."""
        count = 0
        for bit in bits:
            count += int(bit)
        return count > 1

    opts['dobuild'] = merge(args.dobuild, config.get('dobuild', None), False)
    opts['doproperty'] = merge(args.doproperty,
                               config.get('doproperty', None), False)
    opts['docoverage'] = merge(args.docoverage,
                               config.get('docoverage', None), False)
    opts['doreport'] = merge(args.doreport, config.get('doreport', None), False)

    if more_than_one_set([opts['dobuild'], opts['doproperty'],
                          opts['docoverage'], opts['doreport']]):
        abort("Too many commands passed to docker container.")

    return opts

################################################################

def phase_parser(parser):
    """Parse options specific which cbmc phase to run."""

    parser.add_argument('--build', dest='build', default=None,
                        action="store_true",
                        help='Do the CBMC build phase')
    parser.add_argument('--no-build', dest='build', default=None,
                        action="store_false",
                        help="Don't the CBMC build phase")
    parser.add_argument('--property', dest='property', default=None,
                        action="store_true",
                        help='Do the CBMC property phase')
    parser.add_argument('--no-property', dest='property', default=None,
                        action="store_false",
                        help="Don't the CBMC property phase")
    parser.add_argument('--coverage', dest='coverage', default=None,
                        action="store_true",
                        help='Do the CBMC coverage phase')
    parser.add_argument('--no-coverage', dest='coverage', default=None,
                        action="store_false",
                        help="Don't the CBMC coverage phase")
    parser.add_argument('--report', dest='report', default=None,
                        action="store_true",
                        help='Do the CBMC report phase')
    parser.add_argument('--no-report', dest='report', default=None,
                        action="store_false",
                        help="Don't the CBMC report phase")

    parser.add_argument('--copysrc', dest='copysrc', default=None,
                        action="store_true",
                        help='Copy source directory to bucket')
    parser.add_argument('--no-copysrc', dest='copysrc', default=None,
                        action="store_false",
                        help="Don't copy source directory to bucket")
    parser.add_argument('--copyws', dest='copyws', default=None,
                        action="store_true",
                        help='Copy workspace directory to bucket')
    parser.add_argument('--no-copyws', dest='copyws', default=None,
                        action="store_false",
                        help="Don't copy workspace directory to bucket")
    parser.add_argument('--copyout', dest='copyout', default=None,
                        action="store_true",
                        help='Copy output directory to bucket')
    parser.add_argument('--no-copyout', dest='copyout', default=None,
                        action="store_false",
                        help="Don't copy output directory to bucket")

    return parser

def phase_merge(opts, args, config):
    """Merge options specific which cbmc phase to run."""

    opts['build'] = merge(args.build, config.get('build', None), True)
    opts['property'] = merge(args.property, config.get('property', None), True)
    opts['coverage'] = merge(args.coverage, config.get('coverage', None), True)
    opts['report'] = merge(args.report, config.get('report', None), True)
    opts['copysrc'] = merge(args.copysrc, config.get('copysrc', None),
                            opts['build'] or opts['report'])
    opts['copyws'] = merge(args.copyws, config.get('copyws', None), True)
    opts['copyout'] = merge(args.copyout, config.get('copyout', None), False)

    return opts

################################################################

def other_parser(parser):
    """Parse other miscellaneous options"""

    parser.add_argument('--no-file-output', action="store_true",
                        help="Don't generate JSON, YAML, Makefile files")
    return parser

def other_merge(opts, args, config):
    """Merge other miscellaneous options"""

    opts['no-file-output'] = merge(args.no_file_output,
                                   config.get('no-file-output', None),
                                   False)
    return opts

################################################################


def parse_config(args):
    """Parse command line arguments from a config file."""

    if args.yaml and args.json:
        abort("Can't give both JSON and YAML configuration files.")

    if args.yaml:
        return parse_yaml_config(args.yaml)
    if args.json:
        return parse_json_config(args.json)
    if args.jsons:
        return parse_jsons_config(args.jsons)

    return {}

def parse_yaml_config(config):
    """Parse command line arguments from a YAML config file."""

    with open(config, 'r') as fptr:
        return cleanup_config(yaml.load(fptr))

def parse_json_config(config):
    """Parse command line arguments from a JSON config file."""

    with open(config, 'r') as fptr:
        return cleanup_config(json.load(fptr))

def parse_jsons_config(string):
    """Parse command line arguments from a JSON config string."""

    return json.loads(string)

def cleanup_config(val):
    """Interpret string values found in YAML config file."""

    if val == "None":
        return None
    if isinstance(val, dict):
        new = {}
        for key in val:
            new[key] = cleanup_config(val[key])
        return new
    if isinstance(val, list):
        new = []
        for key in val:
            new.append(cleanup_config(key))
        return new
    return str2int(val)

################################################################
# Translate between --cbmcflags string used on the command line and
# the cbmcflags dictionary used in the config file.
#
# There are two encodings in the string to pay attention to.  The list
# of whitespace-separated strings given to cbmc on the command line
# are separated by ';'.  For the special case of the --unwindset
# command line option, the name-integer pairs are separated by ',' and
# the name and integer themselves are separated by ':'.

def str2int(string):
    """Make an integer from a string whenever possible"""

    try:
        return int(string)
    except (TypeError, ValueError):
        return string


def unwindset_str2words(uwd):
    """Translate unwindset string to loop name:count words"""
    return uwd.split(',')

def unwindset_words2str(uwd):
    """Translate unwindset loop name:count words to a string"""
    return ','.join(uwd)

def unwindset_words2dict(uwd):
    """Translate unwindset loop name:count words to a dictionary"""
    uwd_dict = {}
    for pair in uwd:
        name, count = pair.split(':')
        uwd_dict[name] = str2int(count)
    return uwd_dict

def unwindset_dict2words(uwd):
    """Translate unwindset dictionary to loop name:count words"""
    uwd_words = []
    for name in uwd:
        pair = "{}:{}".format(name, uwd[name])
        uwd_words.append(pair)
    return uwd_words

def unwindset_str2dict(opts):
    """Translate unwindset string to dictionary"""
    return unwindset_words2dict(unwindset_str2words(opts))

def unwindset_dict2str(opts):
    """Translate unwindset dictionary to string"""
    return unwindset_words2str(unwindset_dict2words(opts))


def options_str2words(opts):
    """Translation cbmc options string to command line words"""
    return opts.split(';')

def options_words2str(opts):
    """Translation cbmc option command line words to string"""
    opts2 = [str(opt) for opt in opts]
    return ';'.join(opts2)

def options_words2dict(opts):
    """Translation cbmc option command line words to dictionary"""
    opt_words = opts or []
    opt_dict = {}

    while opt_words:
        key = opt_words[0]
        opt_words = opt_words[1:]
        if not opt_words:
            opt_dict[key] = None
            break
        val = opt_words[0]
        if val.startswith('--'):
            opt_dict[key] = None
            continue
        opt_dict[key] = str2int(val)
        opt_words = opt_words[1:]

    unwindset = opt_dict.get('--unwindset', None)
    if unwindset is not None:
        opt_dict['--unwindset'] = unwindset_str2dict(unwindset)

    return opt_dict

def options_dict2words(opts):
    """Translation cbmc options dictionary to command line words"""
    opt_dict = dict(opts or {})
    opt_words = []

    unwindset = opt_dict.get('--unwindset', None)
    if unwindset is not None:
        opt_dict['--unwindset'] = unwindset_dict2str(unwindset)

    for key in opt_dict:
        opt_words.append(str(key))
        if opt_dict[key] is not None:
            opt_words.append(str(opt_dict[key]))

    return opt_words

def options_str2dict(opts):
    """Translation cbmc options string to dictionary"""
    if opts is None:
        return None
    if isinstance(opts, dict):
        return opts
    return options_words2dict(options_str2words(opts))

def options_dict2str(opts):
    """Translation cbmc options dictionary to string"""
    if opts is None:
        return None
    if isinstance(opts, str):
        return opts
    return options_words2str(options_dict2words(opts))

################################################################

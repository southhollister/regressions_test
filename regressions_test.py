#!/usr/bin/python
"""
Regressions testing module for core script projects.

positional arguments:
  project      name of project to be regressions tested
  environment  environment in which to run regressions tests

optional arguments:
  -h, --help   show this help message and exit
  --all        if present run all rts for <project>

"""
# TODO https://stackoverflow.com/questions/24892396/py-test-logging-messages-and-test-results-assertions-into-a-single-file
# TODO https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option

import re
import sys
import urllib2
import pytest
import json
import argparse
import os
from engine_request import EngineRequest


__version__ = 2


# setup command line args
def create_parser():
    parser = argparse.ArgumentParser(description='Regressions testing module for core script projects.')
    # TODO add arguments to update config files. i.e., new version number
    # TODO add arguments to add/modify endpoints
    parser.add_argument('project', help='name of project to be regressions tested')
    parser.add_argument('-e', '--environment', default='staging', help='environment in which to run regressions tests')
    parser.add_argument('--all', dest='ALL', action='store_true', help='if present run all rts for <project>')
    parser.add_argument('-V', '--version_number', type=int, default=0, metavar='version_number', help='Version number of kb to be tested.')
    commands = parser.add_subparsers()
    parser.set_defaults(func=main)
    return parser.parse_args(sys.argv[1:])


#
# **************** Main ****************
#
def main():
    """
    Default functionality

    """
    # if version number is in command line args reset version number in project config file
    if args.version_number != 0:
        update_version_number(args.version_number)

    else:
        # if captured version number is valid
        try:
            v_num = input("Enter kb version number (Press enter to re-run last test): ")
            update_version_number(int(v_num))
        except ValueError:
            print 'Version number must be an integer.'
            print 'Testing against last saved version.'
        except SyntaxError:
            pass

    try:
        # set up project params
        config = json.loads(open('project_configs/%s.json' % args.project.lower()).read())
    except ValueError, e:
        print 'Error while reading config file: %s' % e
    except IOError, e:
        print '%s; Be sure regressions tests have been set up for this project.'

    project = config.get('name')

    endpoint = config.get('endpoints').get(args.environment)
    print 'Testing project: %s; Using endpoint: %s' % (project, args.environment)
    # Determine which tests to run based on args entered and project name
    flags = {
        'BACK_TEXT': 'custom_back_text_values' in config,
        'ALL': args.ALL,
        'BLANK_CONNECTORS': 'blank_connector_values' in config,
        'SEMANTIC': config.get('semantic_input', '') != '',
        'LIVE_CHAT': 'live_chat_values' in config,
    }

    # make first request to the engine. this response is used in most of those tests
    try:
        req = EngineRequest(endpoint).make_request()
    except urllib2.HTTPError, e:
        if e.code == 404:
            sys.exit('Bad Endpoint: %s' % endpoint)
        else:
            sys.exit(e)

    # if response returns correctly run tests
    if req.get('ident'):
        # TODO add kb version number to print statement on test initialization.
        print 'Session initiated targeting endpoint: %s' % endpoint
        print 'Session Id: %s' % req['ident']
        params = {'ident': req['ident'],
                  'entry': ''}
    else:
        print 'Failed to initiate session. Response: %s' % req

    # list of params to pass pytest; add custom tests if available for project
    tests = ['-v', '--params=%s' % json.dumps(params), 'tests/main_tests.py']
    custom_tests = ['%s' % f for f in os.listdir(os.getcwd()) if project.lower() in f.lower()]
    tests.extend(custom_tests)
    print tests

    pytest.main(tests)


def add_endpoint():
    pass


def update_version_number(num):
    """
    Update version number in json config file.
    :param num: int; new kb version number to be updated in project config file
    :return:
    """
    with open('project_configs/%s.json' % args.project.lower(), 'r') as f:
        new_json = json.loads(f.read())

    new_json['version_number'] = str(num)

    with open('project_configs/%s.json' % args.project.lower(), 'w') as f:
        f.write(json.dumps(new_json, indent=2, sort_keys=True))


if __name__ == '__main__':

    args = create_parser()
    args.func()


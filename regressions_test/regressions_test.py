#!/usr/bin/python
"""
Usage:
    regressions_test
    regressions_test [-h | --help]
    regressions_test [-h] test PROJECT ENVIRONMENT
    regressions_test [-h] update_version PROJECT VERSION_NUMBER
    regressions_test [-h] add_endpoint PROJECT NAME URL

Commands:
    test            Run regression tests on PROJECT using ENVIRONMENT endpoint
    update_version  Update kb version number to VERSION_NUMBER for regressions test
    add_endpoint    Add URL as endpoint in PROJECT's config file under NAME
"""

# TODO https://stackoverflow.com/questions/24892396/py-test-logging-messages-and-test-results-assertions-into-a-single-file

import sys
import urllib2
import pytest
import json
import argparse
import os
from engine_request import EngineRequest


__version__ = 3.5


def create_parser():
    """
    Create argparser object.
    :return: argparser
    """
    parser = argparse.ArgumentParser(
        add_help=False
    )
    parser.add_argument('project', help='Name of project.')

    main_parser = argparse.ArgumentParser(description='Regressions testing module for core script projects.',
                                          usage='regressions_test [-h] COMMAND PROJECT ARGS')
    commands = main_parser.add_subparsers(metavar='COMMANDS')

    update_version = commands.add_parser('update_version',
                                         parents=[parser],
                                         help='Update kb version number regressions tests are run against.')
    update_version.add_argument('version_number', type=int, help='Version number.')
    update_version.set_defaults(func=update_version_number)

    _add_endpoint = commands.add_parser('add_endpoint',
                                        parents=[parser],
                                        help='Add endpoint to the list of config endpoints for project.')
    _add_endpoint.add_argument('name', type=str, help='Name of endpoint. i.e. "staging".')
    _add_endpoint.add_argument('url', type=str, help='Link to endpoint')
    _add_endpoint.set_defaults(func=add_endpoint)

    tester = commands.add_parser('test',
                                 parents=[parser],
                                 help='Run tests')
    tester.add_argument('environment', nargs='?', default='staging', help='Environment in which to run regressions tests')
    # tester.add_argument('--all', dest='ALL', action='store_true', help='if present run all rts for <project>')
    tester.add_argument('-V', '--version_number', type=int, default=0, metavar='version_number',
                        help='Version number of kb to be tested.')
    tester.add_argument('-a', dest='all', action='store_true', help='Run tests on all known endpoints.')
    tester.set_defaults(func=test)

    _show = commands.add_parser('show',
                                parents=[parser],
                                help='Print list of selected config vars.')
    _show.add_argument('var', help='Config var to retrieve.')
    _show.set_defaults(func=show)

    return main_parser.parse_args()


#
# **************** Main ****************
#
def main():
    """
    Default functionality
    """

    args = create_parser()
    args.func(args=args)


def test(args):
    """
    Run tests
    :param args: Pertinent args: version_number, environment, project.
    :return:
    """
    # if captured version number is valid rn tests using that if not prompt user to update
    if args.version_number == 0:
        try:
            v_num = input("Enter kb version number (Press enter to re-run last test): ")
            update_version_number(int(v_num), args)
        except ValueError:
            print 'Version number must be an integer.'
            print 'Testing against last saved version.'
        except SyntaxError:
            pass

    directory = os.path.dirname(os.path.abspath(__file__))
    try:
        # set up project params
        config = json.loads(open('%s/project_configs/%s.json' % (directory,
                                                                 args.project.lower())).read())
    except ValueError, e:
        print 'Error while reading config file: %s' % e
    except IOError, e:
        print '%s; Be sure regressions tests have been set up for this project.' % e
        print os.path.dirname(os.path.abspath(__file__))

    project = config.get('name')
    # Gather endpoints
    if not args.all and config.get('endpoints').get(args.environment):
        endpoints = [{
            'ep': config['endpoints'][args.environment],
            'env': args.environment
        }]
    else:
        endpoints = [{'ep': ep, 'env': env} for env, ep in config.get('endpoints', {}).items()]

    # Run tests for each endpoint available requested
    for test_point in endpoints:
        environment = test_point['env']
        endpoint = test_point['ep']
        print 'Testing project: %s; Using endpoint: %s' % (project, environment)
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
        tests = ['-v',
                 '--project=%s' % project,
                 '--environment=%s' % environment,
                 '--params=%s' % json.dumps(params),
                 '%s/tests/main_tests.py' % directory]
        custom_tests = ['%s' % f for f in os.listdir(os.getcwd()) if project.lower() in f.lower()]
        tests.extend(custom_tests)
        print tests

        pytest.main(tests)


def show(args):
    """
    Print list of selected config vars.
    :param args: Pertinent args: project, var
    """
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_configs', '%s.json' % args.project.lower())
    with open(directory, 'r') as f:
        config = json.loads(f.read())

    if not config.get(args.var):
        print 'Error: No such config variable: %s' % args.var
        print config.keys()
        return

    if type(config[args.var]) == dict:
        print '%s:' % args.var
        for k,v in config[args.var].items(): print k, v

    else: print config.get(args.var, 'Error')


def add_endpoint(args):
    """
    Add endpoint to project
    :param args: Pertinent args: project, name, url.
    """

    with open('project_configs/%s.json' % args.project.lower(), 'r') as f:
        new_json = json.loads(f.read())

    new_json['endpoints'][args.name] = args.url

    with open('project_configs/%s.json' % args.project.lower(), 'w') as f:
        f.write(json.dumps(new_json, indent=2, sort_keys=True))

    print 'Added endpoint', args.name, args.url, 'to',  args.project


def update_version_number(num=None, args=None):
    """
    Update version number in json config file.
    :param args: Pertinent args: project, version_number
    :param num: int; new kb version number to be updated in project config file
    :return:
    """

    num = num if num else args.version_number

    with open('project_configs/%s.json' % args.project.lower(), 'r') as f:
        new_json = json.loads(f.read())

    new_json['version_number'] = str(num)

    with open('project_configs/%s.json' % args.project.lower(), 'w') as f:
        f.write(json.dumps(new_json, indent=2, sort_keys=True))

    print 'Version number updated to:', num

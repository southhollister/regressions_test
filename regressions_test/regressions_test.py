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
# TODO Create PII Tests
# TODO add create new project command

import sys
import urllib2
import pytest
import json
import argparse
import os
from engine_request import EngineRequest
from shutil import copy
from collections import namedtuple


# Constants
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Get version number from version file
d = os.path.join(*os.path.split(DIRECTORY)[:-1])
try:
    with open(os.path.join(d, 'VERSION'), 'rb') as f:
        __version__ = f.read().decode('utf-8').strip()
except Exception, e:
    __version__ = "ERROR"
    print(d)
    print(e)


def create_parser():
    """
    Create argparser object.
    :return: argparser
    """
    # Parent parser for subparsers
    parser = argparse.ArgumentParser(
        add_help=False
    )
    parser.add_argument('project', help='Name of project.')

    # Main parser; has commands sub parser
    main_parser = argparse.ArgumentParser(description='Regressions testing module for core script projects.')
    main_parser.add_argument('--version',
                             action='version',
                             version='%(prog)s-' + __version__,
                             help='Show version number of currently installed package.')

    commands = main_parser.add_subparsers(metavar='COMMANDS')

    # List projects
    _list_projects = commands.add_parser('list_projects',
                                         help='Print a list of all currently testable projects')
    _list_projects.set_defaults(func=list_projects)

    # Update version command
    update_version = commands.add_parser('update_version',
                                         parents=[parser],
                                         help='Update kb version number regressions tests are run against.')
    update_version.add_argument('version_number', type=int, help='Version number.')
    update_version.set_defaults(func=update_version_number)

    # Add endpoint command
    _add_endpoint = commands.add_parser('add_endpoint',
                                        parents=[parser],
                                        help='Add endpoint to the list of config endpoints for project.')
    _add_endpoint.add_argument('name', type=str, help='Name of endpoint. i.e. "staging".')
    _add_endpoint.add_argument('url', type=str, help='Link to endpoint')
    _add_endpoint.set_defaults(func=add_endpoint)

    # test command
    tester = commands.add_parser('test',
                                 parents=[parser],
                                 help='Run tests')
    tester.add_argument('environment', nargs='?', default='staging',
                        help='Environment in which to run regressions tests')
    # tester.add_argument('--all', dest='ALL', action='store_true', help='if present run all rts for <project>')
    tester.add_argument('-V', '--version_number', type=int, default=0, metavar='version_number',
                        help='Version number of kb to be tested.')
    tester.add_argument('-a', dest='all', action='store_true', help='Run tests on all known endpoints.')
    tester.set_defaults(func=test)

    # show command
    _show = commands.add_parser('show',
                                parents=[parser],
                                help='Print list of selected config vars.')
    # TODO if var == all print all config vars
    _show.add_argument('var', help='Config var to retrieve. Use "all" to view complete config.')
    _show.set_defaults(func=show)

    _update_config = commands.add_parser('update_config',
                                         parents=[parser],
                                         help='Update config var from command line or from file.')
    _update_config.add_argument('json', type=str, default=None, help='Config json')
    _update_config.add_argument('-f', '--from_file', action='store_true', dest='FROM_FILE',
                                help='Flag indicates json argument is a json file.')
    _update_config.add_argument('-o', '--overwrite', action='store_true', dest='OVERWRITE',
                                help="""
                                    When present keys that currently exist in config will be overwritten indiscriminately.
                                    If keys value is a dictionary the dictionary will replace the dictionary of that key in the config file.
                                    """
                                )
    _update_config.set_defaults(func=update_config)

    # create project command
    _create_project = commands.add_parser('create_project',
                                          help='Create new project to be tested')
    config_args = _create_project.add_mutually_exclusive_group(required=False)
    config_args.add_argument('-n', '--blank_config', action='store_true', dest='BLANK_CONFIG',
                             help="""When present no values will be added to the config file and user will not be prompted for them.
                             Variables can be added later via the update_config command.""")
    config_args.add_argument('-f', '--config_file', type=argparse.FileType(), default=None,
                             help="JSON file to be used as config file. File must at least contain 'name' value. "
                                  "File is copied to project_configs directory and renamed as <project>.json.")
    config_args.add_argument('-c', '--clone_project_config', nargs=2, type=str, metavar='PROJECT_NAME', default=None,
                             help="Clone another projects config file, replacing name value with NEW_PROJECT_NAME.")
    _create_project.add_argument('-t', '--custom_tests_file', type=argparse.FileType('r'), default=None,
                                 help='Python file containing custom tests')
    _create_project.set_defaults(func=create_project)

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

    try:
        # set up project params
        config = json.loads(open('%s/project_configs/%s.json' % (DIRECTORY,
                                                                 args.project.lower())).read())
    except ValueError, e:
        print 'Error while reading config file: %s' % e
    except IOError, e:
        print '%s; Be sure regressions tests have been set up for this project.' % e
        print DIRECTORY

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
                 '%s/tests/main_tests.py' % DIRECTORY]
        custom_test_dir = os.path.join(DIRECTORY, 'tests')
        custom_tests = [os.path.join(custom_test_dir, f) for f in os.listdir(custom_test_dir) if project.lower() in f.lower()]
        tests.extend(custom_tests)
        print tests

        pytest.main(tests)


def show(args):
    """
    Print list of selected config vars.
    :param args: Pertinent args: project, var
    """
    directory = os.path.join(DIRECTORY, 'project_configs', '%s.json' % args.project.lower())
    with open(directory, 'r') as f:
        config = json.loads(f.read())

    if args.var == 'all':
        print json.dumps(config, indent=2, sort_keys=True)
        return

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

    directory = os.path.join(DIRECTORY, 'project_configs', '%s.json' % args.project.lower())
    with open(directory, 'r') as f:
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

    directory = os.path.join(DIRECTORY, 'project_configs', '%s.json' % args.project.lower())

    with open(directory, 'r') as f:
        new_json = json.loads(f.read())

    new_json['version_number'] = str(num)

    with open(directory, 'w') as f:
        f.write(json.dumps(new_json, indent=2, sort_keys=True))

    print 'Version number updated to:', num


def update_config(args):
    """Update config variable"""

    directory = os.path.join(DIRECTORY, 'project_configs', '%s.json' % args.project.lower())

    try:
        with open(directory, 'r') as f:
            config = json.loads(f.read())
    except IOError, io:
        print('Could not load config file for %s' % args.project)
        print('ERROR: %s' % io)
        exit()

    try:
        # js = json string from a json file or raw from command line
        js = args.json if not args.FROM_FILE else open(args.json, 'r').read()
    except IOError:
        print('JSON file "%s" not found' % args.json)
        exit()

    try:
        d = json.loads(js)
        # json object must be dictionary; if captured json is of any other type raise a TypeError
        if type(d) is not dict: raise TypeError()
    except Exception, e:
        if isinstance(e, TypeError): print('TypeError: JSON object must be a dictionary.')
        elif isinstance(e, ValueError):
            print('ValueError: No JSON object could be decoded.')
            print('Check that %s is valid json.' % args.json)
        else: print('%s: %s' % (e.__repr__(), e))
        exit()

    for key, value in d.items():
        # if overwrite mode indiscriminately update config dictionary
        # else if value exists and is a dictionary prompt user;
        # append extra warning if value is dictionary as overwrite will delete previous values

        if not args.OVERWRITE and key in config and type(config[key]) is dict:
            msg = "Overwrite key: %s in config? (y/n)\nWARNING: OVERWRITE WILL DELETE ALL PREVIOUSLY SAVED VALUES\n" % key
            overwrite = 'y' in raw_input(msg).lower()

            if overwrite:
                config[key] = value
                m = 'Overwrote'
            else:
                config[key].update(value)
                m = 'Updated'
        else:
            if key in config: m = 'Updated'
            else: m = 'Added'
            config[key] = value

        print('%s %s' % (m, key))

    try:
        with open(directory, 'w') as f:
            f.write(json.dumps(config, indent=2, sort_keys=True))
    except Exception, e:
        print('%s: %s' % (e.__repr__(), e))
        exit()


def list_projects(args=None):
    """
    List all projects by reading the config files in the project_configs folder
    :return:
    """

    directory = os.path.join(DIRECTORY, 'project_configs')
    config_files = os.listdir(directory)

    files = list()
    for _file in config_files:
        with open(os.path.join(directory, _file), 'r') as f:
            js = json.loads(f.read())
            print(js.get('name', 'ERROR'))
            files.append(js.get('name', 'ERROR'))

    return files


def create_project(args):
    """
    Create a new project
    :param args:
    :return:
    """

    tests_dir = os.path.join(DIRECTORY, 'tests')
    config_dir = os.path.join(DIRECTORY, 'project_configs')

    # handle config creation based on vars
    if args.BLANK_CONFIG:
        project_name = raw_input('Project name:  ').lower().strip().replace(' ', '_')
        if not project_name: raise ValueError('Project name is required.')
        with open(os.path.join(config_dir, '%s.json' % project_name), 'w') as f:
            f.writelines(json.dumps({"name": project_name}, indent=2))

    elif args.config_file:
        try:
            config = json.loads(args.config_file.read())
            if not config:
                raise Exception('File does not contain valid json')

            if not config.get('name'):
                raise Exception('"name" is a required value')

            new_file_name = config['name'].lower().strip().replace(' ', '_')
            copy(args.config_file.name, os.path.join(config_dir, new_file_name))

        except Exception, e:
            print('%s: %s' % (type(e), e))
            print(args.config_file)

    elif args.clone_project_config:
        org_project, new_project = args.clone_project_config
        try:
            if org_project.strip() not in list_projects(): raise Exception('%s project not found.' % org_project)
            new_file_name = new_project.lower().strip().replace(' ', '_')
            copy(os.path.join(DIRECTORY, 'project_configs', '%s.json' % org_project.lower().replace(' ', '_')),
                 os.path.join(DIRECTORY, 'project_configs', '%s.json' % new_file_name))

            fake_args = namedtuple('fake_args', 'FROM_FILE, OVERWRITE, json, project')
            js = json.dumps({"name": new_project})

            update_config(fake_args(FROM_FILE=False, OVERWRITE=True, json=js, project=new_project))

        except Exception, e:
            print('%s' % e)

    # step through each config var one by one
    else:
        project_name = raw_input("Project name:  ")
        new_file_name = project_name.lower().strip().replace(' ', '_')

        semantic_input = raw_input("Semantic trigger:  ").strip()
        dtree_input = raw_input("Dtree trigger:  ").strip()

        active_close_answer_id = raw_input("Active close answer id:  ").strip()
        active_close_input = raw_input("Active close input:  ").strip()

        live_chat_inputs = list()
        more = True
        while more:
            lc_input = raw_input("Live chat input:  ").strip()
            live_chat_inputs.append(lc_input)
            more = raw_input("More live chat steps (y/n):  ").strip().lower() == 'y'

        live_chat_skill = raw_input("Live chat skill:  ")

        endpoints = {}
        more = True
        while more:
            endpoint = raw_input("Endpoint name:  ").strip()
            url = raw_input("Url:  ").strip()
            endpoints[endpoint] = url
            more = raw_input("Add endpoints (y/n):  ").strip().lower() == 'y'

        js = {
            'name': project_name,
            'semantic_input': semantic_input,
            'dtree_input': dtree_input,
            'active_close_values': {
                'answer_id': active_close_answer_id,
                'input': active_close_input
            },
            'live_chat_values': {
                'live_chat_input': live_chat_inputs,
                'live_chat_skill': live_chat_skill
            },
            'endpoints': endpoints
        }

        try:
            with open(os.path.join(config_dir, '%s.json' % new_file_name), 'w') as f:
                f.write(json.dumps(js, indent=2, sort_keys=True))

        except Exception, e:
            print(e)

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


class RegeressionsTest(object):

    def __init__(self):
        self.help = False
        print sys.argv
        self.parser = argparse.ArgumentParser(
            description='Regressions testing module for core script projects.',
            usage='regressions_test.py [-h] ([-e ENVIRONMENT] [--all] [-V version_number] | [command <args>])',
            add_help=False
        )
        # TODO add arguments to update config files. i.e., new version number
        # TODO add arguments to add/modify endpoints
        self.parser.add_argument('project', help='name of project to be regressions tested')
        commands = self.parser.add_argument_group(title='Commands', description='List of commands')
        commands.add_argument('command', nargs='?', default='main', help='Command to run. Runs tests by default.')

        print sys.argv[1:3]
        if '-h' in sys.argv or '--help' in sys.argv:
            if len(sys.argv) <= 2:
                self.main()
            elif len(sys.argv) == 3 and sys.argv[1] in [i for i in dir(self) if '__' not in i and i != 'main']:
                getattr(self, sys.argv[1])()

            self.help = True

        print self.help
        args = self.parser.parse_known_args(sys.argv[1:3])[0]
        print args
        self.project = args.project
        if args.command not in [i for i in dir(self) if '__' not in i]: #  and i != 'main'
            self.parser.print_usage()
            exit(1)
        print 'Running', args.command
        # if args.command not in [i for i in dir(self) if '__' not in i and i != 'main']:
        #     self.main()
        # else:
        getattr(self, args.command)()

    #
    # **************** Main ****************
    #
    def main(self):
        """
        Default functionality
        """
        parser = argparse.ArgumentParser(description='Run tests', parents=[self.parser])
        parser.add_argument('-e', '--environment', default='staging', help='Environment in which to run regressions tests')
        parser.add_argument('--all', dest='ALL', action='store_true', help='if present run all rts for <project>')
        parser.add_argument('-V', '--version_number', type=int, default=0, metavar='version_number', help='Version number of kb to be tested.')
        args = parser.parse_known_args()[0]

        # if version number is in command line args reset version number in project config file
        if args.version_number != 0:
            self.update_version_number(args.version_number)

        else:
            # if captured version number is valid
            try:
                v_num = input("Enter kb version number (Press enter to re-run last test): ")
                self.update_version_number(int(v_num))
            except ValueError:
                print 'Version number must be an integer.'
                print 'Testing against last saved version.'
            except SyntaxError:
                pass

        try:
            # set up project params
            config = json.loads(open('project_configs/%s.json' % self.project.lower()).read())
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
        tests = ['-v', '--project=%s' % project, '--environment=%s' % args.environment, '--params=%s' % json.dumps(params), 'tests/main_tests.py']
        custom_tests = ['%s' % f for f in os.listdir(os.getcwd()) if project.lower() in f.lower()]
        tests.extend(custom_tests)
        print tests

        pytest.main(tests)

    def add_endpoint(self):
        """
        Add endpoint to project
        """

        parser = argparse.ArgumentParser(description='Add endpoint to the list of config endpoints for project.', parents=[self.parser])
        parser.add_argument('name', type=str, help='Name of endpoint. i.e. "staging".')
        parser.add_argument('url', type=str, help='Link to endpoint')
        args = parser.parse_known_args(sys.argv[2:])[0] if not self.help else parser.parse_args(sys.argv[3:])

        with open('project_configs/%s.json' % self.project.lower(), 'r') as f:
            new_json = json.loads(f.read())

        new_json['endpoints'][args.name] = args.url

        with open('project_configs/%s.json' % self.project.lower(), 'w') as f:
            f.write(json.dumps(new_json, indent=2, sort_keys=True))

        print 'Added endpoint', args.name, args.url, 'to',  self.project

    def update_version_number(self, num=None):
        """
        Update version number in json config file.
        :param num: int; new kb version number to be updated in project config file
        :return:
        """
        args = None
        if not num:
            parser = argparse.ArgumentParser(description='Update kb version number regressions tests are run against.')
            parser.add_argument('version', type=int, help='Version number')
            args = parser.parse_known_args(sys.argv[2:])[0] if not self.help else parser.parse_args(sys.argv[3:])
            num = args.version

        with open('project_configs/%s.json' % self.project.lower(), 'r') as f:
            new_json = json.loads(f.read())

        new_json['version_number'] = str(num)

        with open('project_configs/%s.json' % self.project.lower(), 'w') as f:
            f.write(json.dumps(new_json, indent=2, sort_keys=True))

        print 'Version number updated to:', num

if __name__ == '__main__':

    RegeressionsTest()


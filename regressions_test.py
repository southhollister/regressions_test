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
# TODO look into printing test initializations and success using -s flag and print statements after all asserts in a test
import re
import sys
import urllib2
import pytest
import json
import argparse
import os
from pytest import fixture, xfail, mark
from engine_request import EngineRequest


# setup command line args
def create_parser():
    parser = argparse.ArgumentParser(description='Regressions testing module for core script projects.')
    # TODO add choices param to arguments. Choices for project based on config files available in project_configs folder
    parser.add_argument('project', help='name of project to be regressions tested')
    parser.add_argument('environment', nargs='?', default='staging', help='environment in which to run regressions tests')
    parser.add_argument('--all', dest='ALL', action='store_true', help='if present run all rts for <project>')
    return parser.parse_args(sys.argv[1:])


args = create_parser()
# set up project params
config = json.loads(open('project_configs/%s.json' % args.project.lower()).read())
project = config.get('name')
endpoint = config.get('endpoints').get(args.environment)

print 'Testing project: %s' % project

# Determine which tests to run based on args entered and project name
flags = {
    'BACK_TEXT': 'custom_back_text_values' in config,
    'ALL': args.ALL,
    'BLANK_CONNECTORS': 'blank_connector_values' in config,
    'SEMANTIC': config.get('semantic_input', '') != '',
    'LIVE_CHAT': 'live_chat_values' in config,
}
# list of params to pass pytest; add custom tests if available for project
tests = ['-v', 'regressions_test.py']
custom_tests = ['tests/%s' % f for f in os.listdir(os.path.join(os.getcwd(), 'tests')) if project.lower() in f.lower()]
tests.extend(custom_tests)
print tests

# make first request to the engine. this response is used in most of those tests
try:
    req = EngineRequest(endpoint).make_request()
except urllib2.HTTPError, e:
    if e.code == 404: sys.exit('Bad Endpoint: %s' % endpoint)
    else: sys.exit(e)

# if response returns correctly run tests
if req.get('ident'):
    # TODO add kb version number to print statement on test initialization.
    print 'Session initiated targeting endpoint: %s' % endpoint
    print 'Session Id: %s' % req['ident']
    params = {'ident': req['ident'],
              'entry': ''}

    pytest.main(tests)
else:
    print 'Failed to initiate session. Response: %s' % req


# Tests
def test_standard_template(response_keys):
    """
    Check that expected keys are returned in response template.
    :param response_keys:
    :return:
    """
    assert isinstance(req, dict)
    for key in response_keys:
        assert req.get(key, False) is not False, 'Failed on %s' % key


def test_init_standard_response_values(init_none_keys, init_value_keys):
    """
    Test that response values are as expected on INIT
    :param init_none_keys:
    :param init_value_keys:
    :return:
    """
    assert all([req[key] is None for key in init_none_keys]), '%s was %s; Expected None' % (key, req[key])
    assert all([req[key] is not None for key in init_value_keys]), '%s was unexpected None.' % key

    assert req['autosubmitmode'] == 'true'
    assert req['autosubmitwaittime'].isdigit()
    assert req['backnavdisabled'] == 'true'
    assert len(req['botanswer']) > 5
    assert 'root' in req['currentBA'].lower()
    assert 'root' in req['currentChannel'].lower()
    assert req['disableautocomplete'] == 'false'
    assert len(json.loads(req['entrysuggestions'])) >= 1
    assert req['forcesessionclose'] == 'false'
    assert req['hideuserentry'] == 'false'
    assert len(req['ident']) == 22
    assert req['livechatrequested'] == 'false'
    assert req['userentryallowed'] == 'true'
    assert len(req['userlogid']) in [9, 10], 'userlogid was %s' % req['userlogid']
    assert req['validresponse'] == 'CVUSAVA Status: Ok'


def test_live_chat(live_chat_values):
    """
    Test live chat etvs on non INIT transaction.
    :param live_chat_values:
    :return:
    """

    params['entry'] = live_chat_values['live_chat_input']
    r = EngineRequest(endpoint).make_request(params)

    # assert r.get('ident') == params['ident']
    assert r.get('livechatskill') == live_chat_values['live_chat_skill']
    assert r.get('livechatrequested') == 'true', 'Live chat maybe out of HOO'


# TODO build out function to test complete tree
def test_active_close(active_close_values):
    if active_close_values:
        params['entry'] = active_close_values['input']
        r = EngineRequest(endpoint).make_request(params)
        assert r.get('ident') == params['ident'], 'First active close input failed'
        assert r.get('answerID') == active_close_values['answer_id'], 'Did not hit active close dtree'
        assert r.get('autosubmitmode') == 'false', 'autosubmitmode did not return false first auto submit transaction'
        assert r.get('hideuserentry') == 'true', 'user entry not hidden'
    else:
        pytest.skip('No active close values found in config.')


def test_semantic(semantic_input):
    if not flags['SEMANTIC']: pytest.skip('No semantic input to test!')
    params['entry'] = semantic_input
    r = EngineRequest(endpoint).make_request(params)
    assert r.get('related_list', None) is not None


def test_versionnumber(version_number):
    params['entry'] = 'versionnumber'
    r = EngineRequest(endpoint).make_request(params)

    v = re.search('publish_id: (\d+)', r.get('botanswer'))
    if v:
        assert v.group(1) == version_number, 'version number was %s. Expected %s' % (v.group(1), version_number)
    else:
        assert False, 'Version number not found. Botanswer: %s' % r.get('botanswer')


def test_custom_back_text(custom_back_text_values):
    if flags['BACK_TEXT'] is True or flags['ALL'] is True:

        # enter dtree
        params['entry'] = custom_back_text_values['inputs'][0]
        r = EngineRequest(endpoint).make_request(params)
        print 'Response from first dtree transaction: Answer: %s | Ident: %s' % (r.get('botanswer'), r.get('ident'))

        # hit test node
        params['ident'] = r.get('ident')
        params['entry'] = custom_back_text_values['inputs'][1]
        r = EngineRequest(endpoint).make_request(params)
        print 'Response from second dtree transaction: Answer: %s | Ident: %s' % (r.get('botanswer'), r.get('ident'))

        assert r.get('backnavtext') == custom_back_text_values['text']

    else:
        pytest.skip('Skipping custom back text test')


def test_blank_connectors(blank_connector_values):
    if flags['BLANK_CONNECTORS'] is False or flags['ALL'] is True:
        pytest.skip('Skipping blank connectors test')
    params['entry'] = blank_connector_values['input']
    r = EngineRequest(endpoint).make_request(params)

    assert r.get('connectors') is None, 'Response returned connectors: %s' % r.get('connectors')


def test_dtree(dtree_input):
    params['ident'] = ''
    params['entry'] = dtree_input
    r = EngineRequest(endpoint).make_request(params)

    assert r.get('connectors') is not None, 'Response did not contain connectors. Response: %s' % r



# TODO create set up file to feed project params in cmd

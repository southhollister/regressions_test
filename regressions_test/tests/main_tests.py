from regressions_test.engine_request import EngineRequest
import json
import pytest
import re

# Tests
def test_standard_template(response_keys, session):
    """
    Check that expected keys are returned in response template.
    :param response_keys:
    :return:
    """
    req = session
    assert isinstance(req, dict)
    for key in response_keys:
        assert req.get(key, False) is not False, 'Failed on %s' % key


def test_init_standard_response_values(init_none_keys, init_value_keys, session):
    """
    Test that response values are as expected on INIT
    :param init_none_keys:
    :param init_value_keys:
    :return:
    """
    req = session
    assert all([req[key] is None for key in init_none_keys]), '%s was %s; Expected None' % (key, req[key])
    assert all([req[key] is not None for key in init_value_keys]), '%s was unexpected None.' % key

    assert req['autosubmitmode'] == 'true'
    assert req['autosubmitwaittime'].isdigit()
    assert req['backnavdisabled'] == 'true'
    assert len(req['botanswer']) > 5
    # TODO update to use config var
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


def test_live_chat(live_chat_values, params, endpoint):
    """
    Test live chat etvs on non INIT transaction.
    :param live_chat_values:
    :return:
    """

    # params = session.get('ident')
    for i in live_chat_values['live_chat_input']:
        params['entry'] = i
        r = EngineRequest(endpoint).make_request(params)

    assert r.get('ident') == params['ident']
    assert r.get('livechatskill') == live_chat_values['live_chat_skill']
    assert r.get('livechatrequested') == 'true', 'Live chat maybe out of HOO'


# TODO build out function to test complete tree
def test_active_close(active_close_values, params, endpoint):
    if not active_close_values: pytest.skip('No active close values found in config.')
    params['entry'] = active_close_values['input']
    r = EngineRequest(endpoint).make_request(params)
    assert r.get('ident') == params['ident'], 'First active close input failed'
    assert r.get('answerID') == active_close_values['answer_id'], 'Did not hit active close dtree'
    assert r.get('autosubmitmode') == 'false', 'autosubmitmode did not return false first auto submit transaction'
    assert r.get('hideuserentry') == 'true', 'user entry not hidden'


def test_semantic(semantic_input, params, endpoint):
    if not semantic_input: pytest.skip('No semantic input to test!')
    params['entry'] = semantic_input
    r = EngineRequest(endpoint).make_request(params)
    assert r.get('related_list', None) is not None


def test_versionnumber(version_number, params, endpoint):
    params['entry'] = 'versionnumber'
    r = EngineRequest(endpoint).make_request(params)

    v = re.search('publish_id: (\d+)', r.get('botanswer'))
    if v:
        assert v.group(1) == version_number, 'version number was %s. Expected %s' % (v.group(1), version_number)
    else:
        assert False, 'Version number not found. Botanswer: %s' % r.get('botanswer')


def test_custom_back_text(custom_back_text_values, params, endpoint):
    if not custom_back_text_values: pytest.skip('Skipping custom back text test')

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


def test_blank_connectors(blank_connector_values, params, endpoint):
    if not blank_connector_values: pytest.skip('Skipping blank connectors test')
    params['entry'] = blank_connector_values['input']
    r = EngineRequest(endpoint).make_request(params)

    assert r.get('connectors') is None, 'Response returned connectors: %s' % r.get('connectors')


def test_dtree(dtree_input, endpoint):
    params = dict()
    params['ident'] = ''
    params['entry'] = dtree_input
    r = EngineRequest(endpoint).make_request(params)

    assert r.get('connectors') is not None, 'Response did not contain connectors. Response: %s' % r


# TODO add test for related results prompt
def test_related_results_prompt(engine, params, related_results_prompt, semantic_input, session):
    params['ident'] = session.get('ident', '')
    params['entry'] = semantic_input

    r = engine.make_request(params)

    assert r.get('relatedlistprompttext') == related_results_prompt, \
        'Session id: %s || Res. Session id: %s' % (session.get('ident'), r.get('ident'))

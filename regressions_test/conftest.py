import pytest
import json
import os
from engine_request import EngineRequest


def pytest_addoption(parser):
    parser.addoption('--project', action='store')
    parser.addoption('--environment', action='store')
    parser.addoption("--params", action="store", default='{"params":"", "entry":""}')



@pytest.fixture
def params(request):
    return json.loads(request.config.getoption("--params"))


@pytest.fixture
def project_config(request):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'project_configs', '%s.json' % request.config.getoption('project').lower())
    config = json.loads(open(p).read())
    return config


@pytest.fixture
def endpoint(project_config, request):
    return project_config['endpoints'][request.config.getoption('environment')]


@pytest.fixture
def engine(endpoint):
    return EngineRequest(endpoint=endpoint)


@pytest.fixture
def session(project_config, engine, params):
    return engine.make_request(params)


@pytest.fixture
def version_number(project_config):
    return project_config['version_number']


@pytest.fixture
def response_keys(project_config):
    return ['answerID', 'answerLinkID', 'autosubmitmode', 'autosubmitwaittime', 'backnavdisabled', 'backnavflag', 'backnavtext',
            'userintent', 'botanswer', 'conditionID', 'conditionLinkID', 'connectors', 'conversationhistory', 'currentBA',
            'currentChannel', 'disableautocomplete', 'disambiguationoptions', 'dtreenodeid', 'dtreeobjectid',
            'entrysuggestions', 'fbresponse', 'forcesessionclose', 'hideuserentry', 'icsappended', 'ident',
            'livechatrequested', 'livechatskill', 'maxsemanticfaqs', 'question', 'recognitionID',
            'relatedlistprompttext', 'section', 'sitecontext', 'transactioncount', 'userentryallowed', 'userlogid',
            'validresponse']


@pytest.fixture
def init_none_keys(project_config):
    return ['backnavflag', 'connectors', 'conversationhistory', 'disambiguationoptions', 'dtreenodeid', 'dtreeobjectid',
            'fbresponse', 'livechatskill', 'question', 'relatedlistprompttext', 'sitecontext']


@pytest.fixture
def init_value_keys(project_config):
    return ['answerID', 'answerLinkID', 'autosubmitmode', 'autosubmitwaittime', 'backnavdisabled', 'botanswer',
            'conditionID', 'conditionLinkID', 'currentBA', 'currentChannel', 'disableautocomplete', 'entrysuggestions',
            'forcesessionclose', 'hideuserentry', 'icsappended', 'ident', 'livechatrequested', 'maxsemanticfaqs',
            'recognitionID', 'section', 'transactioncount', 'userentryallowed', 'userlogid', 'validresponse']


# TODO parametrize this fixture to be able to test all live chat queues
@pytest.fixture
def live_chat_values(project_config):
    return project_config.get('live_chat_values', {})


@pytest.fixture
def active_close_values(project_config):
    return project_config.get('active_close_values', {})


@pytest.fixture
def semantic_input(project_config):
    return project_config.get('semantic_input', None)


@pytest.fixture
def custom_back_text_values(project_config):
    return project_config.get('custom_back_text_values', {})


@pytest.fixture
def blank_connector_values(project_config):
    return project_config.get('blank_connector_values', {})


@pytest.fixture
def dtree_input(project_config):
    return project_config.get('dtree_input', {})


@pytest.fixture
def related_results_prompt(project_config):
    return project_config.get('related_results_prompt', None)


@pytest.fixture
def multipart_answer(project_config):
    return project_config.get('multipart_answer_values', {})

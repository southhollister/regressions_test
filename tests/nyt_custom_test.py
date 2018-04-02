"""
Custom tests for Asus project
"""
from pytest import fixture
from engine_request import EngineRequest
import sys
from regressions_test import endpoint


@fixture
def session():
    return EngineRequest(endpoint).make_request()


def test_disambiguation(session, project_config):
    res = EngineRequest(endpoint).make_request(params={'ident': session['ident'], 'entry': project_config.get('disambiguation_input', '')})
    assert res.get('disambiguationoptions', None) is not None, '%s' % project_config.get('disambiguation_input', 'ERROR')

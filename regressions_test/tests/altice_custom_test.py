"""
Custom tests for Altice project
"""
from pytest import fixture
from regressions_test.engine_request import EngineRequest
from regressions_test import endpoint


@fixture
def session():
    return EngineRequest(endpoint).make_request()


def test_user_intent(session):
    res = EngineRequest(endpoint).make_request(params={'ident': session['ident'], 'entry': 'hello'})
    assert res.get('userintent') == 'hello'

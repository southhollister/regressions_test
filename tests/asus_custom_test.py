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


def test_top_semantic_answer(session, project_config):
    res = EngineRequest(endpoint).make_request(params={'ident': session['ident'], 'entry': 'rog'})
    assert project_config.get('top_semantic_answer_prefix', '').lower() in res.get('botanswer', '').lower()
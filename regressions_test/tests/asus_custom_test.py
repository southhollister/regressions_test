"""
Custom tests for Asus project
"""
from pytest import fixture



@fixture
def session(engine):
    return engine.make_request()


def test_top_semantic_answer(engine, session, project_config):
    res = engine.make_request(params={'ident': session['ident'], 'entry': 'rog'})
    assert project_config.get('top_semantic_answer_prefix', '').lower() in res.get('botanswer', '').lower()
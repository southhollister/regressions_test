"""
Custom tests for Asus project
"""
from pytest import fixture


@fixture
def session(engine):
    return engine.make_request()


def test_disambiguation(engine, session, project_config):
    res = engine.make_request(params={'ident': session['ident'], 'entry': project_config.get('disambiguation_input', '')})
    assert res.get('disambiguationoptions', None) is not None, '%s' % project_config.get('disambiguation_input', 'ERROR')

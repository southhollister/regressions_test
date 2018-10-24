from pytest import fixture


def test_blank_related_results_prompt(session, engine, project_config):
    params = {
        'ident': session['ident'],
        'entry': project_config.get('blank_related_results_prompt_input')
    }
    res = engine.make_request(params=params)
    assert res.get('related_list', None) is not None
    assert res.get('related_results_prompt') is None


def test_non_multipart_answer(engine, multipart_values):
    params = {
        'channel': multipart_values.get('non_multipart_channel'),
        'entry': multipart_values.get('input')
    }
    res = engine.make_request(params=params)
    assert multipart_values.get('delimiter') not in res.get('botanswer')
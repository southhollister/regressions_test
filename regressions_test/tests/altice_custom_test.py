"""
Custom tests for Altice project
"""
from pytest import fixture


@fixture
def session(engine):
    return engine.make_request()


@fixture
def custom_vars(project_config):
    return project_config['custom']


# TODO get custom use case stuff from custom section of config file
def test_user_intent(engine, session, custom_vars):
    trigger = custom_vars.get('user_intent_values')
    if not trigger:
        assert False, 'Failed to retrieve trigger'

    res = engine.make_request(params={'ident': session['ident'], 'entry': trigger['input']})
    assert res.get('userintent') == trigger['text']


def test_shortened_related_result_text(engine, session, custom_vars):
    """Makes a request with input that will return results with shortened question texts;
    select a related result and make an faq request;
    use the user intent (rec question) from the response to compare against the selected faqs question text
    """
    trigger = custom_vars.get('shortened_related_result_text_input', '')
    if not trigger:
        assert False, 'Failed to retrieve trigger'

    params = {
        'ident': session['ident'],
        'entry': trigger
    }
    res = engine.make_request(params=params)

    # Gather necessary bits for faq request
    faq = res.get('related_list', [])[0]
    rec_id = faq.get('RecognitionId')
    ans_id = faq.get('AnswerId')
    # Bail if necessary bits were not collected
    if not all([rec_id, ans_id]):
        assert False

    # Make faq request
    params.update({
        'entry': '',
        'recognition_id': rec_id,
        'answer_id': ans_id,
        'faq': 1
    })
    faq_res = engine.make_request(params=params)

    assert faq.get('QuestionText') != faq_res.get('userintent')
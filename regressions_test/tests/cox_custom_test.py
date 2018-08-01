"""
Custom tests for Asus project
"""
from pytest import fixture


@fixture
def session(engine):
    return engine.make_request()
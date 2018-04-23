To install run python setup.py install

Usage:
    regressions_test
    regressions_test [-h | --help]
    regressions_test [-h -a] test PROJECT [ENVIRONMENT]
    regressions_test [-h] update_version PROJECT VERSION_NUMBER
    regressions_test [-h] add_endpoint PROJECT NAME URL
    regressions_test [-h] show PROJECT CONFIG_VAR


Commands:
    test            Run regression tests on PROJECT using ENVIRONMENT endpoint
        ENVIRONMENT Defaults to staging;
        -a          Run regressions tests on all endpoints
        -V          Update kb version number before running tests
    update_version  Update kb version number to VERSION_NUMBER for regressions test
    add_endpoint    Add URL as endpoint in PROJECT's config file under NAME
    show            Display CONFIG_VAR for PROJECT
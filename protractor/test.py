# -*- coding: utf-8 -*-

import os
import subprocess
from unittest import skipUnless
try:
    from urllib.request import urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import urlopen, URLError

gotWebdriverManager = os.path.exists('/usr/bin/webdriver-manager')


def internet_on():
    try:
        urlopen('http://216.58.192.142', timeout=1)
        return True
    except URLError:
        return False


class ProtractorTestCaseMixin(object):
    protractor_conf = 'protractor.conf.js'
    suite = None
    specs = None

    @classmethod
    @skipUnless(gotWebdriverManager, 'skipping protractor e2e tests')
    def setUpClass(cls):
        super(ProtractorTestCaseMixin, cls).setUpClass()
        with open(os.devnull, 'wb') as f:
            if internet_on():
                subprocess.call(['webdriver-manager', 'update'], stdout=f, stderr=f)
            cls.webdriver = subprocess.Popen(
                ['webdriver-manager', 'start'], stdout=f, stderr=f)

    @classmethod
    @skipUnless(gotWebdriverManager, 'skipping protractor e2e tests')
    def tearDownClass(cls):
        cls.webdriver.kill()
        super(ProtractorTestCaseMixin, cls).tearDownClass()

    def get_protractor_params(self):
        """A hook for adding params that protractor will receive."""
        return {
            'live_server_url': self.live_server_url
        }

    @skipUnless(gotWebdriverManager, 'skipping protractor e2e tests')
    def test_run(self):
        if not self.specs and not self.suite:
            return

        protractor_command = 'protractor {}'.format(self.protractor_conf)
        protractor_command += ' --baseUrl {}'.format(self.live_server_url)
        if self.specs:
            protractor_command += ' --specs {}'.format(','.join(self.specs))
        if self.suite:
            protractor_command += ' --suite {}'.format(self.suite)
        for key, value in self.get_protractor_params().items():
            protractor_command += ' --params.{key}={value}'.format(
                key=key, value=value
            )
        return_code = subprocess.call(protractor_command.split())
        self.assertEqual(return_code, 0)

# -*- coding: utf-8 -*-

import os
import subprocess

class ProtractorTestCaseMixin(object):
    protractor_conf = 'protractor.conf.js'
    npm_prefix = None
    suite = None
    specs = None

    @classmethod
    def setUpClass(cls):
        super(ProtractorTestCaseMixin, cls).setUpClass()
        with open(os.devnull, 'wb') as f:
            subprocess.call(['webdriver-manager', 'update'], stdout=f, stderr=f)
            cls.webdriver = subprocess.Popen(
                ['webdriver-manager', 'start'], stdout=f, stderr=f)

    @classmethod
    def tearDownClass(cls):
        cls.webdriver.kill()
        super(ProtractorTestCaseMixin, cls).tearDownClass()

    def get_protractor_params(self):
        """A hook for adding params that protractor will receive."""
        return {
            'live_server_url': self.live_server_url
        }

    def test_run(self):
        command_prefix = ''
        npm_prefix = self.npm_prefix
        if (npm_prefix):
            npm_prefix = 'npm run --prefix={} '.format(npm_prefix)
        protractor_command = npm_prefix + 'protractor ' + os.getcwd() + '/{}'.format(self.protractor_conf)
        if (npm_prefix):
            protractor_command += ' -- '
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

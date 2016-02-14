# -*- coding: utf-8 -*-

import os
import sys
from multiprocessing import Process
from optparse import make_option
import subprocess
import socket

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.runner import setup_databases
from django.test.testcases import QuietWSGIRequestHandler
from django.core.servers.basehttp import WSGIServer


class Command(BaseCommand):
    args = '[--protractor-conf] [--runserver-command] [--specs] [--suite] [--addrport]'
    help = 'Run protractor tests with a test database'

    option_list = BaseCommand.option_list + (
        make_option('--protractor-conf',
            action='store',
            dest='protractor_conf',
            default='protractor.conf.js',
            help='Specify a destination for your protractor configuration'
        ),
        make_option('--runserver-command',
            action='store',
            dest='run_server_command',
            default='runserver',
            help='Specify which command you want to run a server'
        ),
        make_option('--direct-connect',
            action='store_true',
            dest='direct_connect',
            default=False,
            help='Do not start a selenium webdriver server because you are using protractor directConnect'
        ),
        make_option('--specs',
            action='store',
            dest='specs',
            help='Specify which specs to run'
        ),
        make_option('--suite',
            action='store',
            dest='suite',
            help='Specify which suite to run'
        ),
        make_option('--fixture',
            action='append',
            dest='fixtures',
            help='Specify fixture to load initial data to the database'
        ),
        make_option('--addrport', action='store', dest='addrport',
            type='string',
            help='port number or ipaddr:port to run the server on'),
    )

    def handle(self, *args, **options):
        options['verbosity'] = int(options.get('verbosity'))

        if not os.path.exists(options['protractor_conf']):
            raise IOError("Could not find '{}'"
                .format(options['protractor_conf']))

        if not options["direct_connect"]:
            self.run_webdriver()

        old_config = self.setup_databases(options)

        fixtures = options['fixtures']
        if fixtures:
            call_command('loaddata', *fixtures,
                         **{'verbosity': options['verbosity']})

        if options['addrport'] is None:
            options['addrport'] = os.environ.get(
                    'DJANGO_LIVE_TEST_SERVER_ADDRESS', 'localhost:8081')
        host, possible_ports = self.parse_addr(options['addrport'])
        print(host, possible_ports)
        options['addrport'] = "{}:{}".format(host, self.choose_port(host, possible_ports))

        test_server_process = Process(target=self.runserver, args=(options,))
        test_server_process.daemon = True
        test_server_process.start()

        authority = options['addrport']
        if ':' not in authority:
            authority = 'localhost:' + authority
        live_server_url = 'http://%s' % authority

        params = {
            'live_server_url': live_server_url
        }

        protractor_command = 'protractor {}'.format(options['protractor_conf'])
        protractor_command += ' --baseUrl {}'.format(live_server_url)
        if options['specs']:
            protractor_command += ' --specs {}'.format(options['specs'])
        if options['suite']:
            protractor_command += ' --suite {}'.format(options['suite'])
        for key, value in params.items():
            protractor_command += ' --params.{key}={value}'.format(
                key=key, value=value
            )

        return_code = subprocess.call(protractor_command.split())
        self.teardown_databases(old_config, options)
        if return_code:
            self.stdout.write('Failed')
            sys.exit(1)
        else:
            self.stdout.write('Success')

    def setup_databases(self, options):
        return setup_databases(options['verbosity'], False)

    def teardown_databases(self, old_config, options):
        """
        Destroys all the non-mirror databases.
        """
        old_names, mirrors = old_config
        for connection, old_name, destroy in old_names:
            if destroy:
                connection.creation.destroy_test_db(old_name, options['verbosity'])

    def parse_addr(self, specified_address):
        """Parse the --addrport argument into a host/IP address and port range"""
        # This code is based on
        # django.test.testcases.LiveServerTestCase.setUpClass

        # The specified ports may be of the form '8000-8010,8080,9200-9300'
        # i.e. a comma-separated list of ports or ranges of ports, so we break
        # it down into a detailed list of all possible ports.
        possible_ports = []
        try:
            host, port_ranges = specified_address.split(':')
            for port_range in port_ranges.split(','):
                # A port range can be of either form: '8000' or '8000-8010'.
                extremes = list(map(int, port_range.split('-')))
                assert len(extremes) in (1, 2)
                if len(extremes) == 1:
                    # Port range of the form '8000'
                    possible_ports.append(extremes[0])
                else:
                    # Port range of the form '8000-8010'
                    for port in range(extremes[0], extremes[1] + 1):
                        possible_ports.append(port)
        except Exception:
            raise Exception(
                'Invalid address ("%s") for live server.' % specified_address)

        return host, possible_ports

    def choose_port(self, host, possible_ports):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for port in possible_ports:
            result = sock.connect_ex((host, port))
            if result != 0:
                return port
        raise OSError("Could not find an open port")

    def runserver(self, options):
        use_threading = connection.features.test_db_allows_multiple_connections
        self.stdout.write('Starting server...')
        call_command(
            options['run_server_command'],
            addrport=options.get('addrport'),
            shutdown_message='',
            use_reloader=False,
            use_ipv6=False,
            verbosity=0,
            use_threading=use_threading,
            stdout=open(os.devnull, 'w')
        )

    def run_webdriver(self):
        self.stdout.write('Starting webdriver...')
        with open(os.devnull, 'w') as f:
            subprocess.call(['webdriver-manager', 'update'], stdout=f, stderr=f)
            subprocess.Popen(['webdriver-manager', 'start'], stdout=f, stderr=f)

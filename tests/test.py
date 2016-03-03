#!/usr/bin/python2

# Use test.py with any valid combination of arguments in order to run
# DAO test scenarios

import argparse
import os
import json
import subprocess
import shutil
import sys
import calendar
from datetime import datetime
from string import Template
import re
import random


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(random.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def determine_binary(given_binary, name):
    """
    Determines if a path to a binary is correct and if not tries to
    get a generic one by looking at the system PATH
    """
    if given_binary:
        if is_exe(given_binary):
            return given_binary
    else:
        # try to find binary in the PATH
        return which(name)
    return None


def seconds_in_future(secs):
    return calendar.timegm(datetime.utcnow().utctimetuple()) + secs


class TestContext():
    def __init__(self, args):
        self.tests_ok = True
        self.dao_addr = None
        self.tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(self.tests_dir, 'templates')
        self.contracts_dir = os.path.dirname(self.tests_dir)
        self.solc = determine_binary(args.solc, 'solc')
        self.geth = determine_binary(args.geth, 'geth')
        self.verbose = args.verbose
        if args.clean_chain:
            self.clean_blockchain()
        self.closing_time = seconds_in_future(args.closing_time * 60)
        self.min_value = args.min_value
        self.test_scenarios = {
            'none': self.run_test_none,
            'deploy': self.run_test_deploy,
            'fund': self.run_test_fund,
        }

    def clean_blockchain(self):
        """Clean all blockchain data directories apart from the keystore"""
        print("Cleaning blockchain data directory ...")
        data_dir = os.path.join(self.tests_dir, "data")
        shutil.rmtree(os.path.join(data_dir, "chaindata"), ignore_errors=True)
        shutil.rmtree(os.path.join(data_dir, "dapp"), ignore_errors=True)
        try:
            os.remove(os.path.join(data_dir, "nodekey"))
        except OSError:
            pass

    def test_results(self, testname):
        if self.tests_ok:
            print("Tests for '{}' PASSED!".format(testname))
        else:
            print("Tests for '{}' FAILED!".format(testname))
            sys.exit(1)

    def check(self, got, expect, msg):
        res = got == expect
        if self.verbose:
            print("{} ... {}".format(msg, "OK!" if res else "FAIL!"))
        if not res:
            self.tests_ok = False
            print("    Expected '{}' but got '{}'".format(expect, got))
        return res

    def run_script(self, script):
        print("Running '{}' script".format(script))
        return subprocess.check_output([
            self.geth,
            "--networkid",
            "123",
            "--nodiscover",
            "--maxpeers",
            "0",
            "--genesis",
            "./genesis_block.json",
            "--datadir",
            "./data",
            "--verbosity",
            "0",
            "js",
            script
        ])

    def compile_contracts(self):
        if not self.solc:
            print("Error: No valid solc compiler provided")
            sys.exit(1)
        print("Compiling the DAO contract...")

        dao_contract = os.path.join(self.contracts_dir, "DAO.sol")
        if not os.path.isfile(dao_contract):
            print("DAO contract not found at {}".format(dao_contract))

        data = subprocess.check_output([
            self.solc,
            os.path.join(self.contracts_dir, "DAO.sol"),
            "--optimize",
            "--combined-json",
            "abi,bin"
        ])
        res = json.loads(data)
        contract = res["contracts"]["DAO"]
        DAOCreator = res["contracts"]["DAO_Creator"]
        self.creator_abi = DAOCreator["abi"]
        self.creator_bin = DAOCreator["bin"]
        self.dao_abi = contract["abi"]
        self.dao_bin = contract["bin"]

    def create_deploy_js(self):
        print("Creating 'deploy.js'...")
        with open(os.path.join(self.templates_dir, 'deploy.template.js'), 'r') as f:
            data = f.read()
        tmpl = Template(data)
        s = tmpl.substitute(
            dao_abi=self.dao_abi,
            dao_bin=self.dao_bin,
            creator_abi=self.creator_abi,
            creator_bin=self.creator_bin,
            min_value=self.min_value,
            closing_time=self.closing_time
        )
        with open("deploy.js", "w") as f:
            f.write(s)

    def run_test_deploy(self):
        print("Running the Deploy Test Scenario")
        self.create_deploy_js()
        output = self.run_script('deploy.js')

        r = re.compile(
            'dao_creator_address: (?P<dao_creator_address>.*?)\n.*?dao_address'
            ': (?P<dao_address>.*?)\n',
            flags=re.MULTILINE | re.DOTALL
        )
        m = r.search(output)
        if not m:
            print("Error: Could not find addresses in the deploy output.")
            sys.exit(1)

        self.dao_creator_addr = m.group('dao_creator_address')
        self.dao_addr = m.group('dao_address')
        print("DAO Creator address is: {}".format(self.dao_creator_addr))
        print("DAO address is: {}".format(self.dao_addr))

    def create_fund_js(self, waitsecs, amounts):
        print("Creating 'fund.js'...")
        with open(os.path.join(self.templates_dir, 'fund.template.js'), 'r') as f:
            data = f.read()
        tmpl = Template(data)
        s = tmpl.substitute(
            dao_abi=self.dao_abi,
            dao_address=self.dao_addr,
            wait_ms=waitsecs*1000,
            userval0=amounts[0],
            userval1=amounts[1],
            userval2=amounts[2],
            userval3=amounts[3],
            userval4=amounts[4],
            userval5=amounts[5],
            userval6=amounts[6]
        )
        with open("fund.js", "w") as f:
            f.write(s)

    def run_test_fund(self):
        sale_secs = 15
        # if deployment did not already happen do it now, with some predefined
        # values for this scenario
        if not self.dao_addr:
            self.closing_time = seconds_in_future(sale_secs)
            self.run_test_deploy()
        total_amount = self.min_value + random.randint(1, 100)
        amounts = constrained_sum_sample_pos(7, total_amount)
        self.create_fund_js(sale_secs, amounts)
        print(
            "Notice: Funding period is {} seconds so the test will wait "
            "as much".format(sale_secs)
        )
        output = self.run_script('fund.js')
        r = re.compile(
            r'CHECK\(dao.funded\): (?P<funded>.*?)\n.*'
            'CHECK\(dao.totalSupply\): (?P<total_supply>.*?)\n.*'
            'CHECK\(balanceuser0\): (?P<balance0>.*?)\n.*'
            'CHECK\(balanceuser1\): (?P<balance1>.*?)\n.*'
            'CHECK\(balanceuser2\): (?P<balance2>.*?)\n.*'
            'CHECK\(balanceuser3\): (?P<balance3>.*?)\n.*'
            'CHECK\(balanceuser4\): (?P<balance4>.*?)\n.*'
            'CHECK\(balanceuser5\): (?P<balance5>.*?)\n.*'
            'CHECK\(balanceuser6\): (?P<balance6>.*?)\n.*'
            'CHECK\(afterbalanceuser0\): (?P<afterbalance0>.*)\n.*',
            flags=re.MULTILINE | re.DOTALL
        )
        m = r.search(output)
        if not m:
            print("Error: Could not parse fund.js output properly")
            sys.exit(1)
        print(m.groups())
        self.check(m.group('funded'), 'true', 'Check DAO is funded')
        self.check(
            int(m.group('total_supply')),
            total_amount,
            'Check total supply of tokens'
        )
        for idx, amount in enumerate(amounts):
            self.check(
                int(m.group('balance{}'.format(idx))),
                amount,
                'Check token balance of user {}'.format(idx)
            )
        self.check(
            int(m.group('afterbalance0')),
            amounts[0],
            'Check no tokens can be bought after the end of the sale period'
        )
        self.test_results('fund.js')

    def run_test_none(self):
        print("No test scenario provided.")

    def run_test(self, args):
        if not self.geth:
            print("Error: No valid geth binary provided/found")
            sys.exit(1)
        # All scenarios would need to have the contracts compiled
        self.compile_contracts()
        self.test_scenarios[args.scenario]()

if __name__ == "__main__":
    p = argparse.ArgumentParser(description='DAO contracts test helper')
    p.add_argument(
        '--solc',
        help='Full path to the solc binary to use'
    )
    p.add_argument(
        '--geth',
        help='Full path to the geth binary to use'
    )
    p.add_argument(
        '--clean-chain',
        action='store_true',
        help=(
            'If given then the blockchain is deleted before any '
            'test scenario is executed'
        )
    )
    p.add_argument(
        '--verbose',
        action='store_true',
        help='If given then all test checks are printed in the console'
    )
    p.add_argument(
        '--closing-time',
        type=int,
        help='Number of minutes from now when the newly created DAO sale ends',
        default=120
    )
    p.add_argument(
        '--min-value',
        type=int,
        help='Minimum value to consider the DAO crowdfunded',
        default=20
    )
    p.add_argument(
        '--scenario',
        choices=['none', 'deploy', 'fund'],
        default='none',
        help='Test scenario to play out'
    )
    args = p.parse_args()

    # Initialize the test support context
    ctx = TestContext(args)
    ctx.run_test(args)

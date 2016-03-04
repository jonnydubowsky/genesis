#!/usr/bin/python2

# Use test.py with any valid combination of arguments in order to run
# DAO test scenarios

import os
import json
import subprocess
import shutil
import sys
from datetime import datetime
from string import Template
import re
import random
from utils import (
    constrained_sum_sample_pos, rm_file,
    determine_binary, ts_now, seconds_in_future
)
from args import test_args


class TestContext():
    def __init__(self, args):
        self.tests_ok = True
        self.dao_addr = None  # check to determine if DAO is deployed
        self.offer_addr = None  # check to determine if offer is deployed
        self.tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.save_file = os.path.join(self.tests_dir, "data", "saved")
        self.templates_dir = os.path.join(self.tests_dir, 'templates')
        self.contracts_dir = os.path.dirname(self.tests_dir)
        self.solc = determine_binary(args.solc, 'solc')
        self.geth = determine_binary(args.geth, 'geth')
        self.verbose = args.verbose

        self.closing_time = seconds_in_future(args.closing_time * 60)
        self.min_value = args.min_value
        self.test_scenarios = {
            'none': self.run_test_none,
            'deploy': self.run_test_deploy,
            'fund': self.run_test_fund,
        }

        # keep this at end since any data loaded should override constructor
        if args.clean_chain:
            self.clean_blockchain()
        else:
            self.attemptLoad()

    def attemptLoad(self):
        """
        If there is a saved file, then attempt to load DAO data from there
        """
        if os.path.isfile(self.save_file):
            print("Loading DAO from a saved file...")
            with open(self.save_file, 'r') as f:
                data = json.loads(f.read())
            self.dao_addr = data['dao_addr']
            self.dao_creator_addr = data['dao_creator_addr']
            self.closing_time = data['closing_time']
            print("Loaded dao_addr: {}".format(self.dao_addr))
            print("Loaded dao_creator_addr: {}".format(self.dao_creator_addr))

    def clean_blockchain(self):
        """Clean all blockchain data directories apart from the keystore"""
        print("Cleaning blockchain data directory ...")
        data_dir = os.path.join(self.tests_dir, "data")
        shutil.rmtree(os.path.join(data_dir, "chaindata"), ignore_errors=True)
        shutil.rmtree(os.path.join(data_dir, "dapp"), ignore_errors=True)
        rm_file(os.path.join(data_dir, "nodekey"))
        rm_file(os.path.join(data_dir, "saved"))

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

    def compile_contract(self, contract_path):
        print("    Compiling {}...".format(contract_path))
        data = subprocess.check_output([
            self.solc,
            contract_path,
            "--optimize",
            "--combined-json",
            "abi,bin"
        ])
        return json.loads(data)

    def compile_contracts(self, keep_limits):
        if not self.solc:
            print("Error: No valid solc compiler provided")
            sys.exit(1)
        print("Compiling the DAO contracts...")

        dao_contract = os.path.join(self.contracts_dir, "DAO.sol")
        if not os.path.isfile(dao_contract):
            print("DAO contract not found at {}".format(dao_contract))
            sys.exit(1)

        if not keep_limits:
            with open(dao_contract, 'r') as f:
                contents = f.read()
            contents = contents.replace(" || _debatingPeriod < 1 weeks", "")
            contents = contents.replace(" || (_debatingPeriod < 2 weeks)", "")
            new_path = os.path.join(self.contracts_dir, "DAOcopy.sol")
            with open(new_path, "w") as f:
                f.write(contents)
            dao_contract = new_path

        res = self.compile_contract(dao_contract)
        contract = res["contracts"]["DAO"]
        DAOCreator = res["contracts"]["DAO_Creator"]
        self.creator_abi = DAOCreator["abi"]
        self.creator_bin = DAOCreator["bin"]
        self.dao_abi = contract["abi"]
        self.dao_bin = contract["bin"]

        offer = os.path.join(self.contracts_dir, "SampleOffer.sol")
        res = self.compile_contract(offer)
        self.offer_abi = res["contracts"]["SampleOffer"]["abi"]
        self.offer_bin = res["contracts"]["SampleOffer"]["bin"]

        if not keep_limits:
            # also delete the temporary created file
            rm_file(new_path)

    def create_deploy_js(self):
        print("Creating 'deploy.js'...")
        with open(
                os.path.join(self.templates_dir, 'deploy.template.js'),
                'r'
        ) as f:
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
        with open(self.save_file, "w") as f:
            f.write(json.dumps({
                "dao_creator_addr": self.dao_creator_addr,
                "dao_addr": self.dao_addr,
                "closing_time": self.closing_time
            }))

    def create_fund_js(self, waitsecs, amounts):
        print("Creating 'fund.js'...")
        with open(
                os.path.join(self.templates_dir, 'fund.template.js'),
                'r'
        ) as f:
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
        # values for this scenario (15 seconds)
        if not self.dao_addr:
            self.closing_time = seconds_in_future(sale_secs)
            self.run_test_deploy()
        else:
            sale_secs = self.closing_time - ts_now()
            print(
                "WARNING: Running the funding scenario with a pre-deployed "
                "DAO contract. Closing time is {} which is approximately {} "
                "seconds from now.".format(
                    datetime.fromtimestamp(self.closing_time).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    sale_secs
                )
            )
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
            print(
                "Error: Could not parse fund.js output properly.Output was:\n"
                "{}".format(output)
            )
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
        self.compile_contracts(args.keep_limits)
        self.test_scenarios[args.scenario]()

if __name__ == "__main__":
    args = test_args()
    ctx = TestContext(args)
    ctx.run_test(args)

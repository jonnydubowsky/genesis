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


class TestContext():
    def __init__(self, args):
        self.tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.templates_dir = os.path.join(self.tests_dir, 'templates')
        self.contracts_dir = os.path.dirname(self.tests_dir)
        self.solc = determine_binary(args.solc, 'solc')
        self.geth = determine_binary(args.geth, 'geth')
        if args.clean_chain:
            self.clean_blockchain()
        self.closing_time = (
            calendar.timegm(datetime.utcnow().utctimetuple()) +
            args.closing_time * 60
        )
        self.min_value = args.min_value
        self.test_scenarios = {
            'none': self.run_test_none,
            'deploy': self.run_test_deploy
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
        return (
            contract["abi"],
            contract["bin"],
            DAOCreator["abi"],
            DAOCreator["bin"]
        )

    def create_deploy_js(self, dabi, dbin, cabi, cbin):
        print("Rewritting deploy.js using the compiled contract...")
        with open(os.path.join(self.templates_dir, 'deploy.template.js'), 'r') as f:
            data = f.read()
        tmpl = Template(data)
        s = tmpl.substitute(
            dao_abi=dabi,
            dao_bin=dbin,
            creator_abi=cabi,
            creator_bin=cbin,
            min_value=self.min_value,
            closing_time=self.closing_time
        )
        with open("deploy.js", "w") as f:
            f.write(s)

    def run_test_deploy(self):
        print("Running the Deploy Test Scenario")
        dabi, dbin, cabi, cbin = g_ctx.compile_contracts()
        g_ctx.create_deploy_js(dabi, dbin, cabi, cbin)
        output = subprocess.check_output([
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
            "deploy.js"
        ])

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

    def run_test_none(self):
        print("No test scenario provided.")

    def run_test(self, args):
        if not self.geth:
            print("Error: No valid geth binary provided/found")
            sys.exit(1)
        self.test_scenarios[args.scenario]()

g_ctx = None

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
    p.add_argument('--clean-chain', action='store_true')
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
        choices=['none', 'deploy'],
        default='none',
        help='Test scenario to play out'
    )
    args = p.parse_args()

    # Initialize the test support context
    g_ctx = TestContext(args)
    g_ctx.run_test(args)

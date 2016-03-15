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
    constrained_sum_sample_pos, rm_file, determine_binary, ts_now,
    seconds_in_future, create_votes_array, arr_str, eval_test, write_js,
    count_token_votes, create_genesis, calculate_reward, tokens_after_split,
    calculate_closing_time, extract_test_dict, edit_dao_source
)
from args import test_args


class TestContext():
    def __init__(self, args):
        self.args = args
        self.tests_ok = True
        self.dao_addr = None  # check to determine if DAO is deployed
        self.offer_addr = None  # check to determine if offer is deployed
        self.token_amounts = None  # check to determine if funding happened
        self.prop_id = None  # check to if we have ran proposal scenario
        self.tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.save_file = os.path.join(self.tests_dir, "data", "saved")
        self.templates_dir = os.path.join(self.tests_dir, 'templates')
        self.contracts_dir = os.path.dirname(self.tests_dir)
        self.solc = determine_binary(args.solc, 'solc')
        self.geth = determine_binary(args.geth, 'geth')

        self.min_value = args.min_value
        self.test_scenarios = {
            'none': self.run_test_none,
            'deploy': self.run_test_deploy,
            'fund': self.run_test_fund,
            'proposal': self.run_test_proposal,
            'rewards': self.run_test_rewards,
            'split': self.run_test_split,
            'split-insufficient-gas': self.run_test_split_insufficient_gas,
        }

        # keep this at end since any data loaded should override constructor
        if args.clean_chain:
            self.clean_blockchain()
            self.create_accounts(args.users_num)
        else:
            self.attemptLoad()

    def create_accounts(self, accounts_num):
        print("Creating accounts and genesis block ...")
        with open(
                os.path.join(self.templates_dir, 'accounts.template.js'),
                'r'
        ) as f:
            data = f.read()
        tmpl = Template(data)
        s = tmpl.substitute(accounts_number=accounts_num)
        with open('accounts.js', "w") as f:
            f.write(s)
        output = self.run_script('accounts.js')
        self.accounts = json.loads(output)
        # creating genesis block with a generous allocation for all accounts
        create_genesis(self.accounts)
        print("Done!")

    def next_proposal_id(self):
        self.prop_id += 1
        return self.prop_id

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
            self.offer_addr = data['offer_addr']
            self.closing_time = data['closing_time']
            print("Loaded dao_addr: {}".format(self.dao_addr))
            print("Loaded dao_creator_addr: {}".format(self.dao_creator_addr))

    def clean_blockchain(self):
        """Clean all blockchain data directories apart from the keystore"""
        print("Cleaning blockchain data directory ...")
        data_dir = os.path.join(self.tests_dir, "data")
        shutil.rmtree(os.path.join(data_dir, "chaindata"), ignore_errors=True)
        shutil.rmtree(os.path.join(data_dir, "dapp"), ignore_errors=True)
        shutil.rmtree(os.path.join(data_dir, "keystore"), ignore_errors=True)
        rm_file(os.path.join(data_dir, "nodekey"))
        rm_file(os.path.join(data_dir, "saved"))

    def run_script(self, script):
        if script == 'accounts.js':
            return subprocess.check_output([
                self.geth,
                "--networkid",
                "123",
                "--nodiscover",
                "--maxpeers",
                "0",
                "--datadir",
                "./data",
                "--verbosity",
                "0",
                "js",
                script
            ])
        else:
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
        dao_contract = edit_dao_source(
            self.contracts_dir,
            keep_limits
        )

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

        # also delete the temporary created files
        rm_file(os.path.join(self.contracts_dir, "DAOcopy.sol"))
        rm_file(os.path.join(self.contracts_dir, "TokenSaleCopy.sol"))

    def create_js_file(self, name, substitutions, cb_before_creation=None):
        """
        Creates a js file from a template

        Parameters
        ----------
        name : string
        The name of the javascript file without the '.js' extension

        substitutions : dict
        A dict of the substitutions to make in the template
        file in order to produce the final js

        cb_before_creation : function
        (Optional) A callback function to be called right before substitution.
        It should accept the following arguments:
        (test_framework_object, name_of_js_file, substitutions_dict)
        and it returns the edited substitutions map
        """
        print("Creating {}.js".format(name))
        with open(
                os.path.join(self.templates_dir, '{}.template.js'.format(name)),
                'r'
        ) as f:
            data = f.read()
        tmpl = Template(data)
        if cb_before_creation:
            substitutions = cb_before_creation(self, name, substitutions)
        s = tmpl.substitute(substitutions)
        write_js("{}.js".format(name), s, len(self.accounts))

    def run_test_deploy(self):
        print("Running the Deploy Test Scenario")
        self.create_js_file(
            'deploy',
            {
                "dao_abi": self.dao_abi,
                "dao_bin": self.dao_bin,
                "creator_abi": self.creator_abi,
                "creator_bin": self.creator_bin,
                "offer_abi": self.offer_abi,
                "offer_bin": self.offer_bin,
                "offer_onetime": self.args.offer_onetime_costs,
                "offer_total": self.args.offer_total_costs,
                "min_value": self.min_value,
            },
            calculate_closing_time
        )
        output = self.run_script('deploy.js')
        results = extract_test_dict('deploy', output)

        try:
            self.dao_creator_addr = results['dao_creator_address']
            self.dao_addr = results['dao_address']
            self.offer_addr = results['offer_address']
        except:
            print(
                "ERROR: Could not find expected results in the deploy scenario"
                ". The output was:\n{}".format(output)
            )
            sys.exit(1)
        print("DAO Creator address is: {}".format(self.dao_creator_addr))
        print("DAO address is: {}".format(self.dao_addr))
        print("SampleOffer address is: {}".format(self.offer_addr))
        with open(self.save_file, "w") as f:
            f.write(json.dumps({
                "dao_creator_addr": self.dao_creator_addr,
                "dao_addr": self.dao_addr,
                "offer_addr": self.offer_addr,
                "closing_time": self.closing_time
            }))

    def run_test_fund(self):
        # if deployment did not already happen do it now
        if not self.dao_addr:
            self.run_test_deploy()
        else:
            print(
                "WARNING: Running the funding scenario with a pre-deployed "
                "DAO contract. Closing time is {} which is approximately {} "
                "seconds from now.".format(
                    datetime.fromtimestamp(self.closing_time).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    self.closing_time - ts_now()
                )
            )

        sale_secs = self.closing_time - ts_now()
        self.total_supply = self.min_value + random.randint(1, 100)
        self.token_amounts = constrained_sum_sample_pos(
            len(self.accounts), self.total_supply
        )
        self.create_js_file(
            'fund',
            {
                "dao_abi": self.dao_abi,
                "dao_address": self.dao_addr,
                "wait_ms": (sale_secs-3)*1000,
                "amounts": arr_str(self.token_amounts)
            }
        )
        print(
            "Notice: Funding period is {} seconds so the test will wait "
            "as much".format(sale_secs)
        )
        output = self.run_script('fund.js')
        eval_test('fund', output, {
            "dao_funded": True,
            "total_supply": self.total_supply,
            "balances": self.token_amounts,
            "user0_after": self.token_amounts[0],
        })

    def run_test_proposal(self):
        if not self.token_amounts:
            # run the funding scenario first
            self.run_test_fund()

        debate_secs = 20
        minamount = 2  # is determined by the total costs + one time costs
        amount = random.randint(minamount, sum(self.token_amounts))
        votes = create_votes_array(
            self.token_amounts,
            not self.args.proposal_fail
        )
        yay, nay = count_token_votes(self.token_amounts, votes)
        # self.create_proposal_js(amount, debate_secs, votes)
        self.create_js_file(
            'proposal',
            {
                "dao_abi": self.dao_abi,
                "dao_address": self.dao_addr,
                "offer_abi": self.offer_abi,
                "offer_address": self.offer_addr,
                "offer_amount": amount,
                "offer_desc": 'Test Proposal',
                "proposal_deposit": self.args.proposal_deposit,
                "transaction_bytecode": '0x2ca15122',  # solc --hashes SampleOffer.sol
                "debating_period": debate_secs,
                "votes": arr_str(votes)
            }
        )
        print(
            "Notice: Debate period is {} seconds so the test will wait "
            "as much".format(debate_secs)
        )
        output = self.run_script('proposal.js')
        eval_test('proposal', output, {
            "dao_proposals_number": "1",
            "proposal_passed": True,
            "proposal_yay": yay,
            "proposal_nay": nay,
            "calculated_deposit": self.args.proposal_deposit,
            "onetime_costs": self.args.offer_onetime_costs,
            "deposit_returned": True,
            "offer_promise_valid": True
        })
        self.prop_id = 1

    def run_test_rewards(self):
        if not self.prop_id:
            # run the proposal scenario first
            self.run_test_proposal()

        debate_secs = 15
        self.create_js_file(
            'rewards',
            {
                "dao_abi": self.dao_abi,
                "dao_address": self.dao_addr,
                "total_rewards": self.args.total_rewards,
                "proposal_deposit": self.args.proposal_deposit,
                "transaction_bytecode": '0x0',  # fallback function
                "debating_period": debate_secs,
                "prop_id": self.next_proposal_id()
            }
        )
        print(
            "Notice: Debate period is {} seconds so the test will wait "
            "as much".format(debate_secs)
        )
        output = self.run_script('rewards.js')
        results = eval_test('rewards', output, {
            "provider_reward_portion": calculate_reward(
                self.token_amounts[0],
                self.total_supply,
                self.args.total_rewards)
        })
        self.dao_balance_after_rewards = results['DAO_balance']
        self.dao_rewardToken_after_rewards = results['DAO_rewardToken']

    def prepare_test_split(self, split_gas):
        if self.prop_id != 2:
            # run the rewards scenario first
            self.run_test_rewards()

        debate_secs = 15
        votes = create_votes_array(
            self.token_amounts,
            not self.args.proposal_fail
        )
        self.create_js_file(
            'split',
            {
                "dao_abi": self.dao_abi,
                "dao_address": self.dao_addr,
                "debating_period": debate_secs,
                "split_gas": split_gas,
                "votes": arr_str(votes),
                "prop_id": self.next_proposal_id()
            }
        )
        print(
            "Notice: Debate period is {} seconds so the test will wait "
            "as much".format(debate_secs)
        )
        output = self.run_script('split.js')
        return votes, output

    def run_test_split(self):
        votes, output = self.prepare_test_split(4000000)
        oldBalance, newBalance, oldDAORewards, newDAORewards = tokens_after_split(
            votes,
            self.token_amounts,
            self.dao_balance_after_rewards,
            self.dao_rewardToken_after_rewards
        )
        eval_test('split', output, {
            # default deposit,a simple way to test new DAO contract got created
            "newDAOProposalDeposit": 20,
            "oldDAOBalance": oldBalance,
            "newDAOBalance": newBalance,
            "oldDaoRewardTokens": oldDAORewards,
            "newDaoRewardTokens": newDAORewards
        })

    def run_test_split_insufficient_gas(self):
        """
        Test that splitting with insufficient gas, will fail reliably and will
        not leave an empty contract in the state burning away user tokens in
        the process.

        This should happen with the latest homestead changes:
        https://github.com/ethereum/EIPs/blob/master/EIPS/eip-2.mediawiki#specification
        """
        votes, output = self.prepare_test_split(1000)
        oldBalance, newBalance, oldDAORewards, newDAORewards = tokens_after_split(
            votes,
            self.token_amounts,
            self.dao_balance_after_rewards,
            self.dao_rewardToken_after_rewards
        )
        eval_test('split-insufficient-gas', output, {
            "newDAOProposalDeposit": 0,
            "oldDAOBalance": self.token_amounts,
            "newDAOBalance": [0] * len(self.token_amounts),
        })

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

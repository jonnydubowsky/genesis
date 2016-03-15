#!/usr/bin/python2
import argparse
import sys


def test_args():
    """ Parse the test arguments and create and return the arguments object"""
    p = argparse.ArgumentParser(description='DAO contracts test framework')
    p.add_argument(
        '--solc',
        help='Full path to the solc binary to use'
    )
    p.add_argument(
        '--geth',
        help='Full path to the geth binary to use'
    )
    p.add_argument(
        '--keep-limits',
        action='store_true',
        help=(
            'If given then the debate limits of the original '
            'contracts will not be removed'
        )
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
        help='Number of seconds from now when the newly created DAO sale ends',
        default=35
    )
    p.add_argument(
        '--min-value',
        type=int,
        help='Minimum value in Ether to consider the DAO crowdfunded',
        default=20
    )
    p.add_argument(
        '--proposal-fail',
        action='store_true',
        help='If given, then in the proposal scenario the voting will fail'
    )
    p.add_argument(
        '--proposal-deposit',
        type=int,
        help='The proposal deposit. Has to be more than 20 ether',
        default=22
    )
    p.add_argument(
        '--offer-onetime-costs',
        type=int,
        help='The one time costs (in ether) in the offer to the DAO',
        default=5
    )
    p.add_argument(
        '--offer-total-costs',
        type=int,
        help='The total costs (in ether) in the offer to the DAO',
        default=10
    )
    p.add_argument(
        '--users-num',
        type=int,
        help='The number of user accounts to create for the scenarios.'
        'Should be at least 3',
        default=5
    )
    p.add_argument(
        '--total-rewards',
        type=int,
        help='Amount of ether a kind soul will donate to the DAO'
        ' for the rewards scenario.',
        default=78
    )
    p.add_argument(
        '--scenario',
        choices=[
            'none',
            'deploy',
            'fund',
            'proposal',
            'rewards',
            'split',
            'split-insufficient-gas'
        ],
        default='none',
        help='Test scenario to play out'
    )
    args = p.parse_args()

    # Argument verification
    if args.users_num < 3:
        print("ERROR: Tests need 3 or more users")
        sys.exit(1)

    return args

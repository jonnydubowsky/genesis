#!/usr/bin/python2
import argparse


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
        '--proposal-fail',
        action='store_true',
        help='If given, then in the proposal scenario the voting will fail'
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
        '--scenario',
        choices=['none', 'deploy', 'fund', 'proposal'],
        default='none',
        help='Test scenario to play out'
    )
    return p.parse_args()

#!/usr/bin/python2
import calendar
import random
import os
import json
import sys
import math
from datetime import datetime
from jsutils import js_common_intro


def constrained_sum_sample_pos(n, total):
    """Return a randomly chosen list of n positive integers summing to total.
    Each such list is equally likely to occur."""

    dividers = sorted(random.sample(xrange(1, total), n - 1))
    return [a - b for a, b in zip(dividers + [total], [0] + dividers)]


def is_exe(fpath):
    return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def rm_file(f):
    try:
        os.remove(f)
    except OSError:
        pass


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


def ts_now():
    """ Return a unix timestamp representing the time in UTC right now"""
    return calendar.timegm(datetime.utcnow().utctimetuple())


def seconds_in_future(secs):
    return ts_now() + secs


def create_votes_array(amounts, succeed):
    votes = []
    total = sum(amounts)
    percentage = 0.0

    if not succeed:
        for val in amounts:
            ratio = val/float(total)
            if (percentage + ratio < 0.5):
                votes.append(True)
                percentage += ratio
            else:
                votes.append(False)
    else:
        for val in amounts:
            ratio = val/float(total)
            if percentage <= 0.5:
                votes.append(True)
                percentage += ratio
            else:
                votes.append(False)

    return votes


def arr_str(arr):
    return '[ ' + ', '.join([str(x).lower() for x in arr]) + ' ]'


def extract_test_dict(name, output):
    split = output.split('Test Results: ', 1)
    if len(split) != 2:
        print("ERROR: Could not parse '{}' output properly.\n"
              "Output was:\n{}".format(
                  name, output
              ))
        sys.exit(1)
    try:
        result = json.loads(split[1])
    except:
        print("ERROR: Could not parse '{}' output properly.\n"
              "Output was:\n{}".format(
                  name, output
              ))
        sys.exit(1)
    return result


def eval_test(name, output, expected_dict):
    tests_fail = False
    results = extract_test_dict(name, output)

    for k, v in expected_dict.iteritems():
        if k not in results:
            tests_fail = True
            print("ERROR: Did not find '{}' in the test results".format(k))
            continue
        if results[k] != v:
            tests_fail = True
            print("ERROR: Expected {} for '{}' but got {}".format(
                v, k, results[k]
            ))

    if not tests_fail:
        print("Tests for '{}' PASSED!".format(name))
    else:
        print("Tests for '{}' FAILED!".format(name))
        sys.exit(1)


def write_js(name, contents, accounts_num):
    """Write a javascript file from a template, prepending common intro"""
    with open(name, "w") as f:
            f.write("{}\n{}".format(js_common_intro(accounts_num), contents))


def create_genesis(accounts):
    """Create a genesis block with ether allocation for the given accounts"""
    genesis = {}
    genesis["nonce"] = "0xdeadbeefdeadbeef"
    genesis["timestamp"] = "0x0"
    genesis["parentHash"] = "0x0000000000000000000000000000000000000000000000000000000000000000"
    genesis["extraData"] = "0x0"
    genesis["gasLimit"] = "0x8000000"
    genesis["difficulty"] = "0x000000001"
    genesis["mixhash"] = "0x0000000000000000000000000000000000000000000000000000000000000000"
    alloc = {}
    for acc in accounts:
        alloc[acc] = {"balance": "133700000000000000000000000000000000"}
    genesis["alloc"] = alloc
    with open('genesis_block.json', "w") as f:
        f.write(json.dumps(genesis))


def count_token_votes(amounts, votes):
    """Returns how many tokens votes yay and how many voted nay"""
    yay = 0
    nay = 0
    for idx, amount in enumerate(amounts):
        if votes[idx]:
            yay += amount
        else:
            nay += amount
    return yay, nay


def calculate_reward(tokens, total_tokens, total_rewards):
    return math.ceil((tokens * total_rewards) / total_tokens)


def calculate_closing_time(obj, script_name, substitutions):
    obj.closing_time = seconds_in_future(obj.args.closing_time)
    substitutions['closing_time'] = obj.closing_time
    return substitutions

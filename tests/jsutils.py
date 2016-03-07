#!/usr/bin/python2


def js_common_intro():
    """Common  functions, variables to add to all js scripts"""
    return """console.log("unlocking accounts");
personal.unlockAccount(eth.accounts[0], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[1], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[2], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[3], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[4], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[5], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[6], "Write here a good, randomly generated, passphrase!");
// set coinbase to something other than service provider and proposal creator
web3.miner.setEtherbase(eth.accounts[5]);

var serviceProvider = eth.accounts[0];
var proposalCreator = eth.accounts[1];
var testMap = {};

function checkWork() {
    miner.start(1);
    admin.sleepBlocks(3);
    miner.stop(0);
}

function bigDiff(astr, bstr) {
    return Math.round((new BigNumber(astr)).minus(new BigNumber(bstr)));
}

function addToTest(name, value) {
    testMap[name] = value;
    console.log("'" + name + "' = " + value);
}

function testResults() {
    console.log("Test Results: " + JSON.stringify(testMap));
}
"""

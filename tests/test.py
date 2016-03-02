#!/usr/bin/python2

# Use test.py with any valid combination of arguments in order to run
# DAO test scenarios

import argparse
import os
import json
import subprocess
import shutil
import sys
from datetime import datetime
datetime.utcnow()


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


def get_solc(given_solc):
    """Determines path to solc we will be using"""
    if given_solc:
        if is_exe(given_solc):
            return given_solc
    else:
        # try to find solc in the PATH
        return which("solc")
    return None


class TestContext():
    def __init__(self, args):
        self.tests_dir = os.path.dirname(os.path.realpath(__file__))
        self.contracts_dir = os.path.dirname(self.tests_dir)
        self.solc = get_solc(args.solc)
        if args.clean_chain:
            self.clean_blockchain()

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
            print("No valid solc compiler provided")
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

g_ctx = None


def create_deploy_js(dabi, dbin, cabi, cbin):
    print("Rewritting deploy.js using the compiled contract...")
    f = open("deploy.js", "w")
    f.write(
        """// geth --networkid 123 --nodiscover --maxpeers 0 --genesis ./genesis_block.json --datadir ./data  js deploy.js 2>>out.log.geth

console.log("unlocking account");
personal.unlockAccount(
    web3.eth.accounts[0],
    "Write here a good, randomly generated, passphrase!"
);

function checkWork() {
    if (!eth.mining) {
       setTimeout(function() {
            miner.stop(0);
        }, 3000);
        miner.start(1);
    } else {
        miner.stop(0);
    }
   // if (eth.getBlock("pending").transactions.length > 0) {
   //     if (eth.mining) return;
   //     console.log("== Pending transactions! Mining...");
   //     miner.start(1);
   // } else {
   //     miner.stop(0);  // This param means nothing
   //     console.log("== No transactions! Mining stopped.");
   // }
}

var _defaultServiceProvider = web3.eth.accounts[0];

var daoContract = web3.eth.contract(""")
    f.write(dabi)
    f.write(""");

console.log("Creating DAOCreator Contract");
var creatorContract = web3.eth.contract(""")
    f.write(cabi)
    f.write(""");
var _daoCreatorContract = creatorContract.new({from: web3.eth.accounts[0], data: '""");
    f.write(cbin)
    f.write("""',
gas: 3000000
   }, function(e, contract){
       if (e) {
           console.log(e+" at DAOCreator creation!");
       }
       if (typeof contract.address != 'undefined') {
           console.log('DAOCreator mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
           checkWork();
           var dao = daoContract.new(
               _defaultServiceProvider,
               contract.address,
               20,
               1556842261,
        {
            from: web3.eth.accounts[0],
            data: '""")
    f.write(dbin)
    f.write(
        """',
            gas: 3000000,
            gasPrice: 500000000000
   }, function(e, contract){
    // funny thing, without this geth hangs
    console.log("At DAO creation callback");
    if (typeof contract.address != 'undefined') {
         console.log('DAO Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
    }
 });
        checkWork();
       }
   });
checkWork();

console.log("mining contract, please wait");""")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description='DAO contracts test helper')
    p.add_argument(
        '--solc',
        help='Full path to the solc binary'
    )
    p.add_argument('--clean-chain', action='store_true')
    args = p.parse_args()

    # Initialize the test support context
    g_ctx = TestContext(args)

    dabi, dbin, cabi, cbin = g_ctx.compile_contracts()
    create_deploy_js(dabi, dbin, cabi, cbin)

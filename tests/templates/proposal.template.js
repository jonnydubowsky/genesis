console.log("unlocking accounts of token holders");
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

function checkWork() {
    miner.start(1);
    admin.sleepBlocks(3);
    miner.stop(0);
}

var dao = web3.eth.contract($dao_abi).at('$dao_address');

console.log("Add offer contract as allowed recipient");
dao.addAllowedAddress.sendTransaction('$offer_address', {from: serviceProvider, gas: 1000000});
checkWork();

console.log("CHECK(pCreatorBalanceStart): " + web3.fromWei(eth.getBalance(proposalCreator)));
console.log("Creating a new proposal for $offer_amount ether.");
var tx_hash = null;
dao.newProposal.sendTransaction(
    '$offer_address',
    web3.toWei($offer_amount, "ether"),
    '$offer_desc',
    '$transaction_bytecode',
    $debating_period,
    false,
    {
        from: proposalCreator,
        value: web3.toWei(21, "ether"), // default proposal deposit is 20 ether
        gas: 1000000
    }
    , function (e, res) {
        if (e) {
            console.log(e + "at newProposal()!");
        } else {
            tx_hash = res;
            console.log("newProposal tx hash is: " + tx_hash);
        }
    }
);
checkWork();

console.log("CHECK(pCreatorBalanceAfterProposal): " + web3.fromWei(eth.getBalance(proposalCreator)));
console.log("CHECK(dao.numberOfProposals): " + dao.numberOfProposals());

var votes = $votes;
var prop_id = 0;

console.log("Deadline is: " + dao.proposals(prop_id)[3] + " Voting ... ");
for (i = 0; i < votes.length; i++) {
    console.log("User " + i +" is voting ["+ votes[i] +"]. His token balance is: " + web3.fromWei(dao.balanceOf(eth.accounts[i])) + " ether and NOW is: " + Math.floor(Date.now() / 1000));
    dao.vote.sendTransaction(
        prop_id,
        votes[i],
        {
            from: eth.accounts[i],
            gas: 1000000
        }
    );
}
checkWork();
console.log("CHECK(proposal.numberOfVotes): " + dao.numberOfVotes(prop_id));
console.log("CHECK(serviceProviderbalancebefore): " + web3.fromWei(eth.getBalance(serviceProvider)));

setTimeout(function() {
    miner.stop(0);
    console.log("After debating period. NOW is: " + Math.floor(Date.now() / 1000));
    console.log("Executing proposal ...");
    dao.executeProposal.sendTransaction(prop_id, '$transaction_bytecode', {from:serviceProvider, gas:1000000});
    checkWork();

    
    console.log("CHECK(proposal.passed): " + dao.proposals(prop_id)[5]); // 5th member of the structure is proposalPassed
    console.log("CHECK(pCreatorBalanceAfterExecution): " + web3.fromWei(eth.getBalance(proposalCreator)));
    console.log("CHECK(serviceProviderbalanceafter): " + web3.fromWei(eth.getBalance(serviceProvider)));
}, $debating_period * 1000);
console.log("Wait for end of debating period");
miner.start(1);

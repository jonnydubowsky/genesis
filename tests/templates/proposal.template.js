var dao = web3.eth.contract($dao_abi).at('$dao_address');
var offer = web3.eth.contract($offer_abi).at('$offer_address');

console.log("Add offer contract as allowed recipient");
dao.addAllowedAddress.sendTransaction('$offer_address', {from: serviceProvider, gas: 1000000});
checkWork();

addToTest('creator_balance_before', web3.fromWei(eth.getBalance(proposalCreator)));
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
        value: web3.toWei($proposal_deposit, "ether"),
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

addToTest('creator_balance_after_proposal', web3.fromWei(eth.getBalance(proposalCreator)));
addToTest(
    'calculated_deposit',
    bigDiffRound(testMap['creator_balance_before'], testMap['creator_balance_after_proposal'])
);
addToTest('dao_proposals_number', dao.numberOfProposals());

var votes = $votes;
var prop_id = 1;

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
addToTest('proposal_yay', parseInt(web3.fromWei(dao.proposals(prop_id)[9])));
addToTest('proposal_nay', parseInt(web3.fromWei(dao.proposals(prop_id)[10])));
addToTest('provider_balance_before', web3.fromWei(eth.getBalance(serviceProvider)));

setTimeout(function() {
    miner.stop(0);
    console.log("After debating period. NOW is: " + Math.floor(Date.now() / 1000));
    console.log("Executing proposal ...");
    dao.executeProposal.sendTransaction(prop_id, '$transaction_bytecode', {from:serviceProvider, gas:1000000});
    checkWork();

    // 5th member of the structure is proposalPassed
    addToTest('proposal_passed', dao.proposals(prop_id)[5]);
    addToTest('creator_balance_after_execution', web3.fromWei(eth.getBalance(proposalCreator)));
    addToTest('provider_balance_after', web3.fromWei(eth.getBalance(serviceProvider)));

    addToTest(
        'onetime_costs',
        bigDiffRound(testMap['provider_balance_after'], testMap['provider_balance_before'])
    );
    addToTest(
        'deposit_returned',
        Math.round(testMap['creator_balance_after_execution']) == Math.round(testMap['creator_balance_before'])
    );
    addToTest('offer_promise_valid', offer.promiseValid());

    testResults();
}, $debating_period * 1000);
console.log("Wait for end of debating period");
miner.start(1);

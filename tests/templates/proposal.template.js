console.log("unlocking service provider account");
personal.unlockAccount(
    web3.eth.accounts[0],
    "Write here a good, randomly generated, passphrase!"
);

function checkWork() {
    miner.start(1);
    admin.sleepBlocks(3);
    miner.stop(0);
}

var dao = web3.eth.contract($dao_abi).at('$dao_address');

console.log("Add offer contract as allowed recipient");
dao.addAllowedAddress.sendTransaction('$offer_address', {from: eth.accounts[0], gas: 1000000});
checkWork();

console.log("CHECK(serviceprovider): " + dao.serviceProvider() + " == " + eth.accounts[0]);
console.log("CHECK(offer_is_allowed_recipient): " + dao.allowedRecipients(0));
console.log("CHECK(offer_is_allowed_recipient): " + dao.allowedRecipients('$offer_address'));

console.log("Creating a new proposal");
var tx_hash = null;
dao.newProposal.sendTransaction(
    '$offer_address',
    web3.toWei($offer_amount, "ether"),
    '$offer_desc',
    '$transaction_bytecode',
    $debating_period,
    false,
    {
        from: eth.accounts[0],
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

console.log("CHECK(dao.numberOfProposals): " + dao.numberOfProposals());

console.log("unlocking accounts of token holders");
personal.unlockAccount(eth.accounts[1], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[2], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[3], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[4], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[5], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[6], "Write here a good, randomly generated, passphrase!");

var votes = $votes;
var prop_id = 0;

console.log("Deadline is: " + dao.proposals(prop_id)[3] + " Voting ... ");
for (i = 0; i < votes.length; i++) {
    console.log("User " + i +" is voting ["+ votes[i] +"]. His balance is: " + dao.balanceOf(eth.accounts[i]) + " and NOW is: " + Math.floor(Date.now() / 1000));
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

setTimeout(function() {
    miner.stop(0);
    console.log("After debating period. NOW is: " + Math.floor(Date.now() / 1000));
    console.log("Executing proposal ...");
    dao.executeProposal(prop_id, '$transaction_bytecode',{from:eth.accounts[0], gas:1000000});
    checkWork();

    console.log("CHECK(proposal.passed): " + dao.proposals(prop_id)[5]); // 5th member of the structure is the proposal passed thing
}, $debating_period * 1000);
console.log("Wait for end of debating period");
miner.start(1);

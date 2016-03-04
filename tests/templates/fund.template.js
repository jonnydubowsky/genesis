function checkWork() {
    if (eth.getBlock("pending").transactions.length > 0) {
        if (eth.mining) return;
        console.log("== Pending transactions! Mining...");
        miner.start(1);
    } else {
        miner.stop(0);  // This param means nothing
        console.log("== No transactions! Mining stopped.");
    }
}

console.log("unlocking accounts");
personal.unlockAccount(eth.accounts[0], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[1], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[2], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[3], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[4], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[5], "Write here a good, randomly generated, passphrase!");
personal.unlockAccount(eth.accounts[6], "Write here a good, randomly generated, passphrase!");

var amounts = [
    $userval0,
    $userval1,
    $userval2,
    $userval3,
    $userval4,
    $userval5,
    $userval6
];
var dao = web3.eth.contract($dao_abi).at('$dao_address');
console.log("Buying DAO tokens");
for (i = 0; i < eth.accounts.length; i++) {
    web3.eth.sendTransaction({
        from:eth.accounts[i],
        to: dao.address,
        gas:100000,
        value:web3.toWei(amounts[i], "ether")
    });
}

checkWork();

console.log("Wait for end of sale");
setTimeout(function() {
    miner.stop(0);
    console.log("CHECK(dao.funded): " + dao.isFunded());
    console.log("CHECK(dao.totalSupply): " + web3.fromWei(dao.totalSupply()));
    for (i = 0; i < eth.accounts.length; i++) {
        console.log("CHECK(balanceuser" + i +"): " + web3.fromWei(dao.balanceOf(eth.accounts[i])));
    }

    // now also try to purchase some extra tokens after the sale ended
    web3.eth.sendTransaction({
        from:eth.accounts[0],
        to: dao.address,
        gas:100000,
        value:web3.toWei(20, "ether")
    });
    // and confirm balance is still the same
    checkWork();
    console.log("CHECK(afterbalanceuser0): " + web3.fromWei(dao.balanceOf(eth.accounts[0])));

}, $wait_ms);
miner.start(1);

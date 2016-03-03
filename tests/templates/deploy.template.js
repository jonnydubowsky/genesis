// geth --networkid 123 --nodiscover --maxpeers 0 --genesis ./genesis_block.json --datadir ./data  js deploy.js 2>>out.log.geth

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
    if (eth.getBlock("pending").transactions.length > 0) {
        if (eth.mining) return;
        console.log("== Pending transactions! Mining...");
        miner.start(1);
    } else {
        miner.stop(0);  // This param means nothing
        console.log("== No transactions! Mining stopped.");
    }
}

var _defaultServiceProvider = web3.eth.accounts[0];
var daoContract = web3.eth.contract($dao_abi);
console.log("Creating DAOCreator Contract");
var creatorContract = web3.eth.contract($creator_abi);
var _daoCreatorContract = creatorContract.new(
    {
	from: web3.eth.accounts[0],
	data: '$creator_bin',
	gas: 3000000
    }, function (e, contract){
	if (e) {
            console.log(e+" at DAOCreator creation!");
	}
	if (typeof contract.address != 'undefined') {
	    console.log('dao_creator_address: ' + contract.address);
            checkWork();
            var dao = daoContract.new(
		_defaultServiceProvider,
		contract.address,
		$min_value,
		$closing_time,
		{
		    from: web3.eth.accounts[0],
		    data: '$dao_bin',
		    gas: 3000000,
		    gasPrice: 500000000000
		}, function (e, contract) {
		    // funny thing, without this geth hangs
		    console.log("At DAO creation callback");
		    if (typeof contract.address != 'undefined') {
			console.log('dao_address: ' + contract.address);
		    }
		});
            checkWork();
	}
    });
checkWork();
console.log("mining contract, please wait");


# Tests for the DAO contracts

## Using the test framework

For the full array of arguments available run `test.py --help`

An example scenario you can run is the deploy scenario. Below you can see a sample test command showcasing many of the arguments:

```
./test.py --solc ~/ew/solidity/build/solc/solc --clean-chain --closing-time 60 --min-value 50 --scenario deploy --geth $GOPATH/src/github.com/ethereum/go-ethereum/build/bin/geth
```

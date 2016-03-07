# Tests for the DAO contracts

## Using the test framework

For the full array of arguments available run `test.py --help`

```
usage: test.py [-h] [--solc SOLC] [--geth GETH] [--keep-limits]
               [--clean-chain] [--verbose] [--closing-time CLOSING_TIME]
               [--min-value MIN_VALUE] [--scenario {none,deploy,fund}]

DAO contracts test framework

optional arguments:
  -h, --help            show this help message and exit
  --solc SOLC           Full path to the solc binary to use
  --geth GETH           Full path to the geth binary to use
  --keep-limits         If given then the debate limits of the original
                        contracts will not be removed
  --clean-chain         If given then the blockchain is deleted before any
                        test scenario is executed
  --verbose             If given then all test checks are printed in the
                        console
  --closing-time CLOSING_TIME
                        Number of minutes from now when the newly created DAO
                        sale ends
  --min-value MIN_VALUE
                        Minimum value to consider the DAO crowdfunded
  --scenario {none,deploy,fund}
                        Test scenario to play out
```

An example scenario you can run is the deploy scenario. Below you can see a sample test command showcasing many of the arguments:

```
./test.py --solc ~/ew/solidity/build/solc/solc --clean-chain --closing-time 60 --min-value 50 --scenario deploy --geth $GOPATH/src/github.com/ethereum/go-ethereum/build/bin/geth --verbose
```

## Scenarios

- *Deploy*
  The deploy scenario essentially creates both a DaoCreator and a DAO contract printing their
  addresses and remembering them in the framework.
- *Fund*
  The fund scenario either uses a previously deployed contract or if there is none calls the
  deploy scenario in order to create a DAO contract. Then it purchases a random number of tokens,
  enough to satisfy the sale and reach the minimum goal. It tests that tokens are bought correctly
  and that nothing can be bought after the sale period has expired.

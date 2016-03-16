# The DAO

## What is it? 
A generic DAO (Decentralized Autonomous Organization) written in Solidity to run on the Ethereum block chain. 
Simple, decentralized and 100% secure.
Feel free to reuse to create your own Decentralized organization.


## How it works

A DAO is an organization that's self-governing and not influenced by outside forces: its software operates on its own, with its by-laws immutably written on the blockchain, not controlled by its creators. DAOs are formed by groups of like-minded individuals with specific projects and goals in mind.

Would-be participants in the DAO can for a period of time acquire DAO tokens by sending Ether to the DAO. These tokens will give them the right to vote on business decisions (proportional to the number of tokens acquired) as well the opportunity to receive the rewards generated by the products and services built on the DAO's behalf by the Service Provider. 

A DAO purely manages funds: in itself it does not have the capabilities to build a product, write code or develop hardware. It requires a Service Provider for this purpose, which it hires by signing off on a proposal. This proposal is written in plain English and backed by smart contract defining the relationship between the DAO and its Service Provider: deliverables, responsibilities and operating parameters. All discussions around proposals take place off-chain on a service chosen by the DAO's community.

While the Service Provider is bound by the term of the proposal, the DAO participants can elect to ‘pull the plug’ on the Service Provider at anytime if they feel they are not getting their money’s worth. This is a major advantage over the Kickstarter or 'pre-sale' models as it considerably minimizes risk. 

It is also possible for the DAO to elect a replacement Service Provider, meaning that the project can continue where it left off. In essence, by decoupling finance from operations this DAO model survives where other means of funding would have failed.

The incentive to the DAO will take the form of revenue generated through the product and services built by its Service Providers, effectively creating a symbiotic relationship between the two.

This DAO model is open source under the LGPL, so it can be reused by anyone wishing to put together a transparent organization where governance and decision making system are immutably programmed in the Blockchain. 


## Licensing
The DAO is free software: you can redistribute it and/or modify
it under the terms of the GNU lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The DAO is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU lesser General Public License for more details.

A copy of the GNU lesser General Public License is included
along with the DAO. See LICENSE.


## Solidity files

### DAO.sol:
Generic contract for a Decentralized Autonomous Organisation (DAO) to manage a trust

### Token.sol: 
Defines the functions to check token balances, send tokens, send tokens on behalf of a 3rd party and its corresponding approval process.

#### TokenSale.sol: 
Token Sale contract, used by the DAO to raise its funding goal

### SampleOffer.sol
Sample Proposal from a Service Provider to the DAO

### ManagedAccount.sol
Basic account, managed by another contract

### DAOTokenSaleProxyTransferer.sol
This contract is used as a fall back in case an exchange doesn't implement the "add data to a transaction" feature in a timely manner, preventing it from calling buyTokenProxy().


## Contact
Please contact us on [slack](https://genesisdao.slack.com/messages/general/)


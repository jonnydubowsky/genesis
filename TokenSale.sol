/*
This file is part of the DAO.

The DAO is free software: you can redistribute it and/or modify
it under the terms of the GNU lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The DAO is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU lesser General Public License for more details.

You should have received a copy of the GNU lesser General Public License
along with the DAO.  If not, see <http://www.gnu.org/licenses/>.
*/


/*
Token Sale contract, used by the DAO to sell its tokens and initialize its fund
*/

import "./Token.sol";


contract TokenSaleInterface {
    
    // End of token sale, in Unix time
    uint public closingTime;   
    // Minimum funding goal of the token sale, denominated in tokens
    uint public minValue;  
    // True if the DAO reached its minimum funding goal, false otherwise
    bool public isFunded;   
    // For DAO splits - if privateSale is 0, then it is a public sale, otherwise
    // only the address stored in privateSale is allowed to purchase tokens
    address public privateSale;               
    
    /// @dev Constructor setting the minimum funding goal and the 
    /// end of the Token Sale
    /// @param _minValue Token Sale minimum funding goal
    /// @param _closingTime Date (in Unix time) of the end of the Token Sale
    // This is the constructor: it can not be overloaded so it is commented out
    //  function TokenSale(uint _minValue, uint _closingTime);

    /// @notice Buy Token with `_tokenHolder` as the initial owner of the Token
    /// @param _tokenHolder The address of the Tokens's recipient 
    function buyTokenProxy(address _tokenHolder) returns (bool success);

    /// @notice Refund `msg.sender` in the case the Token Sale didn't reach its 
    /// minimum funding goal
    function refund();

    event FundingToDate(uint value);
    event SoldToken(address indexed to, uint amount);
    event Refund(address indexed to, uint value);
}


contract TokenSale is TokenSaleInterface, Token {
    function TokenSale(uint _minValue, uint _closingTime, address _privateSale) {
        closingTime = _closingTime;
        minValue = _minValue;
        privateSale = _privateSale;
    }

    function buyTokenProxy(address _tokenHolder) returns (bool success) {
        if (now < closingTime && msg.value > 0 
        && (privateSale == 0 || privateSale == msg.sender)) {
            uint token = msg.value;
            balances[_tokenHolder] += token;
            totalSupply += token;
            SoldToken(_tokenHolder, token);
            if (totalSupply >= minValue && !isFunded) {
                isFunded = true;
                FundingToDate(totalSupply);
            }
            return true;
        }
        throw;
    }

    function refund() noEther {
        if (now > closingTime
            && !isFunded
            && msg.sender.send(balances[msg.sender])) // execute refund
        {
            Refund(msg.sender, balances[msg.sender]);
            totalSupply -= balances[msg.sender];
            balances[msg.sender] = 0;
        }
    }
}

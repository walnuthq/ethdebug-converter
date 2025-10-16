//SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;
contract Counter {
    uint256 public count;

    function increment() public {
        count += 1;
    }

    function getCount() public view returns (uint256) {
        return count;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract FaceVerification {
    struct Record {
        bytes32 dataHash;
        uint256 timestamp;
        address submitter;
    }

    mapping(uint256 => Record) public records;
    uint256 public recordCount;

    event RecordStored(
        uint256 indexed id,
        bytes32 dataHash,
        address indexed submitter,
        uint256 timestamp
    );

    function storeRecord(bytes32 _dataHash) public returns (uint256) {
        uint256 id = recordCount++;
        records[id] = Record(_dataHash, block.timestamp, msg.sender);
        emit RecordStored(id, _dataHash, msg.sender, block.timestamp);
        return id;
    }

    function getRecord(uint256 _id) public view returns (bytes32, uint256, address) {
        Record memory r = records[_id];
        return (r.dataHash, r.timestamp, r.submitter);
    }

    function verifyRecord(uint256 _id, bytes32 _dataHash) public view returns (bool) {
        return records[_id].dataHash == _dataHash;
    }
}

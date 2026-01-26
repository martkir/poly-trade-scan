"""Polymarket ABI definitions for transaction decoding."""

# Order struct: (salt, maker, signer, taker, tokenId, makerAmount, takerAmount, expiration, nonce, feeRateBps, side, signatureType, signature)
ORDER_TUPLE_TYPE = "(uint256,address,address,address,uint256,uint256,uint256,uint256,uint256,uint256,uint8,uint8,bytes)"

# matchOrders selector - same for both Fee Module and NegRisk Fee Module 2
# MethodID: 0x2287e350
MATCH_ORDERS_SELECTOR = bytes.fromhex("2287e350")

# ABI types for matchOrders (7 params) - same for both contracts
# matchOrders(tuple takerOrder, tuple[] makerOrders, uint256 takerFillAmount,
#             uint256 takerReceiveAmount, uint256[] makerFillAmounts,
#             uint256 takerFeeAmount, uint256[] makerFeeAmounts)
MATCH_ORDERS_ABI_TYPES = [
    ORDER_TUPLE_TYPE,           # takerOrder
    f"{ORDER_TUPLE_TYPE}[]",    # makerOrders array
    "uint256",                  # takerFillAmount
    "uint256",                  # takerReceiveAmount
    "uint256[]",                # makerFillAmounts
    "uint256",                  # takerFeeAmount
    "uint256[]",                # makerFeeAmounts
]

# Legacy aliases (both contracts use same selector)
CTF_MATCH_ORDERS_SELECTOR = MATCH_ORDERS_SELECTOR
NEGRISK_MATCH_ORDERS_SELECTOR = MATCH_ORDERS_SELECTOR

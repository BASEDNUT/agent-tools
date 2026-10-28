"""Auditable read-interface ABI signatures sourced from Balancer V3 and ERC specifications.

Intentionally not a claim of complete ABI. A contract implementation still requires
its verified exact build artifact/ABI before any signing or approval decision.
"""
from .evm import selector, keccak256
from .rpc import ChainError

READ_SIGNATURES={
 'RootstockVault':[
  'getPoolTokens(address)', 'getPoolTokenInfo(address)',
  'getPoolTokenRates(address)', 'getStaticSwapFeePercentage(address)',
  'isPoolRegistered(address)',
 ],
 'RootstockRouter':['querySwapSingleTokenExactIn(address,address,address,uint256,address,bytes)'],
 'ERC20':['name()','symbol()','decimals()','totalSupply()','balanceOf(address)','allowance(address,address)'],
 'ERC4626':['asset()','convertToAssets(uint256)','convertToShares(uint256)','totalAssets()'],
}
def catalog():
    from .indexer import TOPICS
    return {'completeness':'partial_read_only','sources':[
        'https://github.com/balancer/balancer-v3-monorepo/blob/main/pkg/interfaces/contracts/vault/IVaultEvents.sol',
        'https://github.com/balancer/balancer-v3-monorepo/blob/main/pkg/interfaces/contracts/vault/IVaultExtension.sol',
        'https://eips.ethereum.org/EIPS/eip-20',
        'https://eips.ethereum.org/EIPS/eip-4626'],
       'interfaces':{iface:{s:selector(s) for s in signatures} for iface,signatures in READ_SIGNATURES.items()},
       'event_topics':TOPICS,'signing_approved':False}

def signature_info(interface:str,signature:str):
    if interface not in READ_SIGNATURES or signature not in READ_SIGNATURES[interface]:
        raise ChainError('No such reviewed partial read signature; never invent ABI')
    return {'interface':interface,'signature':signature,'selector':selector(signature),
            'scope':'reviewed read ABI signature, not exact deployed build ABI','signing_approved':False}

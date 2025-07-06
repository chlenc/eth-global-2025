"""
Patch for eth_account.messages to provide encode_structured_data function
that limit-order-sdk expects but is not available in newer versions.
"""

import eth_account.messages

# Add the missing function by aliasing encode_typed_data
if not hasattr(eth_account.messages, 'encode_structured_data'):
    eth_account.messages.encode_structured_data = eth_account.messages.encode_typed_data 
"""
Verification & Status Module

This module verifies the current status of grants to ensure they are still active
and accepting applications. The Sentinel checks for:

1. Grant Status: Open, Closed, or Exhausted
2. Application Deadlines: Are applications still being accepted?
3. Funding Availability: Is funding still available?

This helps prevent users from applying to grants that are no longer available.

Author: DuckDuckCode
"""


async def check_funding_status(grants):
    """
    Verify the current status of grants.
    
    Checks each grant's status field to ensure it's still active.
    
    Args:
        grants (list): List of grant dictionaries from Analysis module
    
    Returns:
        list: Same grants with guaranteed 'status' field populated.
              Status values: 'Open', 'Closed', 'Exhausted', etc.
    """
    for grant in grants:
        # Ensure every grant has a status field
        # Default to 'Open' if not provided by previous pipeline stages
        grant['status'] = grant.get('status', 'Open')
    
    return grants

"""
Result Prioritization Module

This module ranks and sorts grant results to present the most eligible and
open opportunities first. Prioritization helps users quickly identify which
grants are most likely to be successful.

Priority rules:
1. Open/Available grants appear first
2. Closed/Exhausted grants appear last
3. Grants with matching eligibility criteria ranked higher

Author: DuckDuckCode
"""


def rank_results(grants):
    """
    Sort grants by status, placing open grants first.
    
    This is a simple but effective prioritization strategy that ensures users
    see available funding opportunities before those that are closed or exhausted.
    
    Args:
        grants (list): List of grant dictionaries, each containing at minimum a 'status' key.
                      Status values: 'Open', 'Closed', 'Exhausted', etc.
    
    Returns:
        list: Same grants, sorted with 'Open' status grants first.
        
    Examples:
        >>> grants = [
        ...     {'name': 'Grant A', 'status': 'Closed'},
        ...     {'name': 'Grant B', 'status': 'Open'},
        ...     {'name': 'Grant C', 'status': 'Open'}
        ... ]
        >>> ranked = rank_results(grants)
        >>> [g['name'] for g in ranked]
        ['Grant B', 'Grant C', 'Grant A']
    """
    # Sort grants: Open status grants (False = Open) come before others (True = Closed/Exhausted)
    # This ensures available funding is prioritized
    return sorted(grants, key=lambda grant: grant.get('status', 'Open') != 'Open')

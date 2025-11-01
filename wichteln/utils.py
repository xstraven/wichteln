import random
import string
import re
from typing import Dict, List


def generate_unique_code(length: int = 5) -> str:
    """Generate a unique random code for participant identification."""
    letters = string.ascii_uppercase
    return "".join(random.choice(letters) for _ in range(length))


def generate_secret_santa_matches(participant_ids: List[int], constraints: Dict[int, List[int]] = None) -> Dict[int, int]:
    """
    Generate secret santa matches ensuring no one gets themselves.
    
    Args:
        participant_ids: List of participant IDs
        constraints: Dict mapping participant_id to list of participant_ids they cannot give to
        
    Returns:
        Dict mapping giver_id to receiver_id
    """
    if len(participant_ids) < 2:
        raise ValueError("Need at least 2 participants")
    
    if constraints is None:
        constraints = {}
    
    # Simple algorithm: try random permutations until we find a valid one
    max_attempts = 1000
    
    for _ in range(max_attempts):
        receivers = participant_ids.copy()
        random.shuffle(receivers)
        
        matches = {}
        valid = True
        
        for i, giver_id in enumerate(participant_ids):
            receiver_id = receivers[i]
            
            # Check if giver gets themselves
            if giver_id == receiver_id:
                valid = False
                break
                
            # Check constraints
            if giver_id in constraints and receiver_id in constraints[giver_id]:
                valid = False
                break
                
            matches[giver_id] = receiver_id
        
        if valid:
            return matches
    
    # Fallback: simple rotation (might violate some constraints)
    matches = {}
    for i, giver_id in enumerate(participant_ids):
        receiver_id = participant_ids[(i + 1) % len(participant_ids)]
        matches[giver_id] = receiver_id
    
    return matches


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[-1]


def slugify(value: str) -> str:
    """Simplified slugify helper to normalise identifier/email parts."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "item"

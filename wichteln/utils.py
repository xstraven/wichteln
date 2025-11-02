import random
import string
from typing import Dict, List
from wichteln.word_bank import WORD_BANK


def generate_identifier() -> str:
    """Generate a random 3-word PascalCase identifier for secret santa groups."""
    first = random.choice(WORD_BANK["first"])
    second = random.choice(WORD_BANK["second"])
    third = random.choice(WORD_BANK["third"])
    return f"{first}{second}{third}"


def generate_unique_code(length: int = 5) -> str:
    """Generate a unique random code for participant identification."""
    letters = string.ascii_uppercase
    return "".join(random.choice(letters) for _ in range(length))


def generate_secret_santa_matches(participant_ids: List[int], constraints: Dict[int, List[int]] = None) -> Dict[int, int]:
    """
    Generate secret santa matches ensuring no one gets themselves and all constraints are respected.

    Args:
        participant_ids: List of participant IDs (indices)
        constraints: Dict mapping participant_id to list of participant_ids they cannot give to

    Returns:
        Dict mapping giver_id to receiver_id (a valid derangement)

    Raises:
        ValueError: If constraints make a valid matching impossible
    """
    if len(participant_ids) < 2:
        raise ValueError("Need at least 2 participants")

    if constraints is None:
        constraints = {}

    # Try random permutations to find a valid derangement
    max_attempts = 5000  # Increased attempts for complex scenarios

    for _ in range(max_attempts):
        receivers = participant_ids.copy()
        random.shuffle(receivers)

        matches = {}
        valid = True

        for i, giver_id in enumerate(participant_ids):
            receiver_id = receivers[i]

            # Check if giver gets themselves (violates derangement property)
            if giver_id == receiver_id:
                valid = False
                break

            # Check if this violates a constraint
            if giver_id in constraints and receiver_id in constraints[giver_id]:
                valid = False
                break

            matches[giver_id] = receiver_id

        if valid:
            # Verify the solution is complete and valid
            _verify_matches(matches, participant_ids, constraints)
            return matches

    # If we couldn't find a valid matching, the constraints are likely impossible
    raise ValueError(
        "Could not find a valid gift assignment with the given constraints. "
        "Try removing some forbidden pairs to make it possible."
    )


def _verify_matches(matches: Dict[int, int], participant_ids: List[int], constraints: Dict[int, List[int]]) -> None:
    """
    Verify that matches form a valid derangement respecting all constraints.

    Raises:
        ValueError: If matches are invalid
    """
    # Check that all participants are givers exactly once
    if set(matches.keys()) != set(participant_ids):
        raise ValueError("Invalid matches: not all participants are givers")

    # Check that all participants are receivers exactly once
    if set(matches.values()) != set(participant_ids):
        raise ValueError("Invalid matches: not all participants are receivers or duplicates exist")

    # Check no self-matches
    for giver_id, receiver_id in matches.items():
        if giver_id == receiver_id:
            raise ValueError(f"Invalid matches: participant {giver_id} cannot gift themselves")

        # Check constraints are respected
        if giver_id in constraints and receiver_id in constraints[giver_id]:
            raise ValueError(
                f"Invalid matches: constraint violated - {giver_id} cannot gift to {receiver_id}"
            )


def validate_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[-1]

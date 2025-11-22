"""
Unit tests for the Secret Santa matching algorithm.

These tests directly test the generate_secret_santa_matches() function
to verify it produces valid outputs that satisfy all constraints.
"""

import pytest
from wichteln.utils import generate_secret_santa_matches


class TestCoreValidity:
    """Tests for basic matching validity properties."""

    def test_everyone_is_a_giver_exactly_once(self):
        """Verify all participants appear exactly once as givers."""
        participants = list(range(5))
        matches = generate_secret_santa_matches(participants)

        # All participants should be in the keys (givers)
        assert set(matches.keys()) == set(participants)
        # Each participant appears exactly once (no duplicates)
        assert len(matches.keys()) == len(participants)

    def test_everyone_is_a_receiver_exactly_once(self):
        """Verify all participants appear exactly once as receivers."""
        participants = list(range(5))
        matches = generate_secret_santa_matches(participants)

        # All participants should be in the values (receivers)
        assert set(matches.values()) == set(participants)
        # Each participant receives exactly once (no duplicates)
        assert len(matches.values()) == len(set(matches.values()))

    def test_no_self_matches(self):
        """Verify no participant is matched to themselves."""
        participants = list(range(10))
        matches = generate_secret_santa_matches(participants)

        for giver, receiver in matches.items():
            assert giver != receiver, f"Participant {giver} matched to themselves"

    def test_is_valid_permutation(self):
        """Verify the matching forms a valid permutation (derangement)."""
        participants = list(range(7))
        matches = generate_secret_santa_matches(participants)

        # Should be a complete cycle or set of cycles covering all participants
        visited = set()
        for start in participants:
            if start in visited:
                continue

            current = start
            cycle = []
            while current not in visited:
                visited.add(current)
                cycle.append(current)
                current = matches[current]

            # Cycle should not be length 1 (that would be self-match)
            assert len(cycle) > 1, f"Found self-loop at {start}"

        # All participants should be visited
        assert visited == set(participants)

    def test_deterministic_count_but_random_assignment(self):
        """Verify algorithm produces valid but potentially different results."""
        participants = list(range(4))

        # Run multiple times and collect results
        results = []
        for _ in range(10):
            matches = generate_secret_santa_matches(participants)
            results.append(tuple(sorted(matches.items())))

        # All results should be valid (tested by other tests running)
        # With randomness, we should see some variation in small runs
        # (though theoretically could get same result multiple times by chance)
        unique_results = set(results)

        # Each result should have correct count
        for result in unique_results:
            assert len(result) == len(participants)


class TestConstraintHandling:
    """Tests for constraint validation."""

    def test_simple_constraint_respected(self):
        """Verify a simple constraint is respected."""
        participants = list(range(4))
        constraints = {0: [1]}  # Participant 0 cannot give to 1

        matches = generate_secret_santa_matches(participants, constraints)

        assert matches[0] != 1, "Constraint violated: 0 gave to 1"

    def test_multiple_constraints_respected(self):
        """Verify multiple constraints are all respected."""
        participants = list(range(5))
        constraints = {
            0: [1, 2],  # 0 cannot give to 1 or 2
            2: [3],     # 2 cannot give to 3
            4: [0]      # 4 cannot give to 0
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Verify each constraint
        assert matches[0] not in [1, 2], "Constraint violated for participant 0"
        assert matches[2] != 3, "Constraint violated for participant 2"
        assert matches[4] != 0, "Constraint violated for participant 4"

    def test_all_constraints_checked(self):
        """Verify no constraint violations in complex scenario."""
        participants = list(range(6))
        constraints = {
            0: [1, 5],
            1: [2],
            2: [3, 4],
            3: [0],
            4: [1, 5]
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Check every constraint
        for giver, forbidden_receivers in constraints.items():
            assert matches[giver] not in forbidden_receivers, \
                f"Participant {giver} gave to forbidden {matches[giver]}"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_minimum_participants_no_constraints(self):
        """Test with exactly 2 participants (minimum valid case)."""
        participants = [0, 1]
        matches = generate_secret_santa_matches(participants)

        # With 2 people, only valid matching is 0→1 and 1→0
        assert matches[0] == 1
        assert matches[1] == 0

    def test_minimum_participants_with_impossible_constraint(self):
        """Test that 2 participants with blocking constraint raises error."""
        participants = [0, 1]
        constraints = {0: [1]}  # If 0 can't give to 1, impossible with n=2

        with pytest.raises(ValueError, match="Could not find a valid gift assignment"):
            generate_secret_santa_matches(participants, constraints)

    def test_single_participant_raises_error(self):
        """Test that single participant raises ValueError."""
        participants = [0]

        with pytest.raises(ValueError, match="Need at least 2 participants"):
            generate_secret_santa_matches(participants)

    def test_zero_participants_raises_error(self):
        """Test that zero participants raises ValueError."""
        participants = []

        with pytest.raises(ValueError, match="Need at least 2 participants"):
            generate_secret_santa_matches(participants)

    def test_empty_constraints_dict(self):
        """Test that empty constraints dict is handled same as None."""
        participants = list(range(4))

        matches_with_none = generate_secret_santa_matches(participants, None)
        matches_with_empty = generate_secret_santa_matches(participants, {})

        # Both should produce valid matches
        assert len(matches_with_none) == 4
        assert len(matches_with_empty) == 4

    def test_large_group_no_constraints(self):
        """Test with large group (50 participants)."""
        participants = list(range(50))

        matches = generate_secret_santa_matches(participants)

        # Verify basic properties
        assert len(matches) == 50
        assert set(matches.keys()) == set(participants)
        assert set(matches.values()) == set(participants)

        # Verify no self-matches
        for giver, receiver in matches.items():
            assert giver != receiver

    def test_large_group_with_constraints(self):
        """Test with large group and multiple constraints."""
        participants = list(range(30))
        constraints = {
            i: [i + 1] if i < 29 else [0]  # Each person can't give to next
            for i in range(30)
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Verify constraints
        for giver, forbidden in constraints.items():
            assert matches[giver] not in forbidden


class TestConstraintPatterns:
    """Tests for specific constraint patterns."""

    def test_unidirectional_chain_constraint(self):
        """Test chain of constraints A→B, B→C, C→D all blocked."""
        participants = list(range(5))
        constraints = {
            0: [1],  # 0 cannot give to 1
            1: [2],  # 1 cannot give to 2
            2: [3],  # 2 cannot give to 3
            3: [4]   # 3 cannot give to 4
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Verify chain is broken
        assert matches[0] != 1
        assert matches[1] != 2
        assert matches[2] != 3
        assert matches[3] != 4

    def test_bidirectional_constraints(self):
        """Test bidirectional constraints (A→B and B→A both blocked)."""
        participants = list(range(4))
        constraints = {
            0: [1],  # 0 cannot give to 1
            1: [0]   # 1 cannot give to 0
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Verify bidirectional blocking
        assert matches[0] != 1
        assert matches[1] != 0

    def test_complex_overlapping_constraints(self):
        """Test overlapping constraint patterns."""
        participants = list(range(6))
        constraints = {
            0: [1, 2],    # 0 blocked from 1, 2
            1: [0, 3],    # 1 blocked from 0, 3
            2: [1, 4],    # 2 blocked from 1, 4
            3: [2, 5],    # 3 blocked from 2, 5
            4: [3, 0]     # 4 blocked from 3, 0
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Verify all constraints
        for giver, forbidden_list in constraints.items():
            assert matches[giver] not in forbidden_list

    def test_high_constraint_density(self):
        """Test with many constraints but still solvable."""
        participants = list(range(8))

        # Block many pairs but leave solution space
        constraints = {
            0: [1, 2, 3],
            1: [2, 3, 4],
            2: [3, 4, 5],
            3: [4, 5, 6],
            4: [5, 6, 7],
            5: [6, 7, 0],
            6: [7, 0, 1],
            7: [0, 1, 2]
        }

        matches = generate_secret_santa_matches(participants, constraints)

        # Should still find a valid solution
        assert len(matches) == 8

        # Verify constraints
        for giver, forbidden_list in constraints.items():
            assert matches[giver] not in forbidden_list

    def test_impossible_constraints_circular(self):
        """Test that impossible circular constraints raise error."""
        participants = list(range(3))

        # With 3 people, if 0→1 and 0→2 blocked, 0 must give to self (impossible)
        constraints = {
            0: [1, 2]
        }

        with pytest.raises(ValueError, match="Could not find a valid gift assignment"):
            generate_secret_santa_matches(participants, constraints)

    def test_impossible_constraints_fully_connected(self):
        """Test that too many constraints make matching impossible."""
        participants = list(range(4))

        # Block all valid non-self assignments for participant 0
        constraints = {
            0: [1, 2, 3]  # 0 can only give to self (invalid)
        }

        with pytest.raises(ValueError, match="Could not find a valid gift assignment"):
            generate_secret_santa_matches(participants, constraints)


class TestRandomness:
    """Tests for randomness and fairness of algorithm."""

    def test_produces_different_results_over_multiple_runs(self):
        """Verify algorithm can produce different valid matchings."""
        participants = list(range(6))

        # Run algorithm many times
        results = set()
        for _ in range(100):
            matches = generate_secret_santa_matches(participants)
            # Convert to sorted tuple for hashing
            result_tuple = tuple(sorted(matches.items()))
            results.add(result_tuple)

        # With 6 participants and 100 runs, we should see multiple different
        # valid matchings (though exact number depends on randomness)
        # At minimum, we should see more than 1 unique result
        assert len(results) > 1, "Algorithm appears deterministic (no variation observed)"

        # Verify all results are valid (length check)
        for result in results:
            assert len(result) == len(participants)

    def test_randomness_with_constraints(self):
        """Verify randomness even with constraints."""
        participants = list(range(5))
        constraints = {
            0: [1],
            2: [3]
        }

        results = set()
        for _ in range(50):
            matches = generate_secret_santa_matches(participants, constraints)
            result_tuple = tuple(sorted(matches.items()))
            results.add(result_tuple)

        # Should still see variation
        assert len(results) > 1, "No variation with constraints"


class TestErrorMessages:
    """Tests for error message quality."""

    def test_too_few_participants_error_message(self):
        """Verify clear error message for too few participants."""
        with pytest.raises(ValueError, match="Need at least 2 participants"):
            generate_secret_santa_matches([0])

    def test_impossible_constraints_error_message(self):
        """Verify error message mentions constraints for impossible case."""
        participants = [0, 1, 2]
        constraints = {0: [1, 2]}

        with pytest.raises(ValueError) as exc_info:
            generate_secret_santa_matches(participants, constraints)

        error_message = str(exc_info.value)
        assert "Could not find a valid gift assignment" in error_message
        assert "constraints" in error_message.lower()

"""Pure-math geometry helpers for the grid (single concern, no side effects).

These functions are deliberately stateless and dependency-light so they can be
unit-tested in isolation and reused by the strategy, rules, and Tier-1 trap
detection without importing heavier domain objects.
"""

from __future__ import annotations

from cop_thief.domain.constants import Direction

Coord = tuple[int, int]
Shape = tuple[int, int]


def calculate_manhattan(p1: Coord, p2: Coord) -> int:
    """Return the Manhattan (L1) distance between two coordinates.

    Used as the partial-observability vision metric and a heuristic distance.
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def random_start_positions(rows: int, cols: int, rng) -> tuple[Coord, Coord]:
    """Return two distinct random cells ``(cop, thief)`` for a fresh sub-game (ex06 §4.2).

    ``rng`` is a ``random.Random`` instance; seeding it deterministically lets both
    groups reproduce the identical opening (so the agreed result cannot drift).
    """
    cop = (rng.randrange(rows), rng.randrange(cols))
    thief = cop
    while thief == cop:
        thief = (rng.randrange(rows), rng.randrange(cols))
    return cop, thief


def get_adjacent_coords(pos: Coord, grid_shape: Shape) -> list[Coord]:
    """Return the in-bounds 8-way neighbours of ``pos`` (STAY excluded)."""
    rows, cols = grid_shape
    row, col = pos
    neighbours: list[Coord] = []
    for direction in Direction:
        if direction is Direction.STAY:
            continue
        new_row, new_col = row + direction.value[0], col + direction.value[1]
        if 0 <= new_row < rows and 0 <= new_col < cols:
            neighbours.append((new_row, new_col))
    return neighbours


def is_conway_trap_inevitable(
    cop_pos: Coord,
    thief_pos: Coord,
    barriers: set[Coord],
    grid_shape: Shape,
) -> bool:
    """Fast deterministic Tier-1 look-ahead for an inevitable capture.

    Returns ``True`` iff the Cop is within Manhattan distance 2 of the Thief and
    every one of the Thief's 8-way escape vectors is occluded by a board
    boundary, an active barrier, or the Cop's own cell — i.e. the Thief has no
    legal cell to flee to.

    Why: lets the Cop recognise a guaranteed win without a full tree search,
    and lets the Thief recognise it must avoid such configurations.
    """
    if calculate_manhattan(cop_pos, thief_pos) > 2:
        return False
    escapes = [
        cell
        for cell in get_adjacent_coords(thief_pos, grid_shape)
        if cell not in barriers and cell != cop_pos
    ]
    return len(escapes) == 0

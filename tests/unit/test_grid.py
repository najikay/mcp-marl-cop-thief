"""Unit tests for Cell and Grid geometry."""

from __future__ import annotations

import pytest

from cop_thief.constants import Direction
from cop_thief.domain.grid import Cell, Grid


def test_in_bounds():
    grid = Grid(5, 5)
    assert grid.in_bounds(Cell(0, 0))
    assert grid.in_bounds(Cell(4, 4))
    assert not grid.in_bounds(Cell(5, 0))
    assert not grid.in_bounds(Cell(-1, 2))


def test_cell_step():
    assert Cell(2, 2).step(Direction.NE) == Cell(1, 3)
    assert Cell(2, 2).step(Direction.STAY) == Cell(2, 2)


def test_center_has_eight_neighbors():
    assert len(Grid(5, 5).neighbors(Cell(2, 2))) == 8


def test_corner_has_three_neighbors():
    assert len(Grid(5, 5).neighbors(Cell(0, 0))) == 3


def test_orthogonal_only_neighbors():
    assert len(Grid(5, 5).neighbors(Cell(2, 2), include_diagonal=False)) == 4


def test_non_positive_dimensions_rejected():
    with pytest.raises(ValueError):
        Grid(0, 3)


def test_non_square_grid_cells_count():
    assert len(Grid(3, 2).cells()) == 6

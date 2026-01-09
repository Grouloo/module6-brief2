import pytest
from modules.calcul import calcul


def test_two_squared_is_four():
    assert calcul(2) == 4

def test_three_squared_is_nine():
    assert calcul(3) == 9

def test_the_square_of_a_negative_is_always_positive():
    assert calcul(-1) == 1
from utils.math_utils import sieve_of_eratosthenes


def test_sieve_returns_known_primes_up_to_30() -> None:
    assert sieve_of_eratosthenes(30) == {2, 3, 5, 7, 11, 13, 17, 19, 23, 29}


def test_sieve_below_2_returns_empty_set() -> None:
    assert sieve_of_eratosthenes(1) == set()
    assert sieve_of_eratosthenes(0) == set()
    assert sieve_of_eratosthenes(-5) == set()


def test_sieve_excludes_one() -> None:
    assert 1 not in sieve_of_eratosthenes(10)


def test_sieve_single_value_range() -> None:
    assert sieve_of_eratosthenes(2) == {2}

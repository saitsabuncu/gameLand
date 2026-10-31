def sieve_of_eratosthenes(limit: int) -> set[int]:
    """Returns the set of prime numbers in the inclusive range [2, limit]."""
    if limit < 2:
        return set()

    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False

    for candidate in range(2, int(limit**0.5) + 1):
        if is_prime[candidate]:
            for multiple in range(candidate * candidate, limit + 1, candidate):
                is_prime[multiple] = False

    return {number for number, prime in enumerate(is_prime) if prime}

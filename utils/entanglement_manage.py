import random
def measure_bell_pair_event_model(basis_a, basis_b, error_rate=0.0):
    """
    Scalable model: Simulate Bell state measurement correlations without matrices.

    Args:
        basis_a (str): 'Z' or 'X' for Alice
        basis_b (str): 'Z' or 'X' for Bob
        error_rate (float): Probability of flipping each bit

    Returns:
        (bit_a, bit_b): Measurement outcomes
    """
    if basis_a == basis_b:
        # Perfect correlation: both get same random bit
        bit = random.choice([0, 1])
        bit_a, bit_b = bit, bit
    else:
        # Mismatched bases: independent random bits
        bit_a, bit_b = random.choice([0,1]), random.choice([0,1])

    # Apply errors (simulating QBER or decoherence)
    if random.random() < error_rate:
        bit_a = 1 - bit_a
    if random.random() < error_rate:
        bit_b = 1 - bit_b

    return bit_a, bit_b
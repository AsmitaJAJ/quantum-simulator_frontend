from entanglement_manage import measure_bell_pair_event_model
import random
num_trials = 10000
error_rate = 0.02  # Simulated QBER (2%)

# Count outcomes for each basis choice
results = {
    ('Z', 'Z'): [],
    ('X', 'X'): [],
    ('Z', 'X'): [],
    ('X', 'Z'): []
}

for _ in range(num_trials):
    # Randomly select bases for Alice and Bob
    basis_a = random.choice(['Z', 'X'])
    basis_b = random.choice(['Z', 'X'])

    bit_a, bit_b = measure_bell_pair_event_model(basis_a, basis_b, error_rate=error_rate)

    results[(basis_a, basis_b)].append((bit_a, bit_b))

# Compute and display stats
for bases, outcomes in results.items():
    total = len(outcomes)
    if total == 0:
        continue

    same = sum(1 for a, b in outcomes if a == b)
    diff = total - same
    qber = diff / total if total else None

    print(f"Basis {bases[0]}-{bases[1]}: {total} rounds")
    print(f"   Correlated: {same} times ({same / total:.2%})")
    print(f"   QBER: {qber:.2%}\n")
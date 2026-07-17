import numpy as np


def hill_4pl(x, E0, Emax, EC50, h):
    return E0 + (Emax - E0) / (1 + (x / EC50) ** (-h))


def generate_concentration_series(ic50, n=6, dilution=2):
    half = n // 2
    return np.array([ic50 * dilution ** (i - half) for i in range(n)])


def generate_checkerboard(
    d1_conc, d2_conc,
    hill_a=(0.0, 0.95, 3.0, 1.2),
    hill_b=(0.0, 0.90, 10.0, 0.9),
    synergy_magnitude=0.0,
    noise_std=0.0,
    seed=42
):
    rng = np.random.RandomState(seed)
    D1, D2 = np.meshgrid(d1_conc, d2_conc)
    d1 = D1.ravel()
    d2 = D2.ravel()
    e1 = hill_4pl(d1, *hill_a)
    e2 = hill_4pl(d2, *hill_b)
    log_c1 = np.log(np.array(d1_conc, dtype=float))
    log_c2 = np.log(np.array(d2_conc, dtype=float))
    center = (log_c1[len(log_c1)//2] + log_c2[len(log_c2)//2]) / 2
    sigma = (log_c1[-1] - log_c1[0]) / 4
    log_d1 = np.log(np.maximum(d1, 1e-10))
    log_d2 = np.log(np.maximum(d2, 1e-10))
    synergy = synergy_magnitude * np.exp(
        -((log_d1 - center)**2 + (log_d2 - center)**2) / (2 * sigma**2)
    )
    E = np.clip(e1 + e2 + synergy, 0, 1)
    if noise_std > 0:
        E += rng.normal(0, noise_std, size=E.shape)
        E = np.clip(E, 0, 1)
    return d1, d2, E


DEMO_CONFIG = {
    "strong":       {"synergy_magnitude": 0.25, "noise_std": 0.0},
    "moderate":     {"synergy_magnitude": 0.10, "noise_std": 0.0},
    "additive":     {"synergy_magnitude": 0.00, "noise_std": 0.0},
    "antagonistic": {"synergy_magnitude": -0.20, "noise_std": 0.0},
    "noisy":        {"synergy_magnitude": 0.10, "noise_std": 0.03},
}

DEMO_MODES = list(DEMO_CONFIG.keys())


def generate_demo(mode, conc_a, conc_b, seed=42):
    config = DEMO_CONFIG[mode]
    d1, d2, E = generate_checkerboard(
        conc_a, conc_b,
        synergy_magnitude=config["synergy_magnitude"],
        noise_std=config["noise_std"],
        seed=seed,
    )
    return d1, d2, E

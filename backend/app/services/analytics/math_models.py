import numpy as np
from scipy.optimize import curve_fit


def hill_4pl(x, E0, Emax, EC50, h):
    return E0 + (Emax - E0) / (1 + (x / EC50) ** (-h))


def fit_4pl(d, E):
    d = np.asarray(d, dtype=float)
    E = np.asarray(E, dtype=float)
    sort_idx = np.argsort(d)
    d_sorted = d[sort_idx]
    E_sorted = E[sort_idx]

    E0_guess = min(E_sorted)
    Emax_guess = max(E_sorted)
    mid_idx = len(d_sorted) // 2
    EC50_guess = d_sorted[mid_idx] if len(d_sorted) > 2 else np.median(d_sorted)
    h_guess = 1.0

    p0 = [E0_guess, Emax_guess, EC50_guess, h_guess]
    lower = [E0_guess - 0.5, Emax_guess - 0.5, 0.001, 0.1]
    upper = [E0_guess + 0.5, Emax_guess + 0.5, 1e6, 10.0]

    try:
        popt, pcov = curve_fit(
            hill_4pl, d_sorted, E_sorted, p0=p0,
            bounds=(lower, upper), maxfev=5000
        )
        residuals = E_sorted - hill_4pl(d_sorted, *popt)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((E_sorted - np.mean(E_sorted)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        return {
            "E0": popt[0], "Emax": popt[1], "EC50": popt[2], "h": popt[3],
            "r_squared": r_squared, "converged": True,
            "d": d_sorted, "E": E_sorted,
        }
    except Exception:
        return {
            "E0": E0_guess, "Emax": Emax_guess,
            "EC50": EC50_guess, "h": h_guess,
            "r_squared": 0, "converged": False,
            "d": d_sorted, "E": E_sorted,
        }


def hill_E_inv(e, E0, Emax, EC50, h):
    inv = np.full_like(e, np.nan, dtype=float)
    mask = (e > E0) & (e < Emax)
    if np.any(mask):
        inv[mask] = EC50 * ((Emax - E0) / (e[mask] - E0) - 1) ** (-1 / h)
    return inv


def synergy_bliss_reference(e1, e2):
    return e1 + e2 - e1 * e2


def synergy_hsa_reference(e1, e2):
    return np.maximum(e1, e2)


def synergy_loewe_reference(d1, d2, params1, params2):
    E0_1, Emax_1, EC50_1, h_1 = params1["E0"], params1["Emax"], params1["EC50"], params1["h"]
    E0_2, Emax_2, EC50_2, h_2 = params2["E0"], params2["Emax"], params2["EC50"], params2["h"]
    lo = max(E0_1, E0_2)
    hi = min(Emax_1, Emax_2)
    E_ref = np.full_like(d1, np.nan, dtype=float)
    if lo >= hi:
        return E_ref
    for i in range(len(d1)):
        a, b = lo, hi
        for _ in range(100):
            mid = (a + b) / 2
            D1_mid = hill_E_inv(np.array([mid]), E0_1, Emax_1, EC50_1, h_1)[0]
            D2_mid = hill_E_inv(np.array([mid]), E0_2, Emax_2, EC50_2, h_2)[0]
            if not np.isfinite(D1_mid) or not np.isfinite(D2_mid):
                break
            val = d1[i] / D1_mid + d2[i] / D2_mid - 1
            if val > 0:
                a = mid
            else:
                b = mid
            if b - a < 1e-10:
                break
        E_ref[i] = (a + b) / 2
    return E_ref


def synergy_zip_reference(d, params):
    return hill_4pl(d, params["E0"], params["Emax"], params["EC50"], params["h"])


def compute_all_synergy(d1, d2, E):
    d1 = np.asarray(d1, dtype=float)
    d2 = np.asarray(d2, dtype=float)
    E = np.asarray(E, dtype=float)

    d1_u = np.sort(np.unique(d1))
    d2_u = np.sort(np.unique(d2))

    d2_min = d2_u.min()
    d1_min = d1_u.min()

    mask_a = np.isclose(d2, d2_min)
    mask_b = np.isclose(d1, d1_min)

    params_a = fit_4pl(d1[mask_a], E[mask_a])
    params_b = fit_4pl(d2[mask_b], E[mask_b])

    e1_mono = hill_4pl(d1, params_a["E0"], params_a["Emax"], params_a["EC50"], params_a["h"])
    e2_mono = hill_4pl(d2, params_b["E0"], params_b["Emax"], params_b["EC50"], params_b["h"])

    E_ref_bliss = synergy_bliss_reference(e1_mono, e2_mono)
    E_ref_hsa = synergy_hsa_reference(e1_mono, e2_mono)
    E_ref_loewe = synergy_loewe_reference(d1, d2, params_a, params_b)
    E_ref_zip = synergy_zip_reference(d1, params_a) + synergy_zip_reference(d2, params_b) \
                - synergy_zip_reference(d1, params_a) * synergy_zip_reference(d2, params_b)
    E_ref_zip = np.clip(E_ref_zip, 0, 1)

    results = {
        "params_a": params_a,
        "params_b": params_b,
        "d1_unique": d1_u,
        "d2_unique": d2_u,
        "observed": E,
        "bliss": {"reference": E_ref_bliss, "synergy": E - E_ref_bliss},
        "hsa": {"reference": E_ref_hsa, "synergy": E - E_ref_hsa},
        "loewe": {"reference": E_ref_loewe, "synergy": E - E_ref_loewe},
        "zip": {"reference": E_ref_zip, "synergy": E - E_ref_zip},
    }
    for m in results:
        if isinstance(results.get(m), dict) and "synergy" in results.get(m, {}):
            results[m]["mean"] = float(np.nanmean(results[m]["synergy"]))
            results[m]["max"] = float(np.nanmax(results[m]["synergy"]))
            results[m]["min"] = float(np.nanmin(results[m]["synergy"]))
            syn_area = np.nanmean(results[m]["synergy"] > 0.01) * 100
            ant_area = np.nanmean(results[m]["synergy"] < -0.01) * 100
            results[m]["synergistic_area_pct"] = float(syn_area)
            results[m]["antagonistic_area_pct"] = float(ant_area)

    return results


def summarize(results):
    model = results.get("zip")
    if model is None:
        return ""
    lines = [
        f"Model: ZIP (default)",
        f"  Mean synergy score:     {model['mean']:.4f}",
        f"  Max synergy score:      {model['max']:.4f}",
        f"  Min synergy score:      {model['min']:.4f}",
        f"  Synergistic area:       {model['synergistic_area_pct']:.1f}%",
        f"  Antagonistic area:      {model['antagonistic_area_pct']:.1f}%",
    ]
    for m in ["bliss", "hsa", "loewe"]:
        if m in results:
            lines.append(f"  {m.capitalize()} mean:        {results[m]['mean']:.4f}")
    return "\n".join(lines)

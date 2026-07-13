import math

Z_SCORES = {
    90: 1.645,
    95: 1.96,
    99: 2.576,
}

def calculate_sample_size(confidence: int, p: float, e: float, N: int = None) -> dict:
    if confidence not in Z_SCORES:
        raise ValueError(f"Nivel de confianza no válido: {confidence}%. Use 90, 95 o 99.")

    if not (0 < p < 1):
        raise ValueError("La probabilidad de éxito (p) debe estar entre 0 y 1, exclusivo.")

    if not (0 < e < 1):
        raise ValueError("El error admisible (e) debe estar entre 0 y 1, exclusivo.")

    Z = Z_SCORES[confidence]
    q = 1 - p

    n0 = (Z ** 2 * p * q) / (e ** 2)
    n0 = math.ceil(n0)

    result = {
        "Z": Z,
        "confidence": confidence,
        "p": p,
        "q": q,
        "e": e,
        "n_unknown": n0,
        "n0": None,
        "nf": None,
        "N": None,
    }

    if N is not None:
        if N <= 0:
            raise ValueError("El tamaño de la población (N) debe ser un entero positivo.")

        result["N"] = N
        result["n0"] = n0
        nf = n0 / (1 + n0 / N)
        nf = math.ceil(nf)
        result["nf"] = nf

    return result

"""Clasificador supervisado de intenciones de presupuesto en español."""
from collections import Counter
from math import log
import re


EXAMPLES = {
    "budget_create": (
        "crea un presupuesto", "registra un presupuesto", "quiero crear un presupuesto",
        "pon un limite mensual", "fija un limite mensual", "establece un tope",
        "asigna un presupuesto mensual", "define un presupuesto", "arma un presupuesto",
        "agrega un presupuesto", "guardar presupuesto", "quiero un presupuesto",
        "presupuesto mensual de monto para categoria",
    ),
    "budget_list": (
        "muestra mis presupuestos", "cuales son mis presupuestos", "ver presupuestos",
        "lista mis presupuestos", "consulta el presupuesto", "cuanto me queda de presupuesto",
        "como va mi presupuesto", "que presupuestos tengo", "dame mis presupuestos",
    ),
}


def features(text: str) -> list[str]:
    words = re.findall(r"[a-z]+", text)
    return words + [f"{a} {b}" for a, b in zip(words, words[1:])]


COUNTS = {
    label: Counter(feature for phrase in phrases for feature in features(phrase))
    for label, phrases in EXAMPLES.items()
}
VOCABULARY = set().union(*(counts.keys() for counts in COUNTS.values()))
TOTALS = {label: sum(counts.values()) + len(VOCABULARY) for label, counts in COUNTS.items()}


def classify_budget(text: str) -> str | None:
    if not re.search(r"\b(presupuestos?|limite mensual|tope mensual)\b", text):
        return None
    if re.search(r"\b(no|nunca|cancela\w*|borra\w*|elimina\w*|edit\w*|actualiz\w*|cambia\w*|modifi\w*)\b", text):
        return "budget_help"
    tokens = set(features(text)) & VOCABULARY
    scores = {
        label: sum(log((counts[token] + 1) / TOTALS[label]) for token in sorted(tokens))
        for label, counts in COUNTS.items()
    }
    winner = max(scores, key=scores.get)
    # Las consultas y las solicitudes dudosas nunca crean registros.
    if re.search(r"\b(cuanto|cual(?:es)?|que es|que tengo|como va|muestra\w*|consult\w*|list\w*|ver)\b", text):
        return "budget_list"
    if re.search(r"\b(cre\w*|registr\w*|pon\w*|fij\w*|establec\w*|asign\w*|defin\w*|arm\w*|agreg\w*|guard\w*|quiero)\b", text) and winner == "budget_create":
        return winner
    return "budget_help"

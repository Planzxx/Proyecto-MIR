"""Utilidades de texto: normalización para búsqueda y mayúsculas legibles."""
import re
import unicodedata

ACRONIMOS = {"UDM", "AFYC", "UD", "EOXI", "C.H.", "H.", "CHU", "ICS", "I.C.S.",
             "II", "III", "IV", "VI", "UCI", "SAS", "AGS", "HM"}
PEQUENAS = {"de", "del", "la", "las", "los", "el", "y", "i", "en", "da", "do",
            "dels", "les", "al", "d´", "l´"}
_ANTES_DE_LA = re.compile(r"^(H\.|C\.H\.|Universitario|Universitari|Clínico|General|Hospital)$", re.I)
_PUNTO_PEGADO = re.compile(r"\b(H|C\.H)\.(?=[A-ZÁÉÍÓÚ])")
_INICIAL = re.compile(r"(^|[-/(´'])([a-záéíóúüñçàèòï])")


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para buscar sin distinguir acentos."""
    d = unicodedata.normalize("NFD", texto)
    return "".join(c for c in d if not unicodedata.combining(c)).lower()


def titulo(texto: str) -> str:
    """Convierte «H. UNIVERSITARIO LA PAZ» en «H. Universitario La Paz»."""
    texto = _PUNTO_PEGADO.sub(r"\1. ", texto)
    palabras = texto.split(" ")
    salida = []
    for i, w in enumerate(palabras):
        if w in ACRONIMOS:
            salida.append(w)
            continue
        lw = w.lower()
        if i > 0 and lw in PEQUENAS and not (lw == "la" and _ANTES_DE_LA.match(palabras[i - 1])):
            salida.append(lw)
            continue
        salida.append(_INICIAL.sub(lambda m: m.group(1) + m.group(2).upper(), lw))
    return " ".join(salida)


def miles(n: int) -> str:
    """12345 -> «12.345» (formato español)."""
    return f"{n:,}".replace(",", ".")

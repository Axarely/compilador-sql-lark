"""Compilador del pseudolenguaje a PostgreSQL usando Lark.

Uso:
    python compilador.py archivo.msql
    python compilador.py examples      (compila todos los .msql de la carpeta)

Por cada archivo .msql se genera un .sql con el mismo nombre.
"""
import sys
from pathlib import Path

from lark import Lark, Transformer
from lark.exceptions import LarkError

# Tabla de tipos de la especificación (sección 3)
TIPOS = {
    "id": "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY",
    "num": "NUMERIC",
    "text": "TEXT",
    "bool": "BOOLEAN DEFAULT FALSE",
    "time": "TIMESTAMPTZ DEFAULT NOW()",
}


class TraductorSQL(Transformer):
    """Recorre el árbol desde las hojas y convierte cada regla en texto SQL."""

    # ---------- valores y condiciones ----------
    def value(self, hijos):
        token = hijos[0]
        if token.type == "DOUBLE_STRING":
            # En PostgreSQL las comillas dobles son para nombres, no para texto
            return "'" + token[1:-1].replace("'", "''") + "'"
        if token.type == "BOOL":
            return token.upper()
        return str(token)

    def comparison(self, hijos):
        campo, operador, valor = hijos
        return f"{campo} {operador} {valor}"

    def and_join(self, hijos):
        return f"{hijos[0]} AND {hijos[1]}"

    def or_cond(self, hijos):
        return f"{hijos[0]} OR {hijos[1]}"

    def where(self, hijos):
        return f"WHERE {hijos[0]}"

    # ---------- MAKE ----------
    def column(self, hijos):
        nombre, tipo = hijos[0], hijos[1].lower()
        if tipo not in TIPOS:
            raise ValueError(f"tipo desconocido '{hijos[1]}' en la columna '{nombre}'")
        sql = f"{nombre} {TIPOS[tipo]}"
        if len(hijos) == 3:  # trae el signo "!"
            sql += " NOT NULL"
        return sql

    def make(self, hijos):
        tabla, columnas = hijos[0], hijos[1:]
        cuerpo = ",\n".join("    " + c for c in columnas)
        return f"CREATE TABLE {tabla} (\n{cuerpo}\n);"

    # ---------- GET ----------
    def fields(self, hijos):
        if hijos[0].type == "ALL":
            return "*"
        return ", ".join(hijos)

    def sort(self, hijos):
        orden = f"ORDER BY {hijos[0]}"
        if len(hijos) == 2:
            orden += " " + hijos[1].upper()
        return orden

    def top(self, hijos):
        return f"LIMIT {hijos[0]}"

    def get(self, hijos):
        campos, tabla, extras = hijos[0], hijos[1], hijos[2:]
        lineas = [f"SELECT {campos}", f"FROM {tabla}"] + extras
        return "\n".join(lineas) + ";"

    # ---------- PUT ----------
    def assignment(self, hijos):
        return (str(hijos[0]), hijos[1])

    def put(self, hijos):
        tabla = hijos[0]
        asignaciones = [h for h in hijos[1:] if isinstance(h, tuple)]
        where = [h for h in hijos[1:] if isinstance(h, str)]

        if where:  # con WHERE es UPDATE
            sets = ", ".join(f"{campo} = {valor}" for campo, valor in asignaciones)
            return f"UPDATE {tabla}\nSET {sets}\n{where[0]};"

        # sin WHERE es INSERT
        campos = ", ".join(c for c, _ in asignaciones)
        valores = ", ".join(v for _, v in asignaciones)
        return f"INSERT INTO {tabla} ({campos})\nVALUES ({valores});"

    # ---------- DROP ----------
    def drop(self, hijos):
        tabla = hijos[0]
        if len(hijos) == 2:  # con WHERE borra filas
            return f"DELETE FROM {tabla} {hijos[1]};"
        return f"DROP TABLE {tabla};"


gramatica = (Path(__file__).parent / "msql.lark").read_text(encoding="utf-8")
parser = Lark(gramatica, parser="lalr")


def compilar(codigo):
    """Compila el texto completo de un archivo. Cada línea es una instrucción."""
    resultado = []
    for numero, linea in enumerate(codigo.splitlines(), start=1):
        if not linea.strip():
            continue
        try:
            arbol = parser.parse(linea.strip())
            resultado.append(TraductorSQL().transform(arbol))
        except (LarkError, ValueError) as error:
            # VisitError guarda el error original del Transformer
            causa = getattr(error, "orig_exc", error)
            raise SystemExit(f"Error en la línea {numero}: {causa}")
    return "\n\n".join(resultado) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python compilador.py archivo.msql | carpeta")
        sys.exit(1)

    # Se acepta un archivo o una carpeta (en ese caso se toman todos sus .msql)
    archivos = []
    for ruta in sys.argv[1:]:
        ruta = Path(ruta)
        archivos += sorted(ruta.glob("*.msql")) if ruta.is_dir() else [ruta]

    for entrada in archivos:
        salida = entrada.with_suffix(".sql")
        salida.write_text(compilar(entrada.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"{entrada.name} -> {salida.name}")

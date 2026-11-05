# Compilador de pseudolenguaje a PostgreSQL con Lark

## Archivos

- `msql.lark` tiene la gramática del lenguaje (MAKE, GET, PUT, DROP).
- `compilador.py` lee cada línea, la analiza con Lark y traduce el árbol a SQL con un `Transformer`.
- `examples/` tiene los ejemplos `.msql`. Al correr el compilador se crea un `.sql` por cada uno.

## Cómo correrlo

```
pip install lark
python compilador.py examples
```

También se puede compilar un solo archivo, por ejemplo `python compilador.py examples/schema.msql`.

Por cada archivo `.msql` se crea un `.sql` con el mismo nombre en la misma carpeta.
Si una línea tiene un error, el compilador dice en qué línea está y se detiene.

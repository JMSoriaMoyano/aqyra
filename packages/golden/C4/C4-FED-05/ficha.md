# Golden C4-FED-05 — política `mantener-separada` (D22, tarea 1.4)

> Ancla el SEGUNDO valor de `deduplicacion.estructura_espacial` — un camino entero del
> contrato que no tenía oráculo. **Hallazgo 1.4:** el service 0.3.0 ACEPTABA la política
> y la ecoaba en el manifiesto (`"mantenida-separada"`) SIN aplicarla (los nodos se
> unificaban por nombre igualmente). Se implementó en 0.4.0 (este hilo) y se ancla aquí.

## Entradas (congeladas — las limpias de C4-FED-01, byte a byte)

- `entrada/ARQ.ifc` — md5 `653a359154112146d82ca02de0fde2ee`. Modelo `ARQ`, S1.
- `entrada/EST.ifc` — md5 `b84cb79c4a7cf4b560148340bc8dc305`. Modelo `EST`, S1.

## Oráculo (verificado a mano antes de anclar)

- Manifiesto: política `mantenida-separada`; **9 agregados** = Project ÚNICO (por
  definición, aportado por ambos) + 2 Site + 2 Building + 4 Storey — `"Emplazamiento"`
  y `"Edificio"` aparecen DOS VECES, una por modelo, con `aportado_por` UNITARIO:
  nada se funde. (Con `unificar-por-nombre`, las mismas entradas dan 7 — caso 01.)
- Informe: idéntico al del 01 por modelo (mismos ficheros, mismo pack IDS): la política
  de estructura espacial NO altera la validación IDS. Sin emisión (`emitido=false` —
  la emisión ya la ancla el 04; D8).
- El detalle de unidad (nodos por modelo, política desconocida rechazada, min(S)) va
  además en pytest: `tests/test_federacion.py` (bloque "mantener-separada (D22, 1.4)").

## Regla de oro

Un fallo NO se arregla aflojando esta golden. Cambiar la política del caso es cambiar
su DISEÑO (dejaría el camino sin oráculo otra vez) y pasa por decisión explícita con JM.

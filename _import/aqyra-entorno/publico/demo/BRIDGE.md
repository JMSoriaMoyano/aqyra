# Puente Aqyra (bridge A) — diálogo en el visor, Claude de cerebro

El skin Diseño (`/diseno.html`) conversa con **Claude** (en la sesión de Cowork) a
través de **ficheros**, servidos por endpoints del servidor de desarrollo
(plugin `aqyra-bridge` en `vite.config.ts`).

## Flujo

```
visor  --POST /__aqyra/say {text}-->  .aqyra/inbox.jsonl   (lo LEE Claude)
Claude --escribe-->                   .aqyra/outbox.json    (lo SONDEA el visor)
visor  --GET /__aqyra/outbox (1,5 s)--> última respuesta + acciones
```

- `inbox.jsonl`: una línea JSON por mensaje del usuario: `{ "id", "ts", "text" }`.
- `outbox.json`: la última respuesta de Claude. El visor solo la pinta si `seq` crece.

## Formato de `outbox.json` (lo escribe Claude)

```json
{
  "seq": 1,
  "replyTo": "<id del mensaje>",
  "reply": "texto del copiloto que se muestra en el chat",
  "actions": [
    { "type": "summary", "key": "project",  "value": "Can Cabassa" },
    { "type": "summary", "key": "site",     "value": "Sant Cugat · 0419901DF2901H0001WW" },
    { "type": "summary", "key": "building", "value": "Edificio 2" },
    { "type": "view", "show": "volume" }
  ]
}
```

- `summary.key` ∈ `project | site | building | volume | storeys | spaces | grid`.
- `view.show` ∈ `volume | levels | grid | reset` (maqueta visual; aún no es IFC).
- **Importante:** sube `seq` en cada respuesta nueva (el visor compara contra el último visto).

## Cadencia (naturaleza de Claude)

Claude actúa **por turnos**, no de fondo. En una sesión de trabajo: el usuario
escribe en el visor → el mensaje queda en `inbox.jsonl` → en el hilo de Cowork,
Claude lee el buzón, interpreta, (luego) autora el IFC y escribe `outbox.json` →
el visor lo recoge. Un “sigue” por tanda. El cerebro-en-visor permanente será el
operador IA (LLM), más adelante.

## Probar

1. Arranca el visor: `pnpm --filter @aqyra/demo dev` → `localhost:5173/diseno.html`.
2. Escribe un mensaje (o pulsa la sugerencia).
3. En el hilo de Cowork, Claude lee `.aqyra/inbox.jsonl` y escribe `.aqyra/outbox.json`.
4. El visor pinta la respuesta y ejecuta las acciones (resumen + maqueta).

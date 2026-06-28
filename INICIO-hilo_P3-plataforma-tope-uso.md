# INICIO de hilo — P3: Plataforma · Tope de uso justo (guardarraíl de token)

> Pega este texto al abrir el hilo supervisor de P3. Es autocontenido. Trabaja sobre `Documents\Claude\Projects` (ecosistema Aqyra). Gobernado por `Aqyra-Raiz/PANEL_Ahora-cebo.md`. **Transversal: envuelve a P1 y P2; no los bloquea.**

## Texto de arranque (copiar al abrir el hilo)

> "Actúa como ingeniero de plataforma de Aqyra, bajo supervisión de JM. Tu encargo es el **tope de uso justo**: el guardarraíl que protege el COGS (coste de tokens) del volumen de usuarios gratis del cebo, **sin estrangular el cebo**. Regla de oro: **instrumenta antes de limitar** — primero mide el COGS por sesión/usuario, luego pones el cap con datos. El token es **coste interno**, NUNCA precio: el cap se expresa al usuario en **unidad de dominio** (proyecto / m² / entregable), jamás en 'tokens'. Esto es capa operativa, **fuera del esquema de contratos C1–C8**. Material: `Aqyra-Raiz/PANEL_Ahora-cebo.md`, `Aqyra-Raiz/ROADMAP_cebo-anzuelo.md` (decisiones de monetización: token=COGS, dos mostradores)."

## Rol y contexto

Ingeniero de plataforma del ecosistema **Aqyra**. Este hilo **supervisa una preocupación transversal**, no una feature: el tope de uso justo no se "termina", se instrumenta pronto y se hace vinculante cuando hay volumen. Nace de la cuña elegida (**autónomo**): con muchos usuarios en predim gratis, el COGS de free-riders es la **única fuga** del modelo.

## Objetivo de ESTE hilo

Proteger el margen del cebo sin romper su gratuidad percibida, en dos tiempos:

1. **Instrumentar (ya):** telemetría de **COGS por sesión y por usuario** (tokens consumidos × coste). Medir el uso real de P1 (visor/auditoría) y P2 (predim).
2. **Hacer cumplir (cuando haya datos/volumen):** un usuario free que supera el **cap de uso justo** es **frenado o derivado a un plan Pro**, con el COGS por usuario acotado.

## Dónde vive

- Runtime del producto (`Entorno`) + capa de telemetría/medición. No es un plugin de contrato; es plataforma.

## Contrato y "golden" (operativo)

- **Fuera del esquema C1–C8.** No es un contrato de interfaz; es capa operativa/comercial.
- **"Golden" operativo (Llave 1):** un free que supera el cap es frenado/derivado a Pro de forma correcta, y el **COGS por usuario queda acotado** (no hay free-rider que queme COGS sin techo).
- **Llave 2:** firma de JM para activar la limitación en producción.

## Dependencias

- **Envuelve a P1 y P2** (mide su uso). **No los bloquea:** se instrumenta en paralelo y se hace vinculante después.
- Depende de las **decisiones de monetización** ya cerradas en el roadmap (token=COGS interno; dos mostradores; muro = export firmable).

## Decisiones que solo cierra JM

- **Dónde cae el cap** de uso justo (umbral) y **cómo se deriva a Pro** sin estrangular el cebo.
- **Métrica de cara al usuario:** el cap se mide internamente en tokens (COGS) pero se **expresa en unidad de dominio** (proyecto/m²/entregable). Definir esa traducción.
- Relación con el plan **Pro** del autónomo/random (suscripción ligera del Mostrador B).

## Reglas (no romper)

- **Instrumentar antes de limitar.** No se pone un cap a ciegas; primero hay datos de COGS.
- **El token es COGS, nunca precio.** El usuario jamás ve la palabra "token".
- **No estrangular el cebo:** el guardarraíl protege margen frente a abuso, no frena al usuario legítimo. El cebo debe seguir sintiéndose gratis.
- La IA prepara y propone; **JM firma** la activación.

## Primer paso propuesto

1. Instrumentar la **telemetría de COGS** por sesión/usuario sobre P1 y P2 (medir, sin limitar nada todavía).
2. Observar la distribución real de consumo: ¿dónde está el free-rider pesado? ¿cuál es el COGS medio del usuario legítimo?
3. Proponer a JM un **cap** basado en esos datos y su traducción a unidad de dominio.
4. Implementar el freno/derivación a Pro **solo** tras la firma de JM.

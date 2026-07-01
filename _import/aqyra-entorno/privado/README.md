# privado/ — el ANZUELO (moat · NUNCA publicable)

Todo lo que vive aquí es **foso**: si se filtra, se erosiona la ventaja. **No entra jamás en el repo público.** Es lo que convierte el cebo (visor) en un negocio defendible de ingresos recurrentes.

## Qué va aquí

- **`copiloto-criterio/`** — el **criterio de ingeniero** que el copiloto recupera del corpus golden antes de actuar (la diferencia entre "geometría tonta" y "modelo con criterio"). La *superficie* NL es pública (`../publico/ui-nl/`); el **criterio** es privado.
- **`puente-calculo/`** — adaptador a los **motores de cálculo** del ecosistema (motor-fem / motor-cálculo), consumidos **anclados** (`../integracion/versions.lock`). Trae resultados para que el visor los pinte en post-proceso, **bajo dos llaves**.
- **`puente-corpus/`** — acceso de lectura al **corpus golden** y su recuperación por OIR (capa 7 del Hilo 2). El corpus es propiedad de QA/JM; aquí solo el puente.

## Reglas

- Los resultados que el puente trae se muestran con su **estado** (propuesta / verificado-firmado). El visor **nunca** pinta como válido lo no certificado.
- Cambiar algo del corpus o de las tolerancias exige **PR aprobado por JM** (gobierno).
- La IA opera; **JM firma**. La IA no firma ni certifica.

## Regla de frontera

> Si un competidor lo copia y **no** perdemos ventaja → debería estar en `../publico/`.
> Si al filtrarse **se erosiona el foso** → es privado y se queda aquí.

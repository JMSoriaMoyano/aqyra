# verificacion-ec/ — aprovechamiento EC3 (CRITERIO · ANZUELO · privado · D-022)

El **criterio normativo** (qué se comprueba y cómo según norma) es moat: vive aquí, nunca en el cebo. Cubre el **suelo de V3**: comprobación de **aprovechamiento EC3** (acero) y «**qué no cumple**» a partir de los esfuerzos que devuelve el contrato C5.

## Qué hace (D-022·C.1)

- **`ec3_section_utilization`** — comprobación de **sección** EN 1993-1-1 §6.2 (Anejo Nacional español, γM0=1.05): `Npl,Rd = A·fy/γM0`, `Mc,Rd = Wpl·fy/γM0` (clase 1/2; `Wel` si no hay `Wpl`), interacción **lineal conservadora** §6.2.1(7): `u = |N|/Npl,Rd + |My|/Mcy,Rd + |Mz|/Mcz,Rd`. Devuelve `(u, gobernante, cumple)`.
- **`apply_ec3_checks`** — rellena `utilization`/`governing`/`passes` de cada `MemberResult` (peor estación) y devuelve la lista «**qué no cumple**» (u>1).
- **`critical_members`** — elementos «al límite» (u>0,9) que el visor resalta.
- **`Ec3CheckPort`** — puerto para sustituir la implementación de referencia por la **skill anclada `estructuras-eurocodigos 0.1.0`** (versions.lock) en producción.

## Alcance y frontera

- **Dentro (suelo de V3):** verificación de sección + «qué no cumple». 
- **Fuera (incrementos posteriores de V3 / D-022·C.2):** **armado EC2** (elementos + núcleo por sándwich/columna-cajón) y **pandeo de barra** EC3 §6.3 (necesitan longitudes de pandeo y más criterio). En hormigón, **verificar exige dimensionar**.
- **Dos llaves:** este módulo aporta el aprovechamiento; **no** acuña `verified-signed` (eso es la firma de JM). El visor nunca pinta como certificado lo no firmado (D-021).

## Estado

Implementado y verificado en sandbox (Python puro): interacción N+M, «qué no cumple» y críticos. El cableado a la skill EC anclada y el armado EC2 quedan como incrementos.

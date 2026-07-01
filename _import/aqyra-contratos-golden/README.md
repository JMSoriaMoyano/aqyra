# Estructurando 2.0

Proyecto de **industrialización** del ecosistema de agentes de ingeniería. Ejecuta el backlog de la **Fase 0** (de plugins artesanales a producción certificada) y lanza el **wedge** BIM/cumplimiento, mientras el proyecto **Estructurando** sigue creando plugins artesanales.

> **Modelo dual:** Estructurando = *productor* (publica versiones del núcleo). Estructurando 2.0 = *consumidor* (las usa ancladas) e industrializa. Ver `GOBIERNO_QA_Y_VERSIONES.md`.

## Reparto de roles

- **JM (humano):** Dirección · Negocio/Comercial · Ing. Núcleo FEM. *Responsable y firmante.*
- **IA (ecosistema Claude):** Ing. BIM-IFC · Producto (PM) · QA/Verificación · desarrollo de código. *Opera; JM aprueba.*

## Estructura

```
Estructurando-2.0/
├── README.md                  · este mapa
├── GOBIERNO_QA_Y_VERSIONES.md · reglas de QA independiente y de versiones
├── SPRINT_0.md                · plan de arranque (M1)
├── versions.lock              · versiones del núcleo/plugins que se consumen (pin)
├── contratos-golden/          · zona protegida (QA/JM): contratos C1..C5 y casos golden
├── qa/                        · arnés de QA independiente + informes por cálculo
├── producto-wedge/            · Track B: PRD y producto BIM/cumplimiento
├── pilotos/                   · Decopak HQ + Terres Cavades (internos) · Can Cabassa (externo)
├── metricas/                  · KPIs, baseline de ROI, tablero
└── memoria/                   · criterios de despacho de 2.0 (aprende entre hilos)
```

## Pilotos → tracks

| Piloto | Tipo | Track | Aporta |
|---|---|---|---|
| Decopak HQ | interno | A · uso interno | casos golden + baseline ROI |
| Terres Cavades | interno | A · uso interno | casos golden + baseline ROI |
| Can Cabassa | externo | B · wedge | validación del PRD + LOI |

## Por dónde se empieza

Ver **`SPRINT_0.md`**. El gobierno de calidad y versiones ya está cerrado en `GOBIERNO_QA_Y_VERSIONES.md` (decisiones 1 y 3 ratificadas; decisión 2 abierta, a resolver caso a caso).

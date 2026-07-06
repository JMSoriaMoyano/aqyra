# Delta de spec · Capacidad `visor` — Skins por disciplina (Slice 1)

> Se AÑADEN los requisitos que codifican el re-vestido del visor por disciplina: mapa estático
> disciplina→clases, acento de disciplina, color categórico por clase y leyenda por intersección.
> Alcance Slice 1: disciplinas **Diseño** y **Estructuras**. Superficie `apps/visor` (propone
> puro): no dispara ninguna de las dos llaves; la golden del visor/`core` permanece intacta.

## ADDED Requirements

### Requirement: Skin de disciplina (acento + clases del dominio)
El visor SHALL exponer, por cada disciplina soportada, una **skin** con su nombre, su color de
**acento** de marca y la **lista canónica de clases IFC** de ese dominio, definida por un **mapa
estático** (no derivada solo del modelo). En Slice 1 las disciplinas son **Diseño** (`diseno`,
acento `#2f6bed`) y **Estructuras** (`estructuras`, acento `#e07a4f`).

#### Scenario: La skin de Diseño declara su acento y sus clases
- **GIVEN** la disciplina `diseno`
- **WHEN** se consulta su skin en `SKINS`
- **THEN** el acento es `#2f6bed`
- **AND** sus clases incluyen `IFCWALL`, `IFCSLAB` y `IFCWINDOW` (clases de modelo de edificio
  soportadas por `ELEMENT_TYPES`).

#### Scenario: La skin de Estructuras declara su acento y sus clases
- **GIVEN** la disciplina `estructuras`
- **WHEN** se consulta su skin en `SKINS`
- **THEN** el acento es `#e07a4f`
- **AND** sus clases incluyen `IFCCOLUMN`, `IFCBEAM` y `IFCFOOTING`.

### Requirement: Color categórico por clase IFC
El visor SHALL asignar a cada clase IFC un **color propio y estable por tipo** (mapa categórico),
**independiente del acento** de disciplina. El color SHALL ser determinista para una misma clase,
distinto entre clases del mapa, y SHALL usar un **color de reserva** neutro para las clases no
mapeadas. El color NO SHALL ser una rampa derivada del color de disciplina (resuelve D-SK-2).

#### Scenario: La misma clase da siempre el mismo color
- **GIVEN** la clase `IFCWALL`
- **WHEN** se consulta `colorPorClase("IFCWALL")` dos veces
- **THEN** ambas llamadas devuelven el mismo color (determinismo)
- **AND** el color es un `{ r, g, b }` con componentes en el rango `0..1`.

#### Scenario: Clases distintas dan colores distintos
- **GIVEN** las clases `IFCWALL` e `IFCCOLUMN`
- **WHEN** se consultan sus colores categóricos
- **THEN** los dos colores son distintos entre sí.

#### Scenario: Una clase no mapeada cae en el color de reserva
- **GIVEN** una clase ausente del mapa (p. ej. `IFCTANK`)
- **WHEN** se consulta `colorPorClase("IFCTANK")`
- **THEN** devuelve el color de reserva neutro (gris), no un error.

#### Scenario: El color por clase no depende de la disciplina
- **GIVEN** la clase compartida `IFCSLAB`
- **WHEN** se consulta su color categórico
- **THEN** el color es el mismo con independencia de qué skin (Diseño o Estructuras) esté activa.

### Requirement: Leyenda de la skin por intersección con el modelo
El visor SHALL construir la leyenda de la skin como la **intersección** entre las clases del mapa
estático de la disciplina y las clases **realmente presentes** en el modelo cargado (la salida de
`viewer.classes()`). Cada entrada SHALL llevar la clase, su conteo en el modelo y su color
categórico. Las clases del dominio ausentes del modelo NO SHALL aparecer, y las clases presentes
fuera del dominio de la disciplina activa NO SHALL aparecer.

#### Scenario: Solo se listan las clases del dominio presentes en el modelo
- **GIVEN** la disciplina `estructuras` y un modelo cuyas clases presentes son
  `IFCCOLUMN` (×4), `IFCBEAM` (×6) e `IFCWINDOW` (×3)
- **WHEN** se calcula `leyendaSkin("estructuras", presentes)`
- **THEN** la leyenda contiene `IFCCOLUMN` e `IFCBEAM` con sus conteos y colores categóricos
- **AND** NO contiene `IFCWINDOW` (fuera del dominio de Estructuras)
- **AND** NO contiene clases de Estructuras ausentes del modelo (p. ej. `IFCFOOTING`).

#### Scenario: La leyenda alimenta el coloreado por clase existente
- **GIVEN** una leyenda de skin con la entrada `{ ifcClass: "IFCCOLUMN", color }`
- **WHEN** la capa de UI aplica la skin
- **THEN** invoca `viewer.setColorByClass("IFCCOLUMN", color)` con el color categórico de la
  entrada (reutiliza la superficie pública existente, sin recalcular geometría).

### Requirement: La skin no altera el modelo neutro ni dispara las llaves
Aplicar o conmutar una skin SHALL ser una operación de **presentación**: no reescribe el IFC, no
modifica la ingesta de geometría ni el modelo neutro, y no produce el estado `verified-signed`. El
re-vestido SHALL ser reversible al color original (web-ifc) mediante `resetColors()`.

#### Scenario: Conmutar de disciplina es reversible y no toca el modelo
- **GIVEN** un modelo cargado con la skin de Diseño aplicada
- **WHEN** se conmuta a la skin de Estructuras
- **THEN** el visor revierte al color base (`resetColors`) y re-pinta con la leyenda de Estructuras
- **AND** la geometría, la cota de elemento y el derivado congelado (golden `C4-FED-06`)
  permanecen sin cambios (la operación es de render, no reescribe ficheros).

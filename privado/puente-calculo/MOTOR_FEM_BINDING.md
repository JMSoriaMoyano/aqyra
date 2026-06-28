# Binding a `motor-fem 0.1.0` — contrato de integración

`motor-fem` se consume **anclado** desde el ecosistema (`../../integracion/versions.lock`) y **no está vendorizado** en este repo. Su API concreta no aparece documentada aquí, así que el binding (`engine.MotorFemBinding`) está **cableado hasta el borde de la llamada**: el ensamblado del problema y el parseo de resultados están hechos y testeados; **solo queda confirmar el nombre del *entrypoint*** del paquete real.

## Qué está hecho (y testeado)

- **`motor_request.to_request(EngineModel, combo) -> dict`** — serializa el problema FE completo (nudos+apoyos, barras+sección/material/releases, cargas globales, combinaciones) a un dict **neutro JSON-able**.
- **`motor_request.from_response(dict) -> EngineResult`** — parsea la respuesta del motor al esquema neutro.
- **`MotorFemBinding`** — importa `motor_fem`, valida que expone el entrypoint y, en `solve`, hace `to_request → motor_fem.<entrypoint>(request) → from_response`. Falla con mensaje claro si el motor no está o el entrypoint no existe (no finge cálculo).

Tests: `tests/test_motor_request.py` cubre el round-trip de ensamblado/parseo y el binding completo con un `motor_fem` falso inyectado.

## Lo único pendiente: el entrypoint real

Por defecto el binding llama a `motor_fem.solve(request)`. Si la API real difiere, se ajusta en **un solo punto**:

```python
MotorFemBinding(entrypoint="<nombre_real_de_la_funcion>")
```

…o, si el motor usa una clase/firma distinta (p. ej. `Model(...).run()`), adaptar `MotorFemBinding.solve` para construir el problema desde el `request` neutro y devolver el `response` con la forma de abajo. Confirmar también `axial_tension_positive` (PyNite reporta tracción negativa; motor-fem por confirmar).

## Forma del REQUEST (lo que el binding pasa)

```json
{
  "combo": "ELU1",
  "nodes":   [{"id","x","y","z","support":[DX,DY,DZ,RX,RY,RZ]}],
  "members": [{"id","i","j","E","G","A","Iy","Iz","J","rotation",
               "releases":[Dxi,Dyi,Dzi,Rxi,Ryi,Rzi,Dxj,Dyj,Dzj,Rxj,Ryj,Rzj]}],
  "loads":   [{"kind","target","direction":"FZ","value","case"}],
  "combos":  [{"name","factors":{"G":1.35,"Q":1.5}}]
}
```
`support`: bool, true=restringido. `releases`: bool, true=liberado. Ejes en letras del motor: `Iy`=débil, `Iz`=fuerte. Global Z-up, gravedad −Z (D-018).

## Forma del RESPONSE (lo que el motor debe devolver para `combo`)

```json
{
  "members": [{"id","stations":[{"x","axial","Fy","Fz","Mx","My","Mz","dx","dy","dz"}]}],
  "nodes":   [{"id","DX","DY","DZ","RX","RY","RZ","reaction":[FX,FY,FZ,MX,MY,MZ]}]}
```
`reaction` = `null` en nudos sin apoyo. El adaptador alinea el axil a **N>0 tracción** según `axial_tension_positive`.

> La QA (PyNite, `../qa-pynite/`) re-calcula **independientemente** y reconcilia esta salida (D-023). El binding produce `computed`; el verde lo acuña la firma de JM.

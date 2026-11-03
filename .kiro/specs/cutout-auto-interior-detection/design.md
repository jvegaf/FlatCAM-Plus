# Diseño: detección interior automática de recortes

## Arquitectura de la solución

El cambio se encuentra en un único archivo (`appPlugins/ToolCutOut.py`) y consta de:

1. Una función auxiliar de clasificación
2. Modificación del bucle de procesamiento en el bloque `kind != 'single'`

No hay cambios estructurales en el proyecto. No hay nuevas dependencias.

---

## Componentes afectados

```
complementos de aplicación/ToolCutOut.py
  └── clase recortada
       ├── _classify_contours(object_geo) → dict[int, bool] [NUEVO]
       └── on_freeform_cutout() [CAMBIADO]
```

---

## Función auxiliar: `_classify_contours`

```pitón
def _classify_contours(self, geometrías: lista) -> establecer:
    """
    Clasifica polígonos como internos (contenidos dentro de otro polígono más grande).

    Argumentos:
        geometrías: Lista de polígonos (salida de flatten_shapely_geometry)

    Devoluciones:
        Conjunto de índices para polígonos clasificados como internos.
        Los polígonos que no están presentes en el conjunto se consideran externos.
    """
```

### Algoritmo

```
1. Si len(geometrías) <= 1:
     return set() # Nada que ordenar

2. Para cada polígono, calcule el área del polígono relleno (Polygon(geo.exterior))
   - Esto convierte la "franja estrecha" (LineString almacenada en búfer) en un polígono sólido

3. Encuentra el polígono con el área rellena MÁS GRANDE → exterior_candidate

4. Cree una versión rellena del exterior: exterior_filled = Polygon(exterior_candidate.exterior)

5. Para cada uno de los demás polígonos (índice i):
   un. Obtener el punto_representante() del polígono
   B. Si exterior_filled.contiene (punto_representante):
        → Marcar índice i como INTERIOR
   c. Más:
        → Mantener como EXTERIOR (no agregar al conjunto)

6. Conjunto de índice interior de retorno
```

### ¿Por qué `representative_point()` en lugar de `contiene(polígono)`?

Los polígonos de Gerber son franjas estrechas (LineString amortiguado con un ancho de apertura ≈ 0,254 mm). `Polygon.contains(other_polygon)` puede devolver False porque la franja de la ranura interior puede tener partes fuera de la exterior rellenas (en los bordes, debido al almacenamiento en búfer). Usar `representative_point()` (un punto que se garantiza que estará dentro del polígono) es más sólido para probar "¿está este polígono geográficamente dentro del otro?".

### Por qué llenar `Polygon(geo.exterior)`

El perfil Gerber solid_geometry es una tira hueca (anillo fino). Para probar la contención, necesitamos un polígono LLENADO (sin un agujero en el medio). `Polygon(geo.exterior)` crea el polígono sólido a partir del contorno exterior de la franja.

---

## Modificación del bucle de procesamiento

### Código actual (líneas ~790-798 de ToolCutOut.py)

```pitón
object_geo = flatten_shapely_geometry(object_geo)
para geom_struct en object_geo:
    si cutout_obj.kind == 'gerber':
        si margen >= 0:
            geom_struct = (geom_struct.buffer(margen + abs(cut_dia / 2))).exterior
        más:
            geom_struct_buff = geom_struct.buffer(-margen + abs(cut_dia / 2))
            geom_struct = geom_struct_buff.interiores
```

### Código propuesto

```pitón
object_geo = flatten_shapely_geometry(object_geo)

# Ordenar contornos internos y externos
índices_interiores = self._classify_contours(object_geo)

para i, geom_struct en enumerar (object_geo):
    si cutout_obj.kind == 'gerber':
        si margen >= 0:
            almacenado en búfer = geom_struct.buffer (margen + abs (cut_dia / 2))
            si estoy en interior_indices:
                # Recorte interno: desplazado en el agujero
                si está almacenado en búfer.interiores:
                    geom_struct = buffered.interiors[0]
                más:
                    # Alternativa: si no hay interior, use exterior con advertencia
                    self.app.log.advertencia(
                        "Recorte: el contorno interior %d no tiene interiores después de la zona de influencia."
                        "Usar el exterior como alternativa". %i)
                    geom_struct = almacenado en búfer.exterior
            más:
                # Contorno externo: desplazado hacia el exterior del tablero
                geom_struct = almacenado en búfer.exterior
        más:
            geom_struct_buff = geom_struct.buffer(-margen + abs(cut_dia / 2))
            geom_struct = geom_struct_buff.interiores
```

---

## Diagrama de flujo

```
on_freeform_cutout()
    │
    ├── tipo == 'único' → flujo actual (sin cambios)
    │
    └── tipo != 'soltero' (Panel)
         │
         ├── flatten_shapely_geometry(object_geo)
         │
         ├── _classify_contours(object_geo) → interior_indices [NUEVO]
         │
         └── para i, geom_struct en enumerar (object_geo):
              │
              ├── margen >= 0:
              │ ├── i en interior_indices → buffered.interiors[0] [NUEVO]
              │ └── NO estoy en interior_indices → buffered.exterior [EXISTENTE]
              │
              └── margen < 0: → flujo actual (sin cambios)
```

---

## Tratamiento de casos extremos

| Caso | Detección | Acción |
| ------ | ---------- | ------ |
| 1 polígono | `len(geometrías) <= 1` | Conjunto de retorno () → cambio cero |
| Múltiples polígonos sin contención (panel) | `contiene()` devuelve Falso para todos | Conjunto vacío → todo tratado como exterior |
| Borde de juego de tragamonedas | `representative_point()` puede estar fuera del exterior | Tratado como externo (correcto) |
| Geometría abierta (sin interiores después del buffering) | `buffered.interiors` está vacío | Recurrir a `.exterior` + advertencia de registro |
| Polígonos degenerados | `representative_point()` genera una excepción | intentar/excepto → tratado como externo |

---

## Impacto en otros flujos

| Flujo | Impacto |
| ------- | -------- |
| Tipo = Soltero | NINGUNO: no se alcanza el código |
| Margen < 0 | NINGUNO: sucursal separada y no afectada |
| Mordeduras de ratón | NINGUNO: procesado más tarde, utiliza la misma lógica sin _classify |
| Brechas/Puentes | NINGUNO: se aplica más tarde a través de any_cutout_handler() |
| Geometría (no Gerber) | NINGUNO — rama separada `else`, no afectada |
| geo_init (generar CNCJob) | NINGUNO: recibe solid_geo ya procesado |

---

## Dependencias

- **Shapely >= 2.0** (ya en uso): `Polygon`, `representative_point()`, `contains()`
- No hay nuevas dependencias

---

## Riesgos residuales

1. **Gerber con polígono "interno" que en realidad es una marca/logotipo:** Raro en las capas del perfil, pero posible. Mitigación: funciona correctamente si el polígono está contenido; el desplazamiento interior es semánticamente correcto para cualquier forma que deba "cortarse" de la placa.

2. **Rendimiento con muchos polígonos:** Teórico: los PCB con >20 ranuras de perfil son extremadamente raros. Si es necesario en el futuro, utilice STRtree para consultas espaciales O(log n).

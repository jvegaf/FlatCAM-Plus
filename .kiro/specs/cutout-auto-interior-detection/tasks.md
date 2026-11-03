# Tareas: Detección interior automática de recortes

## Implementación

### Tarea 1: Crear la función auxiliar `_classify_contours`

- **Archivo:** `appPlugins/ToolCutOut.py`
- **Ubicación:** Método de la clase `CutOut`, antes de `on_freeform_cutout()`
- **Acción:** Implementar la función que recibe una lista de geometrías y devuelve un conjunto de índices interiores
- **Criterios de aceptación:** La función devuelve un conjunto vacío para 1 polígono, devuelve índices correctos para más de 2 polígonos con contención

### Tarea 2: Modificar el bucle de procesamiento en `on_freeform_cutout()`

- **Archivo:** `appPlugins/ToolCutOut.py`
- **Ubicación:** bloque `else` (tipo! = 'único'), líneas ~790-798
- **Acción:**
  - Agregar llamada a `_classify_contours()` antes del bucle
  - Convertir `para geom_struct` a `para i, geom_struct en enumerate()`
  - Dentro de `if margin >= 0:`, bifurcación entre `.exterior` y `.interiors[0]` según clasificación
  - Agregar respaldo con advertencia de registro para interiores vacíos
- **Criterios de aceptación:** Gerber con contorno + ranura interna genera caminos con desplazamientos correctos (de afuera a exterior, de adentro a ranura)

### Tarea 3: Agregar la importación `Polygon` a la parte superior del archivo

- **Archivo:** `appPlugins/ToolCutOut.py`
- **Ubicación:** Bloque de importaciones (parte superior del archivo)
- **Acción:** Compruebe si `Polygon` de Shapely ya está importado. Si no, agregue.
- **Criterios de aceptación:** Sin ImportError al usar `Polygon(geo.exterior)`

### Tarea 4: Prueba con el usuario Gerber (Fusion 360 — engranaje + ranura triangular)

- **Acción:**
  - Importar el perfil Gerber en FlatCAM Plus
  - Ejecutar recorte con Kind=Panel
  - Comprobar visualmente que el contorno externo tiene un desplazamiento exterior y la ranura interna tiene un desplazamiento interior
- **Criterios de aceptación:** Ambas trayectorias están en el lado correcto según la imagen de referencia.

### Tarea 5: Prueba de regresión: Gerber con un solo polígono

- **Acción:**
  - Importación perfil simple Gerber (rectangular o curvo, sin ranuras)
  - Ejecutar recorte con Kind=Panel y Kind=Single
  - Comprobar qué resultado es idéntico al comportamiento anterior.
- **Criterios de aceptación:** Cero diferencia en la trayectoria generada vs la versión sin modificación

### Tarea 6: Prueba de regresión: panel con múltiples PCB

- **Acción:**
  - Importe Gerber desde el panel con más de 2 contornos uno al lado del otro (sin contención)
  - Ejecutar recorte con Kind=Panel
  - Comprobar que TODOS los contornos reciben un desplazamiento exterior
- **Criterios de aceptación:** Comportamiento idéntico al anterior para paneles reales

### Tarea 7: Caso de borde de prueba: Gerber con ranura tocando el borde

- **Acción:**
  - Crea o encuentra Gerber con una ranura que se cruza con el contorno exterior.
  - Ejecutar recorte
  - Comprobar que la ranura no esté clasificada como "interior"
- **Criterios de aceptación:** Ranura tratada como desplazada exterior

---

## Orden de ejecución

```
Tarea 3 (importar) → Tarea 1 (ayudante) → Tarea 2 (bucle) → Tarea 4 (prueba principal) → Tarea 5-7 (regresión)
```

---

## Estimación

| Tarea | Esfuerzo |
| ------ | --------- |
| Tarea 1 | 15 minutos |
| Tarea 2 | 15 minutos |
| Tarea 3 | 2 minutos |
| Tarea 4 | 10 minutos |
| Tarea 5-7 | 15 minutos |
| **Totales** | **~1 hora** |

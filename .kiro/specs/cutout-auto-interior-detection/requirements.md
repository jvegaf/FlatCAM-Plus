# Herramienta de recorte: detección automática de contornos internos

## Contexto

La herramienta de recorte de FlatCAM Plus genera trayectorias de herramientas para cortar PCB a partir de material. Cuando un perfil Gerber contiene múltiples contornos (por ejemplo, contorno externo + ranura/corte interno), la herramienta actual aplica el desplazamiento "exterior" uniformemente a todos los polígonos.

Esto da como resultado que se corten muescas internas desde el lado equivocado: la fresadora quita material del tablero en lugar de abrir el orificio al tamaño correcto.

### Problema visual

```
Comportamiento ACTUAL (incorrecto para ranuras internas):
┌─────────────────────┐
│ PCB │
│ ┌─────┐ │
│ │RANURA │←fresa │ ← Fresa FUERA de la ranura = elimina material del tablero
│ └─────┘ │
│ │
└─────────────────────┘
     ↑ fresa ← Fresa FUERA del contorno = correcta para exterior

Comportamiento DESEADO:
┌─────────────────────┐
│ PCB │
│ ┌─────┐ │
│ │herramienta de fresado→│ │ ← Fresa DENTRO de la ranura = abre el agujero correctamente
│ └─────┘ │
│ │
└─────────────────────┘
     ↑ fresa ← Fresa FUERA del contorno = correcta para exterior
```

### Causa raíz

En `ToolCutOut.py`, en el bloque `kind != 'single'` (modo Panel), el código itera cada polígono y aplica:

```pitón
geom_struct = (geom_struct.buffer(margen + abs(cut_dia / 2))).exterior
```

Utiliza `.exterior` para TODOS los polígonos, sin distinguir si el contorno es exterior (borde del tablero) o interior (agujero/ranura).

---

## Requisitos funcionales

### REQ-01: Detección automática de contornos internos

Cuando la herramienta de recorte procesa un Gerber con múltiples polígonos (Tipo=Panel), debería identificar automáticamente qué polígonos son contornos internos (contenidos dentro de otro polígono más grande) y cuáles son contornos externos.

### REQ-02: Desplazamiento invertido para contornos internos

Los contornos clasificados como internos deben desplazarse DENTRO del orificio (use `.interiors[0]` del buffer en lugar de `.exterior`), asegurando que el corte sea del tamaño exacto del diseño.

### REQ-03: Regresión cero para un solo polígono

Cuando Gerber contiene sólo un polígono (el caso más común es un contorno simple sin ranuras), el comportamiento debería ser idéntico al actual. Ningún contorno se clasifica como "interior" cuando existe un solo polígono.

### REQ-04: Regresión cero para paneles reales

Cuando Gerber contiene varios polígonos que NO están contenidos entre sí (panel con varios PCB uno al lado del otro), todos deben seguir siendo tratados como exteriores: comportamiento idéntico al actual.

### REQ-05: Transparencia: sin cambios en la interfaz de usuario

La detección debe ser automática y siempre activa en modo Panel con >1 polígono. No requiere casilla de verificación, botón de opción ni ninguna configuración de usuario adicional.

### REQ-06: Repliegue seguro

Si la geometría de un borde interior no produce ".interiors" válido después del búfer (caso de borde de geometría abierta o degenerada), debería recurrir a ".exterior" y emitir una advertencia de registro: nunca falle silenciosamente ni se bloquee.

### REQ-07: Soporte para múltiples ranuras

Una placa puede tener más de un recorte interno (por ejemplo, 2 ranuras + 1 contorno). Todas las ranuras deben detectarse y procesarse correctamente.

---

## Requisitos no funcionales

### REQ-08: Rendimiento

La detección de contención debe completarse en un tiempo imperceptible para el usuario. Los PCB típicos tienen de 2 a 5 polígonos en el perfil; la complejidad O(n) es suficiente.

### REQ-09: Compatibilidad

- No debería cambiar el comportamiento de Kind=Single
- El comportamiento no debería cambiar cuando el margen < 0 (ya funciona de manera diferente)
- No debería afectar a otros complementos (Aislamiento, Fresado, etc.)
- Debe trabajar con Gerbers desde cualquier CAD (Fusion 360, KiCad, EasyEDA, EAGLE)

### REQ-10: Mantenibilidad

El código agregado debe estar aislado en una función auxiliar (por ejemplo, `_classify_interior_exterior()`) para facilitar las pruebas y el mantenimiento futuro.

---

## Escenarios de prueba

| Escenario | Entrada | Resultado esperado |
| --------- | ------- | -------- |
| Contorno simple (1 polígono) | Gerber con 1 contorno | Offset exterior, idéntico al actual |
| Contorno + 1 ranura interna | Gerber con 2 contornos (el externo contiene el interno) | Externo: compensado afuera. Interno: interior desplazado |
| Contorno + 3 ranuras internas | Gerber con 4 contornos | Exterior: exterior. 3 internos: interior |
| Panel (2 PCB uno al lado del otro) | Gerber con 2 contornos sin contención | Ambos: desplazamiento exterior |
| Ranura tocando el borde | Gerber con ranura que cruza el contorno | La ranura no está "contenida" → tratada como externa |
| Polígono único + margen negativo | 1 contorno con margen < 0 | Comportamiento actual (usa .interiors): sin cambios |
| Gerber con geometría abierta | Camino no cerrado | Retroceder a .exterior con advertencia |

---

## Fuera de alcance

- Detección de anidamiento multinivel (contorno dentro del contorno dentro del contorno): límite a 1 nivel
- Cambios en la interfaz de usuario (sin nuevos widgets)
- Cambios en el analizador Gerber.
- Cambios en Tipo=Único
- Soporte de panel con detección automática de PCB individuales (esta es otra característica)

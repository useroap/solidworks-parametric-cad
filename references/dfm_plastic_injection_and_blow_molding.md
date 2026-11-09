---
title: "Subhabilidad: DFM Plástico para Inyección y Soplado (Estándar CAD Engineering)"
company: "CAD Automation"
module: "cad_dfm_plastics"
date: 2026-10-29
tags:
  - dfm
  - plastic-injection
  - blow-molding
  - polymers
  - sealing-lips
  - tamper-evident
---

# Subhabilidad: DFM Plástico para Inyección y Soplado (Estándar CAD Engineering)

Esta subhabilidad establece las reglas de diseño para manufactura (**DFM - Design for Manufacturing**) aplicadas en **CAD Automation** para tapas, envases y componentes plásticos inyectados o soplados, asegurando desmoldeo limpio, estanqueidad hermética y control de peso en resinas estándar.

---

## 1. Materiales, Densidades y Factores de Contracción

Al calcular masa, costo por gramo o dimensiones de cavidad de molde:

| Resina | Nombre Técnico | Densidad ($\text{g/cm}^3$) | Contracción Volumétrica | Aplicación Típica CAD Engineering |
| :--- | :--- | :---: | :---: | :--- |
| **PP** | Polipropileno Homopolímero / Copolímero | **0.90 – 0.91** | **1.5% – 2.0%** | Tapas roscadas, flip-top y dosificadores industriales. |
| **PEAD (HDPE)** | Polietileno de Alta Densidad | **0.95 – 0.96** | **2.0% – 2.8%** | Tapas inviolables de bidones, botellas sopladas de lácteos y químicos. |
| **PEBD (LDPE)** | Polietileno de Baja Densidad | **0.92 – 0.93** | **1.5% – 3.0%** | Insertos cuentagotas, tapones flexibles y sobretapas. |
| **PET** | Polietilentereftalato | **1.35 – 1.38** | **0.2% – 0.5%** | Preformas y botellas sopladas de bebidas carbonatadas. |

### Cálculo Automatizado de Masa y Resina en Python:
```python
DENSITIES = {
    "PP": 0.91,
    "HDPE": 0.955,
    "LDPE": 0.925,
    "PET": 1.37,
}

def calculate_part_mass(sw_doc, resin="PP"):
    mp = sw_doc.Extension.CreateMassProperty
    vol_cm3 = (mp.Volume * 1e9) / 1000.0  # m3 a cm3
    density = DENSITIES.get(resin.upper(), 0.91)
    mass_g = vol_cm3 * density
    return vol_cm3, mass_g
```

---

## 2. Geometría de Elementos de Sellado (Sealing Features)

Para garantizar cero fugas de gas o líquido sin requerir liner espumado:

```
          [Tapa: Techo Superior]
         ┌──────────────────────┐
         │                      │
         │   /│ Crab's Claw     │  Bore Seal / Oliva
         │  / │ (En cuña 45°)   │  (Interferencia radial)
         │ /  │                 │    ┌──┐
         │/   │                 │    │  │ ◄── Interferencia: 0.20 mm
         │    │                 │    └──┘
         └────┴─────────────────┴────────────────
              ▲                      ▲
              │                      │
          [Labio Superior]       [Pared Interna ØI]
          (Superficie de sellado del cuello)
```

### 2.1 Sello de Oliva / Diámetro Interior (Bore Seal / Plug Seal)
- Cilindro o labio anular concéntrico con la falda.
- **Interferencia Radial:** El diámetro exterior del labio debe ser entre **$0.15$ y $0.30\text{ mm}$ mayor** que el diámetro interior nominal del cuello ($I$) de la botella.
- **Ángulo de Entrada:** Chaflán de guía de $15^\circ$ a $30^\circ$ en la punta del labio para facilitar el centrado durante el tapado en línea de llenado a alta velocidad.

### 2.2 Sello Tipo Uña de Cangrejo (Crab's Claw Seal)
- Labio flexible con perfil triangular o curvado orientado a $40^\circ - 45^\circ$.
- Al apretar la rosca, el labio flexiona contra la cara plana superior del cuello creando una banda continua de presión elastomérica.

---

## 3. Bandas de Seguridad Inviolable (Tamper-Evident / Pilfer-Proof)

Para envases de bebidas y farmacéuticos:
1. **Pestaña de Retención (Retention Flaps / Ratchet Teeth):**
   - Se diseñan a $45^\circ$ hacia el interior para que al tapar deslicen sobre el anillo de transferencia ($W$ / Transfer Bead) del cuello.
   - Al desatornillar, la pestaña traba mecánicamente bajo el escalón del anillo.
2. **Puentes Frangibles (Breakable Bridges):**
   - Ranuras circunferenciales unidas por $6$ a $12$ puentes delgados.
   - **Espesor del puente:** $0.30\text{ mm} \pm 0.05\text{ mm}$.
   - **Torque de rotura objetivo:** $1.2\text{ N}\cdot\text{m} - 1.8\text{ N}\cdot\text{m}$, garantizando que se rompan antes de que la rosca se desacople.

---

## 4. Reglas de Espesor de Pared y Desmoldeo

1. **Uniformidad de Pared:**
   - Variaciones súbitas de espesor causan deformaciones térmicas ("warpage") y marcas de rechupe ("sink marks").
   - Mantener espesor nominal en tapas entre $1.0\text{ mm}$ y $1.8\text{ mm}$.
2. **Espesor de Nervios / Moleteado (Ribs):**
   - El espesor en la base de cualquier nervio de refuerzo o estría exterior no debe superar el **$50\% - 60\%$** del espesor de la pared principal adyacente.
3. **Ángulos de Desmoldeo (Draft Angles):**
   - Caras exteriores visibles: Mínimo $1.0^\circ$ ($1.5^\circ$ si tiene textura EDM).
   - Núcleos interiores y falda roscada: Mínimo $0.5^\circ$ a $1.0^\circ$.

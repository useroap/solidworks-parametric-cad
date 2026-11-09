# Annotated Example: 2-Body Parametric Enclosure (`Dual_Body_Enclosure`)

This example demonstrates how to model a dual-material parametric enclosure with **two independent B-Rep solid bodies** in SolidWorks via Python COM:
1. **`Main_Housing`** (Structural rigid shell, e.g., ABS/Polycarbonate)
2. **`Sealing_Gasket`** (Perimeter elastomer seal / overmolding, e.g., TPE)

---

## 1. Feature Tree Sequence (`build_sw.py`)

To guarantee clean boolean separation while keeping both bodies in a single `.SLDPRT`, the feature order is:

1. **Global Equations (`add_globals`)**:
   Registers all driving parameters (`L_box`, `W_box`, `H_box`, `T_wall`, `Gasket_W`, `Gasket_H`) in `EquationMgr`.
2. **`Base_Extrusion` (`FeatureExtrusion3`, `Merge = True`)**:
   Extrudes the primary rectangular footprint ($L \times W$) to height $H$.
3. **`Main_Shell` (`InsertFeatureShell`)**:
   Hollows the core body leaving uniform thin-wall thickness `T_wall = 2.5 mm` on open top face.
4. **`Mounting_Bosses` (`FeatureExtrusion3`, `Merge = True`)**:
   Extrudes internal screw bosses, fully merged with `Main_Housing`.
5. **`Gasket_Channel_Cut` (`FeatureCut4`)**:
   Cuts a peripheral perimeter groove along the top mating rim for gasket retention.
6. **`Sealing_Gasket` (`FeatureSweep3` or `FeatureExtrusion3`, `Merge = False`)**:
   Builds the gasket along the groove contour with **`Merge = False`**, creating the second independent solid body.
7. **`name_solid_bodies(doc)`**:
   Iterates `doc.GetBodies2(0, True)`, naming the main structural body `"Main_Housing"` and the perimeter seal `"Sealing_Gasket"`.

---

## 2. Dynamic Equation Links

Every driving dimension is editable in SolidWorks under *Tools > Equations*:

```ini
"Length@Base_Sketch" = "L_box"
"Width@Base_Sketch"  = "W_box"
"Height@Base_Extrude" = "H_box"
"Thickness@Shell1"   = "T_wall"
"Gasket_Width@Seal_Sketch" = "Gasket_W"
"Gasket_Height@Seal_Sketch" = "Gasket_H"
```

---

## 3. Best Practices for Multi-Body Parts

- **Body Separation:** When adding the second body, always set `Merge = False` on the COM feature creation call (e.g. parameter 18 in `FeatureExtrusion3` or parameter 10 in `FeatureSweep4`).
- **Material Assignment:** Assign distinct optical and mass properties to each body using `IBody2::SetMaterialPropertyValues2`.
- **Drawing Projections:** When automating 2D drawings (ISO-7200), each body can be isolated or shown together in exploded/section views using `View.SetBodies`.

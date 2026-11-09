# Photogrammetric Calibration & B-Rep Loft Geometry Guide

This guide explains how to translate 2D orthogonal engineering drawings and product photographs into clean, manufacturable **B-Rep surfaces** in SolidWorks without loft waviness, spline overshoot, or boolean cut failures.

---

## 1. Photogrammetric Calibration from Orthogonal Views

When an engineering drawing provides only main bounding dimensions (e.g., total length $82.5\text{ mm}$, handle length $37.7\text{ mm}$, max width $24.1\text{ mm}$, lobe distance $16.7\text{ mm}$, bowl height $7.2\text{ mm}$) without intermediate radii:

1. **Crop and Grid Overlay:**
   Use `PIL.Image` and `ImageDraw` to overlay a 20-pixel grid on the cropped plan and side views.
2. **Compute Pixel-to-Millimeter Scale:**
   $$\text{scale}_x = \frac{x_{\text{tip, px}} - x_{\text{handle, px}}}{L_{\text{total}}},\qquad \text{scale}_z = \frac{z_{\text{top, px}} - z_{\text{bot, px}}}{W_{\text{max}}}$$
3. **Measure Intermediate Stations:**
   Convert pixel coordinates of every geometric transition into millimeters:
   - Collar rings ($L_{\text{anillo1}}, L_{\text{anillo2}}, D_{\text{collar}}, D_{\text{anillo2}}$)
   - Neck length and root width ($x_{\text{raiz\_pala}}, W_{\text{cuello\_pala}}$)
   - Abscissa of maximum width ($x_{\text{ancho\_max}}$)
   - Abscissa of deepest belly in side view ($x_{\text{belly}}$)
   - Abscissa of front notch ($x_{\text{muesca}} = L_{\text{total}} - \text{prof\_muesca}$) and lobe rounding start ($x_{\text{frente\_ext}}$).

---

## 2. Preventing Loft Waviness on Shell Parts (Spoons, Trays, Covers)

### Trap #1: Cutting a Variable-Radius Loft Vertically at the Perimeter
If you loft circular arcs with a wide oversize margin and then cut the plan silhouette vertically (`ThroughAllBoth`), any small radial interpolation difference between loft stations turns into a **vertical wave along the top rim** in the side view, and creates vertical cliff walls along the sides.

### Solution: Closed U-Sections with Horizontal Parting-Line Rims
In injection-molded shells, the upper rim of the cavity lies on a **planar parting surface** ($Y = y_{\text{rim}}$). Build each loft cross-section `Sec_Pala_Sxx` directly at the exact plan half-width $w_{\text{out}}(x)$:

- **Outer arc (3-point):** $(-w_{\text{out}}(x),\; y_{\text{rim}}(x)) \to (+w_{\text{out}}(x),\; y_{\text{rim}}(x))$ passing through $(0,\; y_{\text{out}}(x))$.
- **Inner arc (3-point):** $(-w_{\text{in}}(x),\; y_{\text{rim}}(x)) \to (+w_{\text{in}}(x),\; y_{\text{rim}}(x))$ passing through $(0,\; y_{\text{in}}(x))$.
- **Left & right closing lines:** **Horizontal segments at $Y = y_{\text{rim}}(x)$** connecting $\pm w_{\text{in}}(x)$ to $\pm w_{\text{out}}(x)$.

**Mathematical Condition for Non-Bulging 3-Point Arcs:**
A symmetric 3-point circular arc through $(\pm w, y_r)$ and $(0, y_{\text{bot}})$ is less than a semicircle ($< 180^\circ$) and never bulges wider than $\pm w$ if and only if its vertical sag satisfies:
$$0 < y_r - y_{\text{bot}} < w$$
Enforce `y_r - y_out <= 0.85 * w_out` at narrow neck stations so every cross-section is strictly well-behaved.

---

## 3. Preventing Spline Overshoot (Runge Phenomenon) in Plan Contours

When a part widens along an S-shoulder ($x \in [x_r, x_m]$) and then converges along straight side edges ($x \in [x_m, x_f]$):

1. **Match Endpoint Tangents ($C^1$ Cubic Hermite Interpolation):**
   On $u = \frac{x - x_r}{x_m - x_r} \in [0, 1]$, interpolate $w(x)$ using the exact neck slope $m_0 = \frac{w_r - w_{c1}}{x_r - x_{c1}}$ at $u=0$ and the exact converging side slope $m_1 = \frac{w_f - w_m}{x_f - x_m}$ at $u=1$:
   $$w(u) = w_r(2u^3 - 3u^2 + 1) + m_0\Delta x(u^3 - 2u^2 + u) + w_m(-2u^3 + 3u^2) + m_1\Delta x(u^3 - u^2)$$
2. **Uniform Loft Station Spacing:**
   Place loft planes on both sides of $x_m$ (e.g., 2 intermediate stations on the shoulder $[x_r, x_m]$ and 3 intermediate stations on the converging taper $[x_m, x_f]$) so SolidWorks' internal cubic loft spline follows the straight taper without creating an inward waist.

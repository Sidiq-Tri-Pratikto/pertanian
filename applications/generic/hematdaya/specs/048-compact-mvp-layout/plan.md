# Implementation plan — Compact MVP layout

Reuse HDScreen and its existing width, spacing, and safe-area tokens. Add optional supporting content below the main column in DOM order, side by side at the wide breakpoint. Keep the single-column structure for forms, with the existing scroll and content refs and keyboard-safe footer. Keep Home's main summary and read state together. Use the supporting column for the ranking, evidence, or supporting actions. Move archived devices and secondary data notices to supporting content on their respective screens.

Mirror the layout with the prototype Screen's existing aside and app CSS. Maintain its reference app copy. The change uses existing visual styles, calculations and routes. Compare the before and after captures at all four widths. Exercise enlarged text, action sizes, focus order, exact table alternatives, and the existing mobile and prototype checks.

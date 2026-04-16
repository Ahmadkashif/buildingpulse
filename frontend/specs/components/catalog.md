# Component Catalog

A flat index of the reusable components extracted from the source designs.

## Shell

- `AppShell` — composes SideNav, TopBar, main container
- `SideNav` — brand lockup + primary nav + footer nav + gradient CTA
- `TopBar` — section title, search, notification / settings / avatar icons
- `PageHeader` — H1 + description + action slot
- `SectionHeader` — numbered or plain subtitle with action slot

## UI primitives

- `Button` — variants: `gradient`, `default`, `secondary`, `tertiary`, `ghost`, `destructive`, `link`
- `Input`, `Select`, `Slider`, `Progress`, `Badge`, `YesNoToggle`, `Dialog`
- `Card` + subcomponents

## Report

- `KpiTile` — tonal and `signature` variants
- `EdgeAccentCard` — metric strip
- `BarChartCard` — stacked-bar SVG chart with legend chips (used for peer cohort comparison)
- `InfoCard` — titled k/v card
- `InsightCard` — icon + badge + title + body
- `ActionColumn` — vertical CTA stack
- `ExportDialog` — glass modal wrapping the PDF export stub
- `AssetCard`, `AlertBanner`, `RankedListCard` — available in the kit, not used in the current MVP flow

## Forms

- `FormField` — label + hint wrapper
- `PredictEuiForm` — full form for the `/forecasting` page

## Loading

- `ForecastProgress` — hero progress UI with 10% milestone copy

# BuildingPulse Frontend

Web UI for the BuildingPulse energy prediction tool.

## Purpose

Single-page form that collects 5 inputs about a NYC building and displays a predicted Site EUI.

## Inputs collected

| Field | Type | Notes |
|---|---|---|
| Property Type | dropdown | Office, Multifamily Housing, Hotel, K-12 School, Hospital, Retail Store, Warehouse, Restaurant, Other |
| Gross Floor Area | number (sqft) | 500 – 5,000,000 |
| Year Built | number (year) | 1800 – current year |
| Borough | dropdown | Manhattan, Brooklyn, Queens, Bronx, Staten Island |
| Number of Buildings on Lot | number | 1 – 50, default 1 |

## API contract (not yet implemented)

```
POST /predict/eui
Body: {
  "property_type": "Office",
  "gross_floor_area_sqft": 120000,
  "year_built": 1987,
  "borough": "Manhattan",
  "number_of_buildings": 1
}

Response: {
  "predicted_eui_kbtu_per_sqft_year": 87.3,
  "peer_median": 74.1,
  "property_type": "Office",
  "borough": "Manhattan"
}
```

Backend will run at `http://localhost:8000`; frontend at `http://localhost:3000`. Proxy `/api/*` during dev.

## Status

Placeholder — UI code to be added.

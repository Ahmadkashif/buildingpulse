CREATE TABLE leads (
    id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    role TEXT NOT NULL,
    sponsor_id TEXT NOT NULL,
    scenario_id TEXT,
    consent_given_at TEXT NOT NULL,
    fine_snapshot_usd REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX leads_prediction_id_idx ON leads (prediction_id);
CREATE UNIQUE INDEX leads_prediction_email_idx ON leads (prediction_id, email);

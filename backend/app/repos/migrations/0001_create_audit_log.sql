CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    request_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    prediction_id TEXT,
    lead_id TEXT,
    actor_session_id TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX audit_log_event_type_idx ON audit_log (event_type);
CREATE INDEX audit_log_prediction_id_idx ON audit_log (prediction_id);
CREATE INDEX audit_log_lead_id_idx ON audit_log (lead_id);

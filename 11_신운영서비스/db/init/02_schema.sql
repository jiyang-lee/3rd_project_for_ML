CREATE TABLE substation (
  substation_id TEXT PRIMARY KEY,
  manufacturer TEXT NOT NULL,
  raw_id INT NOT NULL,
  system_capability_group TEXT,
  common10_ready BOOLEAN,
  sensor_columns TEXT[],
  active BOOLEAN DEFAULT TRUE
);

CREATE TABLE sensor_readings (
  substation_id TEXT NOT NULL REFERENCES substation(substation_id),
  ts TIMESTAMPTZ NOT NULL,
  outdoor_temperature DOUBLE PRECISION,
  s_hc1_supply_temperature DOUBLE PRECISION,
  s_hc1_supply_temperature_setpoint DOUBLE PRECISION,
  p_hc1_return_temperature DOUBLE PRECISION,
  p_net_meter_energy DOUBLE PRECISION,
  p_net_meter_volume DOUBLE PRECISION,
  p_net_meter_heat_power DOUBLE PRECISION,
  p_net_meter_flow DOUBLE PRECISION,
  p_net_supply_temperature DOUBLE PRECISION,
  p_net_return_temperature DOUBLE PRECISION,
  s_dhw_supply_temperature DOUBLE PRECISION,
  s_dhw_supply_temperature_setpoint DOUBLE PRECISION,
  s_dhw_upper_storage_temperature DOUBLE PRECISION,
  s_dhw_lower_storage_temperature DOUBLE PRECISION,
  p_dhw_return_temperature DOUBLE PRECISION,
  p_dhw_return_temperature_setpoint DOUBLE PRECISION,
  PRIMARY KEY (substation_id, ts)
);
CREATE INDEX sensor_readings_ts_brin ON sensor_readings USING brin(ts);

CREATE TABLE window_features (
  substation_id TEXT NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  features JSONB NOT NULL,
  coverage_rate DOUBLE PRECISION NOT NULL,
  PRIMARY KEY (substation_id, window_end)
);

CREATE TABLE model_score_snapshot (
  snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  substation_id TEXT NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  scores JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agent_priority_card (
  card_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sample_id TEXT UNIQUE NOT NULL,
  substation_id TEXT NOT NULL,
  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  data_scope TEXT NOT NULL,
  primary_state TEXT NOT NULL,
  secondary_tags TEXT DEFAULT '',
  fault_detected BOOLEAN,
  task_detected BOOLEAN,
  activity_detected BOOLEAN,
  fault_probability DOUBLE PRECISION,
  task_probability DOUBLE PRECISION,
  activity_probability DOUBLE PRECISION,
  pre_event_detected TEXT,
  risk_probability DOUBLE PRECISION,
  fault_group TEXT,
  leadtime_label TEXT,
  leadtime_urgency DOUBLE PRECISION,
  group_weight DOUBLE PRECISION,
  priority_score DOUBLE PRECISION,
  priority_tier TEXT,
  review_flag BOOLEAN DEFAULT FALSE,
  review_reasons TEXT DEFAULT '',
  why_reason TEXT DEFAULT '',
  coverage_rate DOUBLE PRECISION,
  validation_level TEXT,
  features JSONB,
  source_card JSONB
);
CREATE INDEX agent_priority_card_sub_end ON agent_priority_card(substation_id, window_end DESC);
CREATE INDEX agent_priority_card_tier ON agent_priority_card(priority_tier, window_end DESC);

CREATE TABLE official_card_reference (
  reference_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_row JSONB NOT NULL,
  substation_id TEXT,
  window_end TIMESTAMPTZ,
  priority_score DOUBLE PRECISION
);

CREATE TABLE complaint_log (
  complaint_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  substation_id TEXT,
  event_time TIMESTAMPTZ,
  category TEXT,
  content TEXT,
  source TEXT
);

CREATE TABLE maintenance_history (
  maintenance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  substation_id TEXT,
  event_time TIMESTAMPTZ,
  event_type TEXT,
  content TEXT,
  source TEXT
);

CREATE TABLE doc_source (
  source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  collected_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE doc_chunks (
  chunk_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source_id BIGINT REFERENCES doc_source(source_id),
  title TEXT NOT NULL,
  breadcrumb TEXT,
  content TEXT NOT NULL,
  embedding vector(384)
);
CREATE INDEX doc_chunks_embedding_ivfflat ON doc_chunks USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE action_ticket (
  ticket_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  card_id BIGINT REFERENCES agent_priority_card(card_id),
  intent TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  text TEXT NOT NULL,
  generated_by TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE llm_call_log (
  call_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  card_id BIGINT,
  intent TEXT NOT NULL,
  model TEXT NOT NULL,
  generated_by TEXT NOT NULL,
  prompt_tokens INT DEFAULT 0,
  completion_tokens INT DEFAULT 0,
  estimated_cost_usd NUMERIC(12, 6) DEFAULT 0,
  cached BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE llm_response_cache (
  cache_key TEXT PRIMARY KEY,
  intent TEXT NOT NULL,
  card_id BIGINT NOT NULL,
  response_text TEXT NOT NULL,
  generated_by TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE agent_runs (
  run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  started_at TIMESTAMPTZ DEFAULT now(),
  trigger_card_ids BIGINT[],
  status TEXT,
  node_trace JSONB,
  error TEXT
);

CREATE TABLE replay_state (
  id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  virtual_time TIMESTAMPTZ,
  speed_factor DOUBLE PRECISION,
  running BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMPTZ DEFAULT now()
);

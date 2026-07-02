CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE substations (
  substation_id            TEXT PRIMARY KEY,          -- 'M1_5'
  manufacturer             TEXT NOT NULL,             -- 'M1'
  raw_id                   INT  NOT NULL,
  system_capability_group  TEXT,
  common10_ready           BOOLEAN,
  sensor_columns           TEXT[],
  active                   BOOLEAN DEFAULT TRUE
);

-- wide hypertable: one row per (substation, 10-min timestamp)
CREATE TABLE sensor_readings (
  ts             TIMESTAMPTZ NOT NULL,
  substation_id  TEXT NOT NULL REFERENCES substations(substation_id),
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
SELECT create_hypertable('sensor_readings', 'ts', chunk_time_interval => INTERVAL '7 days');

CREATE TABLE state_cards (
  card_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  sample_id      TEXT UNIQUE NOT NULL,               -- '{substation_id}_{window_end:%Y%m%d%H%M}'
  substation_id  TEXT NOT NULL REFERENCES substations(substation_id),
  window_start   TIMESTAMPTZ NOT NULL,
  window_end     TIMESTAMPTZ NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT now(),
  data_scope     TEXT DEFAULT 'replay_simulation',
  primary_state  TEXT NOT NULL,                      -- normal/fault/task/activity/review_required
  secondary_tags TEXT DEFAULT '',
  fault_detected BOOLEAN,
  task_detected BOOLEAN,
  activity_detected BOOLEAN,
  fault_probability DOUBLE PRECISION,
  task_probability DOUBLE PRECISION,
  activity_probability DOUBLE PRECISION,
  pre_event_detected TEXT,                           -- 'true'/'false'/'not_applicable_not_fault'/...
  risk_probability DOUBLE PRECISION,
  fault_group    TEXT,
  leadtime_label TEXT,
  leadtime_urgency DOUBLE PRECISION,
  group_weight   DOUBLE PRECISION,
  priority_score DOUBLE PRECISION,
  priority_tier  TEXT,
  review_flag    BOOLEAN DEFAULT FALSE,
  review_reasons TEXT DEFAULT '',
  why_reason     TEXT DEFAULT '',
  coverage_rate  DOUBLE PRECISION,
  validation_level TEXT DEFAULT 'replay_simulation',
  features       JSONB
);
CREATE INDEX ix_state_cards_sub_end ON state_cards(substation_id, window_end DESC);
CREATE INDEX ix_state_cards_tier ON state_cards(priority_tier, window_end DESC);

CREATE TABLE dispatch_orders (
  order_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  card_id       BIGINT REFERENCES state_cards(card_id),
  substation_id TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now(),
  virtual_time  TIMESTAMPTZ,
  priority_tier TEXT,
  priority_score DOUBLE PRECISION,
  title         TEXT,
  body_markdown TEXT,
  recommended_action TEXT,
  generated_by  TEXT,                                -- 'llm:gpt-4o-mini' | 'fallback:template'
  status        TEXT DEFAULT 'draft'                 -- draft/acknowledged/closed
);

CREATE TABLE agent_runs (
  run_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  started_at  TIMESTAMPTZ DEFAULT now(),
  trigger_card_ids BIGINT[],
  status      TEXT,                                  -- running/completed/failed/skipped_no_llm
  node_trace  JSONB,
  error       TEXT
);

CREATE TABLE replay_state (
  id            INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  virtual_time  TIMESTAMPTZ,
  speed_factor  DOUBLE PRECISION,
  running       BOOLEAN DEFAULT FALSE,
  updated_at    TIMESTAMPTZ DEFAULT now()
);
INSERT INTO replay_state (id, virtual_time, speed_factor, running)
VALUES (1, NULL, 60, FALSE);

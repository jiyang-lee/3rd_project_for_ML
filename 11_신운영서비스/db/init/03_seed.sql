INSERT INTO replay_state (id, virtual_time, speed_factor, running)
VALUES (1, NULL, 60, FALSE)
ON CONFLICT (id) DO NOTHING;

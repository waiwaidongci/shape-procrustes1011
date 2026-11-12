ALTER TABLE alignment_runs ADD COLUMN source_run_id INTEGER REFERENCES alignment_runs (id);
ALTER TABLE alignment_runs ADD COLUMN recalculation_key VARCHAR(64);
CREATE UNIQUE INDEX ux_alignment_runs_recalculation_key ON alignment_runs (recalculation_key);
CREATE INDEX ix_alignment_runs_source_run_id ON alignment_runs (source_run_id);

-- SoilAI schema version 0001. Immutable migration snapshot.

CREATE TABLE datasets (
	name VARCHAR(150) NOT NULL,
	version VARCHAR(40) NOT NULL,
	metadata_json JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (name, version)
);

CREATE TABLE ml_models (
	task VARCHAR(40) NOT NULL,
	name VARCHAR(100) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (task)
);

CREATE TABLE roles (
	name VARCHAR(32) NOT NULL,
	PRIMARY KEY (name)
);

CREATE TABLE users (
	email VARCHAR(254) NOT NULL,
	name VARCHAR(100) NOT NULL,
	password_hash TEXT NOT NULL,
	language VARCHAR(2) NOT NULL,
	active BOOLEAN NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE audit_logs (
	user_id VARCHAR(36),
	action VARCHAR(100) NOT NULL,
	resource VARCHAR(100) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);

CREATE TABLE farms (
	owner_id VARCHAR(36) NOT NULL,
	officer_id VARCHAR(36),
	name VARCHAR(150) NOT NULL,
	state VARCHAR(100) NOT NULL,
	district VARCHAR(100) NOT NULL,
	village VARCHAR(100) NOT NULL,
	location VARCHAR(250) NOT NULL,
	survey_number VARCHAR(100) NOT NULL,
	area FLOAT NOT NULL,
	area_unit VARCHAR(20) NOT NULL,
	deleted BOOLEAN NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT positive_farm_area CHECK (area > 0),
	FOREIGN KEY(owner_id) REFERENCES users (id),
	FOREIGN KEY(officer_id) REFERENCES users (id)
);

CREATE INDEX ix_farms_officer_id ON farms (officer_id);

CREATE INDEX ix_farms_owner_id ON farms (owner_id);

CREATE TABLE model_versions (
	model_id VARCHAR(36) NOT NULL,
	dataset_id VARCHAR(36) NOT NULL,
	version VARCHAR(40) NOT NULL,
	artifact_path TEXT NOT NULL,
	approved BOOLEAN NOT NULL,
	active BOOLEAN NOT NULL,
	metadata_json JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(model_id) REFERENCES ml_models (id),
	FOREIGN KEY(dataset_id) REFERENCES datasets (id)
);

CREATE TABLE notifications (
	user_id VARCHAR(36) NOT NULL,
	message TEXT NOT NULL,
	read BOOLEAN NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE password_resets (
	user_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	used BOOLEAN NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	UNIQUE (token_hash)
);

CREATE INDEX ix_password_resets_user_id ON password_resets (user_id);

CREATE TABLE permissions (
	name VARCHAR(80) NOT NULL,
	role VARCHAR(32) NOT NULL,
	PRIMARY KEY (name),
	FOREIGN KEY(role) REFERENCES roles (name)
);

CREATE TABLE sessions (
	user_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
	revoked BOOLEAN NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	UNIQUE (token_hash)
);

CREATE INDEX ix_sessions_user_id ON sessions (user_id);

CREATE TABLE user_roles (
	user_id VARCHAR(36) NOT NULL,
	role VARCHAR(32) NOT NULL,
	PRIMARY KEY (user_id, role),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(role) REFERENCES roles (name)
);

CREATE TABLE dataset_imports (
	user_id VARCHAR(36) NOT NULL,
	farm_id VARCHAR(36) NOT NULL,
	filename VARCHAR(200) NOT NULL,
	status VARCHAR(20) NOT NULL,
	rows JSON NOT NULL,
	mapping JSON NOT NULL,
	valid_rows JSON NOT NULL,
	imported_ids JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id),
	FOREIGN KEY(farm_id) REFERENCES farms (id)
);

CREATE INDEX ix_dataset_imports_user_id ON dataset_imports (user_id);

CREATE TABLE fields (
	farm_id VARCHAR(36) NOT NULL,
	name VARCHAR(100) NOT NULL,
	area FLOAT NOT NULL,
	soil_type VARCHAR(100) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (farm_id, name),
	CONSTRAINT positive_field_area CHECK (area > 0),
	FOREIGN KEY(farm_id) REFERENCES farms (id)
);

CREATE INDEX ix_fields_farm_id ON fields (farm_id);

CREATE TABLE model_metrics (
	version_id VARCHAR(36) NOT NULL,
	name VARCHAR(80) NOT NULL,
	value FLOAT NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(version_id) REFERENCES model_versions (id)
);

CREATE TABLE dataset_import_errors (
	import_id VARCHAR(36) NOT NULL,
	row_number INTEGER NOT NULL,
	message TEXT NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(import_id) REFERENCES dataset_imports (id)
);

CREATE INDEX ix_dataset_import_errors_import_id ON dataset_import_errors (import_id);

CREATE TABLE soil_samples (
	farm_id VARCHAR(36) NOT NULL,
	field_id VARCHAR(36),
	sample_code VARCHAR(100) NOT NULL,
	collected_on VARCHAR(10) NOT NULL,
	location VARCHAR(250) NOT NULL,
	laboratory VARCHAR(200) NOT NULL,
	status VARCHAR(20) NOT NULL,
	climate JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (farm_id, sample_code),
	FOREIGN KEY(farm_id) REFERENCES farms (id),
	FOREIGN KEY(field_id) REFERENCES fields (id)
);

CREATE INDEX ix_soil_samples_farm_id ON soil_samples (farm_id);

CREATE TABLE officer_reviews (
	sample_id VARCHAR(36) NOT NULL,
	officer_id VARCHAR(36) NOT NULL,
	remarks TEXT NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(sample_id) REFERENCES soil_samples (id),
	FOREIGN KEY(officer_id) REFERENCES users (id)
);

CREATE INDEX ix_officer_reviews_sample_id ON officer_reviews (sample_id);

CREATE TABLE predictions (
	sample_id VARCHAR(36) NOT NULL,
	version_id VARCHAR(36) NOT NULL,
	task VARCHAR(40) NOT NULL,
	result JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(sample_id) REFERENCES soil_samples (id),
	FOREIGN KEY(version_id) REFERENCES model_versions (id)
);

CREATE INDEX ix_predictions_sample_id ON predictions (sample_id);

CREATE TABLE reports (
	sample_id VARCHAR(36) NOT NULL,
	user_id VARCHAR(36) NOT NULL,
	language VARCHAR(2) NOT NULL,
	format VARCHAR(10) NOT NULL,
	path TEXT NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(sample_id) REFERENCES soil_samples (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE soil_measurements (
	sample_id VARCHAR(36) NOT NULL,
	parameter VARCHAR(40) NOT NULL,
	value FLOAT NOT NULL,
	unit VARCHAR(30) NOT NULL,
	method VARCHAR(150) NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (sample_id, parameter),
	CONSTRAINT nonnegative_measurement CHECK (value >= 0),
	FOREIGN KEY(sample_id) REFERENCES soil_samples (id) ON DELETE CASCADE
);

CREATE INDEX ix_soil_measurements_sample_id ON soil_measurements (sample_id);

CREATE TABLE crop_recommendations (
	prediction_id VARCHAR(36) NOT NULL,
	crop VARCHAR(80) NOT NULL,
	details JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(prediction_id) REFERENCES predictions (id)
);

CREATE TABLE fertilizer_recommendations (
	prediction_id VARCHAR(36) NOT NULL,
	details JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(prediction_id) REFERENCES predictions (id)
);

CREATE TABLE prediction_explanations (
	prediction_id VARCHAR(36) NOT NULL,
	contributions JSON NOT NULL,
	id VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(prediction_id) REFERENCES predictions (id)
);

INSERT INTO roles (name) VALUES ('FARMER'), ('AGRICULTURAL_OFFICER'), ('ADMIN');

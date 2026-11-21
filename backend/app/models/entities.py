import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, ForeignKey, UniqueConstraint, JSON, DateTime, Boolean, Integer, CheckConstraint, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


def now():
    return datetime.now(timezone.utc)


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class User(Record, Base):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2), default='en')
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Role(Base):
    __tablename__ = 'roles'
    name: Mapped[str] = mapped_column(String(32), primary_key=True)


class Permission(Base):
    __tablename__ = 'permissions'
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    role: Mapped[str] = mapped_column(ForeignKey('roles.name'))


class UserRole(Base):
    __tablename__ = 'user_roles'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    role: Mapped[str] = mapped_column(ForeignKey('roles.name'), primary_key=True)


class Session(Record, Base):
    __tablename__ = 'sessions'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class PasswordReset(Record, Base):
    __tablename__ = 'password_resets'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class Farm(Record, Base):
    __tablename__ = 'farms'
    owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    officer_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    state: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    village: Mapped[str] = mapped_column(String(100), default='')
    location: Mapped[str] = mapped_column(String(250), default='')
    survey_number: Mapped[str] = mapped_column(String(100), default='')
    area: Mapped[float] = mapped_column(Float)
    area_unit: Mapped[str] = mapped_column(String(20))
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint('area > 0', name='positive_farm_area'),)


class Field(Record, Base):
    __tablename__ = 'fields'
    farm_id: Mapped[str] = mapped_column(ForeignKey('farms.id'), index=True)
    name: Mapped[str] = mapped_column(String(100))
    area: Mapped[float] = mapped_column(Float)
    soil_type: Mapped[str] = mapped_column(String(100), default='')
    __table_args__ = (UniqueConstraint('farm_id', 'name'), CheckConstraint('area > 0', name='positive_field_area'))


class SoilSample(Record, Base):
    __tablename__ = 'soil_samples'
    farm_id: Mapped[str] = mapped_column(ForeignKey('farms.id'), index=True)
    field_id: Mapped[str | None] = mapped_column(ForeignKey('fields.id'), nullable=True)
    sample_code: Mapped[str] = mapped_column(String(100))
    collected_on: Mapped[str] = mapped_column(String(10))
    location: Mapped[str] = mapped_column(String(250), default='')
    laboratory: Mapped[str] = mapped_column(String(200), default='')
    status: Mapped[str] = mapped_column(String(20), default='draft')
    climate: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint('farm_id', 'sample_code'),)


class Measurement(Record, Base):
    __tablename__ = 'soil_measurements'
    sample_id: Mapped[str] = mapped_column(ForeignKey('soil_samples.id', ondelete='CASCADE'), index=True)
    parameter: Mapped[str] = mapped_column(String(40))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(30))
    method: Mapped[str] = mapped_column(String(150))
    __table_args__ = (UniqueConstraint('sample_id', 'parameter'), CheckConstraint('value >= 0', name='nonnegative_measurement'))


class Dataset(Record, Base):
    __tablename__ = 'datasets'
    name: Mapped[str] = mapped_column(String(150))
    version: Mapped[str] = mapped_column(String(40))
    metadata_json: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint('name', 'version'),)


class DatasetImport(Record, Base):
    __tablename__ = 'dataset_imports'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey('farms.id'))
    filename: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default='uploaded')
    rows: Mapped[list] = mapped_column(JSON)
    mapping: Mapped[dict] = mapped_column(JSON, default=dict)
    valid_rows: Mapped[list] = mapped_column(JSON, default=list)
    imported_ids: Mapped[list] = mapped_column(JSON, default=list)


class ImportErrorRow(Record, Base):
    __tablename__ = 'dataset_import_errors'
    import_id: Mapped[str] = mapped_column(ForeignKey('dataset_imports.id'), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)


class MLModel(Record, Base):
    __tablename__ = 'ml_models'
    task: Mapped[str] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(100))


class ModelVersion(Record, Base):
    __tablename__ = 'model_versions'
    model_id: Mapped[str] = mapped_column(ForeignKey('ml_models.id'))
    dataset_id: Mapped[str] = mapped_column(ForeignKey('datasets.id'))
    version: Mapped[str] = mapped_column(String(40))
    artifact_path: Mapped[str] = mapped_column(Text)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict] = mapped_column(JSON)


class ModelMetric(Record, Base):
    __tablename__ = 'model_metrics'
    version_id: Mapped[str] = mapped_column(ForeignKey('model_versions.id'))
    name: Mapped[str] = mapped_column(String(80))
    value: Mapped[float] = mapped_column(Float)


class Prediction(Record, Base):
    __tablename__ = 'predictions'
    sample_id: Mapped[str] = mapped_column(ForeignKey('soil_samples.id'), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey('model_versions.id'))
    task: Mapped[str] = mapped_column(String(40))
    result: Mapped[dict] = mapped_column(JSON)


class PredictionExplanation(Record, Base):
    __tablename__ = 'prediction_explanations'
    prediction_id: Mapped[str] = mapped_column(ForeignKey('predictions.id'))
    contributions: Mapped[dict] = mapped_column(JSON)


class CropRecommendation(Record, Base):
    __tablename__ = 'crop_recommendations'
    prediction_id: Mapped[str] = mapped_column(ForeignKey('predictions.id'))
    crop: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON)


class FertilizerRecommendation(Record, Base):
    __tablename__ = 'fertilizer_recommendations'
    prediction_id: Mapped[str] = mapped_column(ForeignKey('predictions.id'))
    details: Mapped[dict] = mapped_column(JSON)


class OfficerReview(Record, Base):
    __tablename__ = 'officer_reviews'
    sample_id: Mapped[str] = mapped_column(ForeignKey('soil_samples.id'), index=True)
    officer_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    remarks: Mapped[str] = mapped_column(Text)


class Report(Record, Base):
    __tablename__ = 'reports'
    sample_id: Mapped[str] = mapped_column(ForeignKey('soil_samples.id'))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'))
    language: Mapped[str] = mapped_column(String(2))
    format: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)


class Notification(Record, Base):
    __tablename__ = 'notifications'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    message: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Record, Base):
    __tablename__ = 'audit_logs'
    user_id: Mapped[str | None] = mapped_column(ForeignKey('users.id'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100))
    resource: Mapped[str] = mapped_column(String(100), default='')

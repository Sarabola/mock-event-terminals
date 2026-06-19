from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class NetworkSettings(Base):
    __tablename__ = "network_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    host: Mapped[str] = mapped_column(String(255), default="localhost")
    port: Mapped[int] = mapped_column(Integer, default=9091)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Device(Base):
    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    supports_temperature: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_card: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_liveness: Mapped[bool] = mapped_column(Boolean, default=False)


class DeviceSettings(Base):
    __tablename__ = "device_settings"
    __table_args__ = (UniqueConstraint("user_id", "device_name", name="uq_device_settings_user_device"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    device_name: Mapped[str] = mapped_column(ForeignKey("devices.name"))
    device_id: Mapped[str] = mapped_column(String(255), default="")
    temperature_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    above_normal_temp: Mapped[bool] = mapped_column(Boolean, default=False)
    abnormal_temp: Mapped[bool] = mapped_column(Boolean, default=False)
    old_event: Mapped[bool] = mapped_column(Boolean, default=False)
    liveness_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    card_event: Mapped[bool] = mapped_column(Boolean, default=False)
    card_number: Mapped[str] = mapped_column(String(64), default="12345")

    device: Mapped[Device] = relationship()


class ImageAsset(Base):
    __tablename__ = "image_assets"

    name: Mapped[str] = mapped_column(String(512), primary_key=True)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ImageSelection(Base):
    __tablename__ = "image_selections"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_image_selection_user_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(512))
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SendJob(Base):
    __tablename__ = "send_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    device_name: Mapped[str] = mapped_column(ForeignKey("devices.name"))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    total: Mapped[int] = mapped_column(Integer, default=0)
    sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    results: Mapped[list["SendResult"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class SendResult(Base):
    __tablename__ = "send_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("send_jobs.id"))
    image_name: Mapped[str] = mapped_column(String(512))
    status_code: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped[SendJob] = relationship(back_populates="results")

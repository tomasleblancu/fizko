"""Notification system models for Fizko platform."""

from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Text,
    Time,
    VARCHAR,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .user import Profile
    from .calendar import CalendarEvent


class NotificationTemplate(Base):
    """Plantilla reutilizable de notificación.

    Define el contenido, timing y configuración de una notificación.
    Soporta variables en el mensaje como {{company_name}}, {{event_title}}, etc.
    """

    __tablename__ = "notification_templates"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Identificación
    code: Mapped[str] = mapped_column(VARCHAR(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Categoría
    category: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    # 'calendar', 'tax_document', 'payroll', 'system', 'custom'

    # Tipo de entidad asociada
    entity_type: Mapped[Optional[str]] = mapped_column(VARCHAR(50), nullable=True)
    # 'calendar_event', 'form29', 'payroll', 'task', null

    # Contenido del mensaje (soporta variables)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)

    # Configuración de timing
    # Ejemplos:
    # {"type": "relative", "offset_days": -1, "time": "09:00"}  -> 1 día antes a las 9am
    # {"type": "absolute", "time": "17:00"}  -> El día del evento a las 5pm
    # {"type": "immediate"}  -> Enviar inmediatamente
    timing_config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{\"type\": \"immediate\"}'::jsonb")
    )

    # Configuración de prioridad y repetición
    priority: Mapped[str] = mapped_column(
        VARCHAR(20), server_default=text("'normal'")
    )  # 'low', 'normal', 'high', 'urgent'
    can_repeat: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    max_repeats: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    repeat_interval_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Condiciones para envío (opcional)
    send_conditions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Auto-asignación para nuevas empresas
    auto_assign_to_new_companies: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )

    # Metadata (extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # WhatsApp Template Integration
    # Template ID from Meta (created manually in Meta Business Manager)
    whatsapp_template_id: Mapped[Optional[str]] = mapped_column(
        VARCHAR(200), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    subscriptions: Mapped[list["NotificationSubscription"]] = relationship(
        "NotificationSubscription",
        back_populates="notification_template",
        cascade="all, delete-orphan",
    )
    scheduled_notifications: Mapped[list["ScheduledNotification"]] = relationship(
        "ScheduledNotification",
        back_populates="notification_template",
    )
    event_triggers: Mapped[list["NotificationEventTrigger"]] = relationship(
        "NotificationEventTrigger",
        back_populates="notification_template",
        cascade="all, delete-orphan",
    )


class NotificationSubscription(Base):
    """Suscripción de una empresa a una notificación específica.

    Permite a las empresas activar/desactivar notificaciones y personalizar
    su contenido y timing.
    """

    __tablename__ = "notification_subscriptions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Relaciones
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Configuración personalizada (sobrescribe template)
    custom_timing_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    custom_message_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Estado
    is_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Canales (futuro: email, push, etc.)
    channels: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'[\"whatsapp\"]'::jsonb")
    )

    # Filtros adicionales
    filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    notification_template: Mapped["NotificationTemplate"] = relationship(
        "NotificationTemplate", back_populates="subscriptions"
    )


class ScheduledNotification(Base):
    """Notificación programada para envío futuro.

    Esta tabla es procesada por el scheduler (manual o Celery) para enviar
    notificaciones en el momento apropiado.
    """

    __tablename__ = "scheduled_notifications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Relaciones
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Entidad relacionada (flexible)
    entity_type: Mapped[Optional[str]] = mapped_column(VARCHAR(50), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Destinatarios
    # [{"user_id": "uuid", "phone": "+56..."}, ...]
    recipients: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Contenido (ya renderizado)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timing
    scheduled_for: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Estado
    status: Mapped[str] = mapped_column(
        VARCHAR(30), server_default=text("'pending'")
    )
    # 'pending', 'processing', 'sent', 'failed', 'cancelled', 'skipped'

    # Resultados del envío
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    send_attempts: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Datos del envío exitoso
    send_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Repetición
    is_repeat: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    repeat_of: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("scheduled_notifications.id", ondelete="SET NULL"),
        nullable=True,
    )
    repeat_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))

    # Metadata (extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    notification_template: Mapped["NotificationTemplate"] = relationship(
        "NotificationTemplate", back_populates="scheduled_notifications"
    )


class NotificationHistory(Base):
    """Historial completo de notificaciones enviadas.

    Mantiene un registro de todas las notificaciones para auditoría,
    analytics y debugging.
    """

    __tablename__ = "notification_history"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Relaciones
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_template_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    scheduled_notification_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("scheduled_notifications.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Entidad relacionada
    entity_type: Mapped[Optional[str]] = mapped_column(VARCHAR(50), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Destinatario
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    phone_number: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)

    # Contenido
    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # Resultado
    status: Mapped[str] = mapped_column(VARCHAR(30), nullable=False)
    # 'sent', 'failed', 'delivered', 'read'

    # Datos de WhatsApp/Kapso
    whatsapp_conversation_id: Mapped[Optional[str]] = mapped_column(
        VARCHAR(100), nullable=True
    )
    whatsapp_message_id: Mapped[Optional[str]] = mapped_column(VARCHAR(100), nullable=True)

    # Timing
    sent_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(VARCHAR(50), nullable=True)

    # Metadata (extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")
    user: Mapped[Optional["Profile"]] = relationship("Profile")
    notification_template: Mapped[Optional["NotificationTemplate"]] = relationship(
        "NotificationTemplate"
    )


class NotificationEventTrigger(Base):
    """Trigger automático para generar notificaciones.

    Define condiciones que, al cumplirse, crean automáticamente una
    notificación programada. Ejemplo: cuando calendar_event.status = 'in_progress'
    """

    __tablename__ = "notification_event_triggers"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Identificación
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuración del trigger
    entity_type: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    # 'calendar_event', 'form29', etc.

    trigger_event: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    # 'created', 'status_changed', 'due_date_approaching', etc.

    # Condiciones para activar
    trigger_conditions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Template a usar
    notification_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Estado
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Metadata (extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    notification_template: Mapped["NotificationTemplate"] = relationship(
        "NotificationTemplate", back_populates="event_triggers"
    )


class UserNotificationPreference(Base):
    """Preferencias individuales de notificaciones por usuario.

    Permite a usuarios configurar horarios de silencio, categorías silenciadas,
    frecuencia máxima, etc.
    """

    __tablename__ = "user_notification_preferences"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # Relaciones
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Configuración global
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true")
    )

    # Horarios de silencio
    quiet_hours_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    # Días silenciados
    quiet_days: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # ["saturday", "sunday"]

    # Categorías silenciadas
    muted_categories: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # ["system", "low_priority"]

    # Templates silenciados
    muted_templates: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # [template_id_1, template_id_2, ...]

    # Frecuencia máxima
    max_notifications_per_day: Mapped[int] = mapped_column(
        Integer, server_default=text("20")
    )
    min_interval_minutes: Mapped[int] = mapped_column(
        Integer, server_default=text("30")
    )

    # Metadata (extra_metadata to avoid SQLAlchemy reserved name)
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    user: Mapped["Profile"] = relationship("Profile")
    company: Mapped[Optional["Company"]] = relationship("Company")

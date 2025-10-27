"""Calendar and tax event models for Fizko platform."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .company import Company
    from .user import Profile


class EventTemplate(Base):
    """Plantilla global de eventos tributarios.

    Representa los diferentes tipos de obligaciones tributarias que existen
    en Chile (F29, F22, Previred, etc.). Este catálogo es compartido por
    todas las empresas. Un template define la estructura y configuración
    base que se usa para generar eventos concretos.
    """

    __tablename__ = "event_templates"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Identificación
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Clasificación
    category: Mapped[str] = mapped_column(
        Enum(
            'impuesto_mensual',
            'impuesto_anual',
            'prevision',
            'declaracion_jurada',
            'libros',
            'otros',
            name='event_category',
            schema='public'
        ),
        nullable=False
    )
    authority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Aplicabilidad
    is_mandatory: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    applies_to_regimes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Configuración por defecto
    default_recurrence: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Metadata adicional
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company_events: Mapped[list["CompanyEvent"]] = relationship(
        "CompanyEvent", back_populates="event_template", cascade="all, delete-orphan"
    )
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        "CalendarEvent", back_populates="event_template"
    )


class CompanyEvent(Base):
    """Relación entre empresas y plantillas de eventos.

    Vincula una empresa con un template de evento tributario específico
    (ej: "Empresa X tiene activo el evento F29"). Esta relación determina
    qué eventos tributarios aplican a cada empresa. A partir de esta
    relación se generan las instancias concretas en calendar_events.
    """

    __tablename__ = "company_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Relaciones
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    event_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False
    )

    # Configuración
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    # Configuraciones personalizadas (solo para casos edge)
    # Por defecto debe estar vacío {}. La configuración viene de event_template.
    custom_config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="company_events")
    event_template: Mapped["EventTemplate"] = relationship("EventTemplate", back_populates="company_events")
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        "CalendarEvent", back_populates="company_event", cascade="all, delete-orphan"
    )


class CalendarEvent(Base):
    """Instancia concreta de un evento en el calendario.

    Representa una ocurrencia específica de una obligación tributaria
    para una empresa y fecha determinada (ej: "F29 Octubre 2025 vence 12-Nov-2025").
    Contiene el estado, notas, y datos específicos de cumplimiento de la empresa.
    """

    __tablename__ = "calendar_events"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Relaciones
    company_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("company_events.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    event_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False
    )

    # Información del evento
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Fechas
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Estado
    status: Mapped[str] = mapped_column(
        Enum(
            'pending',
            'in_progress',
            'completed',
            'overdue',
            'cancelled',
            name='event_status',
            schema='public'
        ),
        server_default=text("'pending'"),
        nullable=False
    )

    # Cumplimiento
    completion_date: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    completion_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Metadata adicional
    auto_generated: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    company_event: Mapped["CompanyEvent"] = relationship("CompanyEvent", back_populates="calendar_events")
    company: Mapped["Company"] = relationship("Company", back_populates="calendar_events")
    event_template: Mapped["EventTemplate"] = relationship("EventTemplate", back_populates="calendar_events")
    tasks: Mapped[list["EventTask"]] = relationship(
        "EventTask", back_populates="calendar_event", cascade="all, delete-orphan"
    )
    history: Mapped[list["EventHistory"]] = relationship(
        "EventHistory", back_populates="calendar_event", cascade="all, delete-orphan", order_by="EventHistory.created_at.desc()"
    )


class EventTask(Base):
    """Tarea específica dentro de un evento del calendario.

    Representa acciones individuales que deben completarse dentro de un evento
    (ej: "Calcular IVA", "Presentar Formulario", "Realizar Pago").
    """

    __tablename__ = "event_tasks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Relación
    calendar_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False
    )

    # Información de la tarea
    task_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Orden y estado
    order_index: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    status: Mapped[str] = mapped_column(
        Enum(
            'pending',
            'in_progress',
            'completed',
            'skipped',
            name='task_status',
            schema='public'
        ),
        server_default=text("'pending'"),
        nullable=False
    )

    # Automatización
    is_automated: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    automation_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Resultado
    completion_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    calendar_event: Mapped["CalendarEvent"] = relationship("CalendarEvent", back_populates="tasks")


class EventDependency(Base):
    """Dependencias entre tipos de eventos.

    Define relaciones entre eventos tributarios
    (ej: F22 requiere que F29 esté completo).
    """

    __tablename__ = "event_dependencies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Relaciones
    event_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False
    )
    depends_on_event_template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False
    )

    # Tipo de dependencia
    dependency_type: Mapped[str] = mapped_column(Text, nullable=False)  # 'blocks', 'suggests', 'requires_data'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    __table_args__ = (
        CheckConstraint("event_template_id != depends_on_event_template_id", name="different_event_templates"),
    )


class EventHistory(Base):
    """Historial de eventos y acciones en un evento del calendario.

    Registra todas las acciones, cambios de estado, notas y eventos
    relacionados con un evento del calendario para mantener un contexto
    completo y auditable.
    """

    __tablename__ = "event_history"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # Relación
    calendar_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=False
    )

    # Usuario que realizó la acción (opcional, puede ser sistema automático)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True
    )

    # Tipo de evento/acción
    event_type: Mapped[str] = mapped_column(
        Enum(
            'created',           # Evento creado
            'status_changed',    # Cambio de estado
            'note_added',        # Nota agregada
            'document_attached', # Documento adjunto
            'task_completed',    # Tarea completada
            'reminder_sent',     # Recordatorio enviado
            'updated',           # Actualización general
            'completed',         # Evento completado
            'cancelled',         # Evento cancelado
            'system_action',     # Acción automática del sistema
            name='event_history_type',
            schema='public'
        ),
        nullable=False
    )

    # Título/resumen del evento
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Descripción detallada (opcional)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Datos adicionales en formato JSON
    # Puede contener: cambios específicos, datos del documento, etc.
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("NOW()")
    )

    # Relationships
    calendar_event: Mapped["CalendarEvent"] = relationship("CalendarEvent", back_populates="history")
    user: Mapped[Optional["Profile"]] = relationship("Profile")

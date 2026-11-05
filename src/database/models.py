from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Competencia(Base):
    __tablename__ = "competencias"
    id: Mapped[int] = mapped_column(primary_key=True)
    referencia: Mapped[str | None] = mapped_column(String(7), nullable=True)
    arquivo: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    importado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(20))
    origem: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("referencia", "sha256"),)


class Procedimento(Base):
    __tablename__ = "procedimentos"
    id: Mapped[int] = mapped_column(primary_key=True)
    competencia_id: Mapped[int] = mapped_column(ForeignKey("competencias.id"))
    codigo: Mapped[str] = mapped_column(String(10))
    nome: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    identificacao_original: Mapped[str] = mapped_column(Text)
    atributos: Mapped[dict] = mapped_column(JSON, default=dict)
    linha_origem: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("competencia_id", "codigo"), Index("ix_procedimentos_codigo", "codigo"))


class Cid(Base):
    __tablename__ = "cids"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(12), unique=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    fonte_descricao: Mapped[str | None] = mapped_column(Text)


class ProcedimentoCid(Base):
    __tablename__ = "procedimento_cid"
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), primary_key=True)
    cid_id: Mapped[int] = mapped_column(ForeignKey("cids.id"), primary_key=True)
    tipo: Mapped[str] = mapped_column(String(12), primary_key=True)
    competencia_id: Mapped[int] = mapped_column(ForeignKey("competencias.id"))
    __table_args__ = (CheckConstraint("tipo IN ('principal', 'secundario')"), Index("ix_procedimento_cid_cid", "cid_id"))


class Opm(Base):
    __tablename__ = "opms"
    id: Mapped[int] = mapped_column(primary_key=True)
    competencia_id: Mapped[int] = mapped_column(ForeignKey("competencias.id"))
    codigo: Mapped[str] = mapped_column(String(30))
    nome: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("competencia_id", "codigo"),)


class ProcedimentoOpm(Base):
    __tablename__ = "procedimento_opm"
    id: Mapped[int] = mapped_column(primary_key=True)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"))
    opm_id: Mapped[int] = mapped_column(ForeignKey("opms.id"))
    competencia_id: Mapped[int] = mapped_column(ForeignKey("competencias.id"))
    tipo: Mapped[str] = mapped_column(String(60))
    limite_quantidade: Mapped[int | None] = mapped_column(Integer)
    regras: Mapped[dict] = mapped_column(JSON, default=dict)
    fonte: Mapped[str] = mapped_column(Text)
    pendencia: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("procedimento_id", "opm_id", "tipo", "competencia_id", "fonte"), CheckConstraint("limite_quantidade IS NULL OR limite_quantidade >= 0"))


class Especialidade(Base):
    __tablename__ = "especialidades"
    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)


class EspecialidadeProcedimento(Base):
    __tablename__ = "especialidade_procedimento"
    especialidade_id: Mapped[int] = mapped_column(ForeignKey("especialidades.id"), primary_key=True)
    procedimento_id: Mapped[int] = mapped_column(ForeignKey("procedimentos.id"), primary_key=True)
    fonte: Mapped[str] = mapped_column(Text)

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class Site(Base):
    """A storefront sharing the same database/organization as other sites
    (e.g. 'chemisto', 'chemisto-food'). Products and users each belong to
    exactly one site, so the chatbot/voice agent and customer accounts never
    cross between storefronts."""

    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="site")  # type: ignore
    users: Mapped[list["User"]] = relationship("User", back_populates="site")  # type: ignore

    def __repr__(self) -> str:
        return f"<Site id={self.id} slug={self.slug}>"

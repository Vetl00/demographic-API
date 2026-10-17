from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Region(Base):
    """Model representing geographical regions or countries."""

    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)

    records = relationship(
        "DemographicRecord",
        back_populates="region",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Region(name='{self.name}')>"


class DemographicRecord(Base):
    """Model representing demographic indicators using an EAV schema."""

    __tablename__ = "demographic_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    indicator_type = Column(String(50), nullable=False)
    age_category = Column(String(100), nullable=False)
    value = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "year",
            "indicator_type",
            "age_category",
            name="uq_region_year_indicator_age",
        ),
    )

    region = relationship("Region", back_populates="records")

    def __repr__(self):
        return (
            f"<DemographicRecord(year={self.year}, "
            f"indicator='{self.indicator_type}', age='{self.age_category}', "
            f"value={self.value})>"
        )

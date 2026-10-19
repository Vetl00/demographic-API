from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import Country, DemographicRecord, Region


app = FastAPI(
    title="Demographic Pipeline API",
    description="API for regional demographic data.",
    version="1.0.0",
)


class CountryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class RegionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: CountryResponse


class DemographicRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    year: int
    indicator_type: str
    age_category: str
    value: float | None


class DemographicsResponse(BaseModel):
    region: RegionResponse
    items: list[DemographicRecordResponse]
    total: int = Field(ge=0)
    year: int | None = None
    indicator_type: str | None = None
    age_category: str | None = None


class HealthResponse(BaseModel):
    status: str
    database: str


class IndicatorResponse(BaseModel):
    code: str
    record_count: int = Field(ge=0)


class YearsResponse(BaseModel):
    years: list[int]


class RegionSummaryResponse(BaseModel):
    region: RegionResponse
    years: list[int]
    indicators: list[str]
    records_count: int = Field(ge=0)


def get_region_or_404(database: Session, region_id: int) -> Region:
    region = database.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@app.get("/health", response_model=HealthResponse)
def health_check(database: Annotated[Session, Depends(get_db)],) -> HealthResponse:
    """Check the health of the API and database connection."""
    try:
        database.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from error
    return HealthResponse(status="ok", database="ok")


@app.get("/indicators", response_model=list[IndicatorResponse])
def list_indicators(database: Annotated[Session, Depends(get_db)],) -> list[IndicatorResponse]:
    """List all available indicators."""
    indicators = (
        database.query(
            DemographicRecord.indicator_type,
            func.count(DemographicRecord.id).label("record_count"),
        )
        .group_by(DemographicRecord.indicator_type)
        .order_by(DemographicRecord.indicator_type)
        .all()
    )
    return [
        IndicatorResponse(code=code, record_count=record_count)
        for code, record_count in indicators
    ]


@app.get("/years", response_model=YearsResponse)
def list_years(database: Annotated[Session, Depends(get_db)],) -> YearsResponse:
    """List all available years."""
    years = (
        database.query(DemographicRecord.year)
        .distinct()
        .order_by(DemographicRecord.year)
        .all()
    )
    return YearsResponse(years=[year for (year,) in years])


@app.get("/countries", response_model=list[CountryResponse])
def list_countries(database: Annotated[Session, Depends(get_db)],) -> list[Country]:
    """List all available countries."""
    return database.query(Country).order_by(Country.name).all()


@app.get("/regions", response_model=list[RegionResponse])
def list_regions(
    database: Annotated[Session, Depends(get_db)],
    country_code: Annotated[
        str | None, Query(min_length=2, max_length=2, pattern="^[A-Z]{2}$")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Region]:
    """List all available regions, optionally filtered by country code (SE or CZ)."""
    regions_query = database.query(Region)
    if country_code is not None:
        regions_query = regions_query.join(Region.country).filter(
            Country.code == country_code
        )
    return regions_query.order_by(Region.name).offset(offset).limit(limit).all()


@app.get("/regions/{region_id}/demographics",response_model=DemographicsResponse,)
def get_demographics(
    region_id: int,
    database: Annotated[Session, Depends(get_db)],
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    indicator_type: Annotated[str | None, Query(min_length=1, max_length=50)] = None,
    age_category: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DemographicsResponse:
    """Get demographic data for a specific region."""
    region = get_region_or_404(database, region_id)
    records_query = database.query(DemographicRecord).filter(
        DemographicRecord.region_id == region_id
    )
    if year is not None:
        records_query = records_query.filter(DemographicRecord.year == year)
    if indicator_type is not None:
        records_query = records_query.filter(
            DemographicRecord.indicator_type == indicator_type
        )
    if age_category is not None:
        records_query = records_query.filter(
            DemographicRecord.age_category == age_category
        )

    total = records_query.count()
    records = (
        records_query.order_by(
            DemographicRecord.year,
            DemographicRecord.indicator_type,
            DemographicRecord.age_category,
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return DemographicsResponse(
        region=RegionResponse.model_validate(region),
        items=[DemographicRecordResponse.model_validate(record) for record in records],
        total=total,
        year=year,
        indicator_type=indicator_type,
        age_category=age_category,
    )


@app.get("/regions/{region_id}/summary", response_model=RegionSummaryResponse,)
def get_region_summary(
    region_id: int,
    database: Annotated[Session, Depends(get_db)],
) -> RegionSummaryResponse:
    """Get a summary of available data for a specific region."""
    region = get_region_or_404(database, region_id)
    years = (
        database.query(DemographicRecord.year)
        .filter(DemographicRecord.region_id == region_id)
        .distinct()
        .order_by(DemographicRecord.year)
        .all()
    )
    indicators = (
        database.query(DemographicRecord.indicator_type)
        .filter(DemographicRecord.region_id == region_id)
        .distinct()
        .order_by(DemographicRecord.indicator_type)
        .all()
    )
    records_count = database.query(DemographicRecord).filter(
        DemographicRecord.region_id == region_id
    ).count()
    return RegionSummaryResponse(
        region=RegionResponse.model_validate(region),
        years=[year for (year,) in years],
        indicators=[indicator for (indicator,) in indicators],
        records_count=records_count,
    )



from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database import get_db
from models import DemographicRecord, Region


app = FastAPI(
    title="Demographic Pipeline API",
    description="API for regional demographic data.",
    version="1.0.0",
)


class RegionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


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


class GeoJSONGeometry(BaseModel):
    type: str = Field(
        pattern="^(Point|MultiPoint|LineString|MultiLineString|Polygon|MultiPolygon)$"
    )
    coordinates: list


class GeoJSONFeatureProperties(BaseModel):
    region_id: int
    region_name: str


class GeoJSONFeature(BaseModel):
    type: str = Field(default="Feature", pattern="^Feature$")
    properties: GeoJSONFeatureProperties
    geometry: GeoJSONGeometry


def get_region_or_404(database: Session, region_id: int) -> Region:
    region = database.get(Region, region_id)
    if region is None:
        raise HTTPException(status_code=404, detail="Region not found")
    return region


@app.get("/regions", response_model=list[RegionResponse])
def list_regions(
    database: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Region]:
    return (
        database.query(Region)
        .order_by(Region.name)
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get(
    "/regions/{region_id}/demographics",
    response_model=DemographicsResponse,
)
def get_demographics(
    region_id: int,
    database: Annotated[Session, Depends(get_db)],
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DemographicsResponse:
    region = get_region_or_404(database, region_id)
    records_query = database.query(DemographicRecord).filter(
        DemographicRecord.region_id == region_id
    )
    if year is not None:
        records_query = records_query.filter(DemographicRecord.year == year)

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
    )


@app.get("/regions/{region_id}/geometry", response_model=GeoJSONFeature)
def get_geometry(
    region_id: int,
    database: Annotated[Session, Depends(get_db)],
) -> GeoJSONFeature:
    get_region_or_404(database, region_id)
    raise HTTPException(
        status_code=404,
        detail="Geometry not found for this region",
    )
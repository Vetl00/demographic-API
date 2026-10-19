import csv
import logging
import os

from models import Country, DemographicRecord, Region


def load_csv_data(
    session,
    filepath,
    indicator_type,
    region_col,
    country_resolver,
    year_col="TIME_PERIOD",
    value_col="OBS_VALUE",
    age_col="age_category",
    commit=True,
):

    """Read a CSV file and load its data into the database."""

    if not os.path.exists(filepath):
        logging.warning(f"File {filepath} not found. Skipping.")
        return

    logging.info(f"Loading data from {filepath} (Indicator: {indicator_type})...")
    existing_countries = {
        country.code: country for country in session.query(Country).all()
    }
    existing_regions = {region.name: region for region in session.query(Region).all()}
    new_regions = {}
    records_to_add = []

    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required_columns = [region_col, year_col, value_col, age_col]
        if not reader.fieldnames or not all(
            column in reader.fieldnames for column in required_columns
        ):
            logging.error(
                f"File {filepath} is missing required columns: "
                f"{', '.join(required_columns)}. Found: {reader.fieldnames}"
            )
            return

        for row in reader:
            region_name = row[region_col].strip()
            country_code, country_name = country_resolver(region_name)

            if country_code not in existing_countries:
                country = Country(code=country_code, name=country_name)
                session.add(country)
                session.flush()
                existing_countries[country_code] = country
            else:
                country = existing_countries[country_code]

            if region_name in existing_regions:
                region = existing_regions[region_name]
            elif region_name in new_regions:
                region = new_regions[region_name]
            else:
                region = Region(name=region_name, country=country)
                session.add(region)
                new_regions[region_name] = region
                session.flush()

            try:
                # Parse year, age category, and value, handling potential conversion errors
                year = int(row[year_col])
                age_category = row[age_col].strip()
                value_str = row[value_col].strip()
                value = float(value_str) if value_str else None
                records_to_add.append(
                    DemographicRecord(
                        region_id=region.id,
                        year=year,
                        indicator_type=indicator_type,
                        age_category=age_category,
                        value=value,
                    )
                )
            except ValueError as error:
                logging.debug(f"Skipped row due to numeric parse error: {row} - {error}")

    for record in records_to_add:
        session.merge(record)

    if records_to_add and commit:
        session.commit()

    logging.info(f"Successfully processed {len(records_to_add)} records from {filepath}.")
import logging
import os

from .database import get_db, init_db
from .data_loader import load_csv_data
from .models import Country, DemographicRecord, Region


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


FILES_TO_PROCESS = {
    os.path.join("data", "fert.csv"): ("fertility", "region_std", "OBS_VALUE"),
    os.path.join("data", "migration.csv"): ("migration", "geo", "OBS_VALUE"),
    os.path.join("data", "mort.csv"): ("mortality", "region_std", "T:Total"),
    os.path.join("data", "aging.csv"): ("aging", "region_std", "T:Total"),
}

CZECH_REGIONS = frozenset(
    {
        "JIHOMORAVSKÝ",
        "JIHOČESKÝ",
        "KARLOVARSKÝ",
        "KRAJ VYSOČINA",
        "KRÁLOVÉHRADECKÝ",
        "LIBERECKÝ",
        "MORAVSKOSLEZSKÝ",
        "OLOMOUCKÝ",
        "PARDUBICKÝ",
        "PLZEŇSKÝ",
        "PRAGUE",
        "STŘEDOČESKÝ",
        "ÚSTECKÝ",
        "ZLÍNSKÝ",
    }
)

SWEDISH_REGIONS = frozenset(
    {
        "BLEKINGE",
        "DALARNA",
        "GOTLAND",
        "GÄVLEBORG",
        "HALLAND",
        "JÄMTLAND",
        "JÖNKÖPING",
        "KALMAR",
        "KRONOBERG",
        "NORRBOTTEN",
        "OREBRO",
        "SKÅNE",
        "STOCKHOLM",
        "SÖDERMANLAND",
        "UPPSALA",
        "VÄRMLAND",
        "VÄSTERBOTTEN",
        "VÄSTERNORRLAND",
        "VÄSTMANLAND",
        "VÄSTRA GÖTALAND",
        "ÖSTERGÖTLAND",
    }
)


def get_country(region_name):
    normalized_name = region_name.strip().upper()
    if normalized_name in CZECH_REGIONS or normalized_name == "CZECHIA":
        return "CZ", "Czechia"
    if normalized_name in SWEDISH_REGIONS or normalized_name == "SWEDEN":
        return "SE", "Sweden"
    raise ValueError(f"Unknown country for region: {region_name}")


def seed_database():
    """Populate an empty database from the demographic CSV files."""
    init_db()

    database_generator = get_db()
    database = next(database_generator)

    try:
        if (
            database.query(Country).first()
            or database.query(Region).first()
            or database.query(DemographicRecord).first()
        ):
            logging.info("Database is not empty. Seeding skipped.")
            return

        missing_files = [filename for filename in FILES_TO_PROCESS if not os.path.exists(filename)]
        if missing_files:
            raise FileNotFoundError(
                "Required CSV files not found: " + ", ".join(missing_files)
            )
		# Load data from each CSV file
        for filename, (indicator, region_col, value_col) in FILES_TO_PROCESS.items():
            load_csv_data(
                session=database,
                filepath=filename,
                indicator_type=indicator,
                region_col=region_col,
                country_resolver=get_country,
                year_col="TIME_PERIOD",
                value_col=value_col,
                age_col="age_category",
                commit=False,
            )
		# Commit all changes to the database after processing all files
        database.commit()
        logging.info("Database seeded successfully.")
    except Exception:
        database.rollback()
        logging.exception("Database seeding failed. All changes were rolled back.")
        raise
    finally:
        database_generator.close()


if __name__ == "__main__":
    seed_database()

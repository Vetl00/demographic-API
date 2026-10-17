import logging
import os

from database import get_db, init_db
from data_loader import load_csv_data
from models import DemographicRecord, Region


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


FILES_TO_PROCESS = {
    "fert.csv": ("fertility", "region_std", "OBS_VALUE"),
    "migration.csv": ("migration", "geo", "OBS_VALUE"),
    "mort.csv": ("mortality", "region_std", "T:Total"),
    "aging.csv": ("aging", "region_std", "T:Total"),
}


def seed_database():
    """Populate an empty database from the demographic CSV files."""
    init_db()

    database_generator = get_db()
    database = next(database_generator)

    try:
        if database.query(Region).first() or database.query(DemographicRecord).first():
            logging.info("Database is not empty. Seeding skipped.")
            return

        missing_files = [filename for filename in FILES_TO_PROCESS if not os.path.exists(filename)]
        if missing_files:
            raise FileNotFoundError(
                "Required CSV files not found: " + ", ".join(missing_files)
            )

        for filename, (indicator, region_col, value_col) in FILES_TO_PROCESS.items():
            load_csv_data(
                session=database,
                filepath=filename,
                indicator_type=indicator,
                region_col=region_col,
                year_col="TIME_PERIOD",
                value_col=value_col,
                age_col="age_category",
                commit=False,
            )

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

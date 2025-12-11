import logging
from src.models.base import init_db, SessionLocal
from src.clients.fiindo_client import FiindoClient
from src.services.etl import ETLService
from src.core.config import settings

from src.core.logging import setup_logging  

def main():
    # Setup Logging
    setup_logging(settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("Starting Fiindo ETL Challenge")

    # Init db
    init_db()
    logger.info("Database initialized")

    # Create db session
    db = SessionLocal()

    try:
        # Initialize Fiindo client
        client = FiindoClient()

        # Initialize ETL service
        etl_service = ETLService(db=db, client=client)

        # Run etl
        summary = etl_service.run()

        # Print summary
        logger.info("ETL completed successfully: %s", summary)
        print(summary)

    except Exception as e:
        logger.exception("ETL pipeline failed: %s", e)
    finally:
        db.close()
        logger.info("Database session closed")

if __name__ == "__main__":
    main()

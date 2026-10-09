import os
import time

import psycopg

MAX_ATTEMPTS = 20
SLEEP_SECONDS = 2


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    if database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with psycopg.connect(database_url):
                print("Database is ready")
                return
        except psycopg.OperationalError as exc:
            print(f"Database not ready (attempt {attempt}/{MAX_ATTEMPTS}): {exc}")
            if attempt == MAX_ATTEMPTS:
                raise
            time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()

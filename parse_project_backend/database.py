from sqlalchemy import create_engine

engine = create_engine(f"postgresql+psycopg2://postgres:root@parse_project_database:7654/parse_project_database")

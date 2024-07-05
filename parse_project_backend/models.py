from sqlalchemy import Table, Column, Integer, String, MetaData, Index

metadata = MetaData()

vacancies_table = Table(
    "vacancies",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("hh_id", Integer, unique=True),
    Column("name", String),
    Column("description", String, nullable=True),
    Column("salary_from", Integer, nullable=True),
    Column("salary_to", Integer, nullable=True),
    Column("currency", String, nullable=True),
    Column("employer", String, nullable=True),
    Column("employment_status", String, nullable=True),
    Column("work_experience", String),
    Column("city", String, nullable=True)
)

name_index = Index("name_idx", vacancies_table.c.name)
id_index = Index("id_idx", vacancies_table.c.hh_id)
city_index = Index("city_idx", vacancies_table.c.city)
work_experience_index = Index("work_experience_idx", vacancies_table.c.work_experience)
employment_status_index = Index("employment_status_idx", vacancies_table.c.employment_status)

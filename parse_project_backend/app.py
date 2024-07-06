from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import requests
from sqlalchemy import insert, select, update, delete, or_
import re
from models import vacancies_table, metadata
from schema import VacancyFilter
from typing import Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from secret import CLIENT_ID, CLIENT_SECRET
from apscheduler.triggers.interval import IntervalTrigger

access_token = None


def update_vacancies():
    with engine.connect() as conn:
        query = select(vacancies_table)
        vacancies = conn.execute(query).fetchall()
        if not vacancies:
            return
        for vacancy in vacancies:
            hh_ru_vacancy = requests.get(f"https://api.hh.ru/vacancies/{vacancy[1]}").json()
            if hh_ru_vacancy.get("name"):
                name = hh_ru_vacancy.get("name")
            else:
                name = vacancy[2]
            if hh_ru_vacancy.get("archived"):
                stmt = delete(vacancies_table).where(vacancies_table.c.hh_id == vacancy[1])
                conn.execute(stmt)
                conn.commit()
                continue
            description = hh_ru_vacancy.get("description")
            if description is not None:
                description = re.sub(r"<.*?>", "", description).strip()
            else:
                description = vacancy[3]
            salary_from = vacancy[4]
            salary_to = vacancy[5]
            currency = vacancy[6]
            if hh_ru_vacancy.get("salary"):
                salary_from = hh_ru_vacancy.get("salary", {}).get("from")
                salary_to = hh_ru_vacancy.get("salary", {}).get("to")
                currency = hh_ru_vacancy.get("salary", {}).get("currency")
            if hh_ru_vacancy.get("area"):
                city = hh_ru_vacancy.get("area", {}).get("name")
            else:
                city = vacancy[10]
            query = update(vacancies_table).where(vacancies_table.c.id == vacancy[0]).values(
                name=name,
                description=description,
                salary_from=salary_from,
                salary_to=salary_to,
                currency=currency,
                employer=hh_ru_vacancy.get("employer", {}).get("name"),
                employment_status=hh_ru_vacancy.get("employment", {}).get("name"),
                work_experience=hh_ru_vacancy.get("experience", {}).get("name"),
                city=city
            )
            conn.execute(query)
            conn.commit()


def update_access_token():
    global access_token
    response = requests.post("https://api.hh.ru/token", params={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }).json()
    access_token = response.get("access_token")


async def lifespan(app):
    metadata.create_all(engine)
    access_token_scheduler = BackgroundScheduler()
    access_token_scheduler.add_job(update_access_token, IntervalTrigger(minutes=10))
    access_token_scheduler.start()
    vacancy_update_scheduler = BackgroundScheduler()
    vacancy_update_scheduler.add_job(update_vacancies, IntervalTrigger(hours=12))
    vacancy_update_scheduler.start()
    response = requests.post("https://api.hh.ru/token", params={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }).json()
    global access_token
    access_token = response.get("access_token")
    yield


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все методы
    allow_headers=["*"],  # Разрешить все заголовки
)


def add_vacancy(params):
    global access_token
    if access_token is not None:
        hh_ru_vacancies = requests.get("https://api.hh.ru/vacancies", params=params, headers={"Authorization": f"Bearer {access_token}"})
        vacancies_dict = hh_ru_vacancies.json()
        for vacancy in vacancies_dict["items"]:
            if vacancy.get("archived"):
                continue
            salary_from = None
            salary_to = None
            currency = None
            if vacancy.get("salary"):
                salary_from = vacancy.get("salary", {}).get("from")
                salary_to = vacancy.get("salary", {}).get("to")
                currency = vacancy.get("salary", {}).get("currency")

            city = None
            if vacancy.get("area"):
                city = vacancy.get("area", {}).get("name")

            description = None
            if vacancy.get("snippet"):
                requirement = vacancy.get("snippet").get("requirement")
                responsibility = vacancy.get("snippet").get("responsibility")
                description = (requirement + " " if requirement else "") + (responsibility if responsibility else "")
                description = re.sub(r"<.+>", "", description)
            with engine.connect() as conn:
                query = select(vacancies_table).where(vacancies_table.c.hh_id == int(vacancy.get("id")))
                res = conn.execute(query).fetchall()
                if res:
                    continue
                stmt = insert(vacancies_table).values(
                    name=vacancy.get("name").lower(),
                    hh_id=vacancy.get("id"),
                    description=description.lower().strip(),
                    salary_from=salary_from,
                    salary_to=salary_to,
                    currency=currency,
                    employer=vacancy.get("employer", {}).get("name"),
                    employment_status=vacancy.get("employment", {}).get("name"),
                    work_experience=vacancy.get("experience", {}).get("name"),
                    city=city
                )
                conn.execute(stmt)
                conn.commit()


@app.get("/vacancy", response_model=List[VacancyFilter])
def get_vacancy(name: Optional[str] = None, salary_from: Optional[int] = None,
                salary_to: Optional[int] = None, employment_status: Optional[str] = None,
                work_experience: Optional[str] = None, employer: Optional[str] = None, city: Optional[str] = None):
    with engine.connect() as conn:
            query = select(vacancies_table)
            if name:
                query = query.where(or_(vacancies_table.c.name.like(f"%{name.lower()}%"),
                                                      vacancies_table.c.description.like(f"%{name.lower}%")))
            if salary_from:
                query = query.where(vacancies_table.c.salary_from >= salary_from)
            if salary_to:
                query = query.where(vacancies_table.c.salary_to <= salary_to)
            if employment_status:
                query = query.where(vacancies_table.c.employment_status == employment_status)
            if work_experience:
                query = query.where(vacancies_table.c.work_experience == work_experience)
            if employer:
                query = query.where(vacancies_table.c.employer == employer)
            if city:
                query = query.where(vacancies_table.c.city == city)
            try:
                result = conn.execute(query).fetchall()
                if not result:
                    params = {
                        "text": name,
                        "salary_from": salary_from,
                        "salary_to": salary_to,
                        "employment_status": employment_status,
                        "work_experience": work_experience,
                        "employer": employer,
                        "city": city
                    }
                    params = {k: v for k, v in params.items() if v is not None}
                    add_vacancy(params)
                    result = conn.execute(query).fetchall()
                vacancies = [dict(vacancy._mapping) for vacancy in result]
                if vacancies:
                    return vacancies
                else:
                    raise HTTPException(status_code=202, detail={"vacancy not found"})
            except Exception as e:
                raise HTTPException(status_code=501, detail=str(e))

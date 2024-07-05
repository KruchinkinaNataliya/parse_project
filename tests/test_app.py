import pytest
import requests


def test_get_vacancy_without_name():
    response = requests.get("http://localhost:8000/vacancy")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("name", [
    "java",
    "Golang",
    "сантехник",
    "репетитор",
    "Backend developer",
    "junior frontend"
])
def test_get_vacancy_with_name_without_filter(name):
    response = requests.get(f"http://localhost:8000/vacancy?name={name}")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("name, salary_from, salary_to, employment_status,"
                         "work_experience, employer, city", [
                             ("java", 20000, None, None, None, None, None),
                             ("грузчик", 60000, 80000, None, None, None, "Барнаул"),
                             ("сантехник", 57000, 90000, "Полная занятость", "От 1 года до 3 лет", "WILDBERRIES", "Рязань"),

                         ])
def test_get_vacancy_with_name_with_filter(name: str, salary_from: int, salary_to: int, employment_status: str,
                                           work_experience: str, employer: str, city: str):
    params = {
        "salary_from": salary_from,
        "salary_to": salary_to,
        "employment_status": employment_status,
        "work_experience": work_experience,
        "employer": employer,
        "city": city
    }
    params = {k: v for k, v in params.items() if v is not None}
    response = requests.get(f"http://localhost:8000/vacancy?name={name}", params=params)
    assert response.status_code == 200
    assert response.json() != []

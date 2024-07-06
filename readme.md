### Инструкция по использованию и настройке

### 1. Создание файлов

- #### Создадите файл secret.py в папке parse_project_backend:
    CLIENT_ID, CLIENT_SECRET - данные выданные приложению от Hh.ru API

            CLIENT_ID=""
            CLIENT_SECRET=""

  - #### Создадите файл secret.py в папке parse_project_backend:
      API_TOKEN - токен телеграмм бота
        
            API_TOKEN=""


- #### 2. Создание образов контейнеров
  - В папке parse_project_backend пишем команду

        docker build -t parse_project_backend .
    
  - В папке telegram_bot пишем команду
    
          docker build -t telegram_bot .

  - #### 3. Запуск Docker контейнеров
    В корневой папке проекта пишем 
  
          docker-compose up


- #### 4. Обращение к поиску вакансий

  Сервис по поиску вакансий работает по адресу:
    
      localhost:8000/vacancy

  На вход по методу GET могут передаваться параметры:
      
      { "name": название вакансии (str),
        "salary_from": зарплата от (int),
        "salary_to": зарплата до (int),
        "city": город (str),
        "work_experience": опыт работы(str),
        "employment_type": тип занятости (str),
        "employer": работодатель (str)}:
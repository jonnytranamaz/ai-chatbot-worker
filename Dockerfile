FROM python:3.10

WORKDIR /app

COPY . /app

COPY requirements.test2.txt .

RUN pip install --no-cache-dir -r requirements.test2.txt

RUN pip install --no-cache-dir rasa

COPY . .

EXPOSE 9009

ENV DATABASE_URL=postgres://postgres:Intern2024@192.168.1.45:5432/amaz_ai_chatbot

CMD ["python", "manage.py", "runserver", "0.0.0.0:9009"]

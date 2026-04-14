FROM python:3.12-slim
WORKDIR /comp7940-lab
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "CHATBOT1.py"]
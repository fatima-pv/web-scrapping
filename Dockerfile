FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Establecer directorio de trabajo
WORKDIR /var/task

# Copiar archivos de la función
COPY scrap_sismos.py .
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Configurar el handler de Lambda
CMD ["scrap_sismos.lambda_handler"]
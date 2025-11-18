# Imagen de Playwright con Python (incluye navegadores y deps)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Directorio donde vivirá la función dentro del contenedor
ARG FUNCTION_DIR="/function"

# Crear directorio de la función
RUN mkdir -p ${FUNCTION_DIR}
WORKDIR ${FUNCTION_DIR}

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias de Python + runtime de Lambda
RUN pip install --no-cache-dir -r requirements.txt awslambdaric

# (Opcional: asegurar que los navegadores estén listos)
# RUN playwright install chromium
# RUN playwright install-deps chromium

# Copiar el código de la función
COPY scrap_sismos.py ${FUNCTION_DIR}

# Lambda usará el runtime interface client
ENTRYPOINT ["/usr/local/bin/python", "-m", "awslambdaric"]

# Nombre del handler de tu función
CMD ["scrap_sismos.lambda_handler"]

import json
import boto3
from playwright.sync_api import sync_playwright

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table("TablaSismosIGP")


def lambda_handler(event, context):
    print("Lambda START")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        print("Abriendo página del IGP...")
        page.goto(
            "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados",
            wait_until="domcontentloaded",   # Mucho más rápido que networkidle
            timeout=15000                    # 15s máximo
        )

        # Pequeña espera para que cargue la tabla dinámica
        page.wait_for_timeout(3000)

        print("Extrayendo filas...")
        filas = page.query_selector_all("tbody tr")

        sismos = []

        for fila in filas[:10]:  # Solo los 10 primeros como pide la tarea
            columnas = fila.query_selector_all("td")

            if len(columnas) < 4:
                continue

            referencia = columnas[0].inner_text().strip()
            url_reporte = columnas[0].query_selector("a").get_attribute("href")
            fecha_hora = columnas[1].inner_text().strip()
            magnitud = columnas[2].inner_text().strip()

            item = {
                "referencia": referencia,
                "url_reporte": url_reporte,
                "fecha_hora": fecha_hora,
                "magnitud": magnitud,
            }

            # Guardar en DynamoDB
            tabla.put_item(Item=item)

            sismos.append(item)

        browser.close()

    print("Lambda END")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Sismos guardados correctamente",
            "cantidad": len(sismos),
            "sismos": sismos
        })
    }

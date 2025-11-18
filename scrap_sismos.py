import json
import boto3
from playwright.sync_api import sync_playwright

dynamodb = boto3.resource("dynamodb")
tabla = dynamodb.Table("TablaSismosIGP")

def lambda_handler(event, context):
    print("Lambda START")

    try:
        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--single-process",
                    "--disable-setuid-sandbox"
                ],
            )

            page = browser.new_page()

            page.goto(
                "https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados",
                wait_until="domcontentloaded",
                timeout=15000
            )

            page.wait_for_timeout(3000)

            filas = page.query_selector_all("tbody tr")

            sismos = []

            for fila in filas[:10]:
                columnas = fila.query_selector_all("td")
                if len(columnas) < 4:
                    continue

                referencia = columnas[0].inner_text().strip()
                link = columnas[0].query_selector("a")
                url_reporte = link.get_attribute("href") if link else None
                fecha_hora = columnas[1].inner_text().strip()
                magnitud = columnas[2].inner_text().strip()

                item = {
                    "id": referencia,
                    "referencia": referencia,
                    "url_reporte": url_reporte,
                    "fecha_hora": fecha_hora,
                    "magnitud": magnitud,
                }

                tabla.put_item(Item=item)
                sismos.append(item)

            browser.close()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Sismos guardados correctamente",
                "cantidad": len(sismos),
                "sismos": sismos,
            })
        }

    except Exception as e:
        print("ERROR:", repr(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

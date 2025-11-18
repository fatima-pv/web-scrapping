import json
import boto3
import uuid
from playwright.sync_api import sync_playwright

def lambda_handler(event, context):
    sismos_data = []
    
    try:
        with sync_playwright() as p:
            # Lanzar navegador en modo headless
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navegar a la página del IGP
            page.goto('https://ultimosismo.igp.gob.pe/ultimo-sismo/sismos-reportados', 
                     wait_until='networkidle', 
                     timeout=30000)
            
            # Esperar a que la tabla se cargue
            page.wait_for_selector('table tbody tr', timeout=10000)
            
            # Extraer las filas de la tabla (primeras 10)
            rows = page.query_selector_all('table tbody tr')[:10]
            
            for row in rows:
                cells = row.query_selector_all('td')
                
                if len(cells) >= 4:
                    # Extraer datos de cada celda
                    referencia = cells[0].inner_text().strip()
                    
                    # Obtener URL del reporte si existe un link
                    link_element = cells[1].query_selector('a')
                    url_reporte = link_element.get_attribute('href') if link_element else ''
                    
                    fecha_hora = cells[2].inner_text().strip()
                    magnitud = cells[3].inner_text().strip()
                    
                    # Construir objeto con los datos del sismo
                    sismo = {
                        'referencia': referencia,
                        'url_reporte': url_reporte,
                        'fecha_hora': fecha_hora,
                        'magnitud': magnitud
                    }
                    
                    sismos_data.append(sismo)
            
            browser.close()
        
        if not sismos_data:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No se encontraron sismos en la tabla'})
            }
        
        # Guardar en DynamoDB
        dynamodb = boto3.resource('dynamodb')
        tabla = dynamodb.Table('TablaSismosIGP')
        
        # Limpiar tabla antes de insertar nuevos datos
        scan = tabla.scan()
        with tabla.batch_writer() as batch:
            for item in scan['Items']:
                batch.delete_item(Key={'id': item['id']})
        
        # Insertar los 10 últimos sismos
        for i, sismo in enumerate(sismos_data):
            sismo['id'] = str(uuid.uuid4())
            sismo['numero'] = i + 1
            tabla.put_item(Item=sismo)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Se guardaron {len(sismos_data)} sismos exitosamente',
                'sismos': sismos_data
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error en el scraping: {str(e)}'
            })
        }
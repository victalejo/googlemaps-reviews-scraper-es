"""
Prueba de scraping para verificar el fix de Redis/RQ.
"""
import requests
import time
import json

API_BASE_URL = "http://localhost:8001"

def test_scraping():
    """Prueba el flujo completo de scraping."""

    print("=" * 60)
    print("PRUEBA DE SCRAPING CON RQ")
    print("=" * 60)

    # 1. Iniciar scraping
    print("\n1. Iniciando job de scraping...")
    url = "https://www.google.com/maps/place/La+BTK+Bellas+Artes/@19.4338211,-99.1455109,17z/data=!3m2!4b1!5s0x85d1f92b275f933b:0xbf641e762a5ca480!4m6!3m5!1s0x85d1f96b83b19901:0xc83c8fcab37f08ab!8m2!3d19.4338211!4d-99.1429306!16s%2Fg%2F11gxvsgx0g"

    payload = {
        "url": url,
        "max_reviews": 5,
        "sort_by": "newest",
        "save_to_db": True
    }

    response = requests.post(f"{API_BASE_URL}/api/scraping/start", json=payload)

    if response.status_code != 202:
        print(f"   ERROR: Status {response.status_code}")
        print(f"   {response.text}")
        return False

    result = response.json()
    job_id = result.get("job_id")
    print(f"   Job ID: {job_id}")
    print(f"   Status: {result.get('status')}")

    # 2. Monitorear status
    print("\n2. Monitoreando progreso del job...")

    max_attempts = 60  # 60 segundos máximo
    for i in range(max_attempts):
        time.sleep(2)

        response = requests.get(f"{API_BASE_URL}/api/scraping/status/{job_id}")

        if response.status_code != 200:
            print(f"   ERROR al consultar status: {response.status_code}")
            print(f"   {response.text}")
            return False

        status_data = response.json()
        status = status_data.get("status")
        progress = status_data.get("progress", "")

        print(f"   [{i*2}s] Status: {status} - {progress}")

        if status == "finished":
            print("\n   Job completado exitosamente!")
            break
        elif status == "failed":
            print(f"\n   ERROR: Job falló - {status_data.get('error')}")
            return False
    else:
        print("\n   TIMEOUT: Job tomó demasiado tiempo")
        return False

    # 3. Obtener resultados
    print("\n3. Obteniendo resultados...")

    response = requests.get(f"{API_BASE_URL}/api/scraping/result/{job_id}")

    if response.status_code != 200:
        print(f"   ERROR: Status {response.status_code}")
        print(f"   {response.text}")
        return False

    result = response.json()
    reviews_count = result.get("reviews_count", 0)
    reviews = result.get("reviews", [])

    print(f"   Reviews obtenidas: {reviews_count}")

    if reviews_count > 0:
        print(f"\n   Primera review:")
        first_review = reviews[0]
        print(f"   - Usuario: {first_review.get('username')}")
        print(f"   - Rating: {first_review.get('rating')}")
        print(f"   - Fecha: {first_review.get('relative_date')}")
        print(f"   - Texto: {first_review.get('caption', '')[:100]}...")

    print("\n" + "=" * 60)
    print("PRUEBA EXITOSA!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_scraping()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

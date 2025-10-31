"""
Script de pruebas de integración para la API.
Ejecutar después de iniciar docker-compose up -d
"""
import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:8001"


def print_test(name: str, success: bool, details: str = ""):
    """Imprime resultado de prueba."""
    status = "PASS" if success else "FAIL"
    print(f"[{status}] {name}")
    if details:
        print(f"      {details}")


def test_health_check():
    """Prueba el endpoint de health check."""
    print("\n=== TEST: Health Check ===")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        success = response.status_code == 200

        if success:
            data = response.json()
            mongodb_ok = data.get("mongodb", False)
            redis_ok = data.get("redis", False)
            print_test("Health endpoint", True, f"MongoDB: {mongodb_ok}, Redis: {redis_ok}")
            return mongodb_ok and redis_ok
        else:
            print_test("Health endpoint", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Health endpoint", False, f"Error: {str(e)}")
        return False


def test_root_endpoint():
    """Prueba el endpoint raíz."""
    print("\n=== TEST: Root Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        success = response.status_code == 200

        if success:
            data = response.json()
            print_test("Root endpoint", True, f"Message: {data.get('message', '')}")
        else:
            print_test("Root endpoint", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("Root endpoint", False, f"Error: {str(e)}")
        return False


def test_create_place():
    """Prueba crear un lugar."""
    print("\n=== TEST: Create Place ===")
    place_data = {
        "client_id": "test_client_001",
        "branch_id": "test_branch_001",
        "url": "https://www.google.com/maps/place/Test+Restaurant",
        "webhook_url": "https://webhook.site/test-endpoint",
        "name": "Test Restaurant",
        "check_interval_minutes": 60,
        "monitoring_enabled": False  # Deshabilitado para pruebas
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/places/",
            json=place_data,
            timeout=10
        )

        if response.status_code in [200, 201]:
            data = response.json()
            place_id = data.get("place_id")
            print_test("Create place", True, f"place_id: {place_id}")
            return place_id
        elif response.status_code == 409:
            print_test("Create place", True, "Place already exists (expected)")
            # Try to get existing place
            return get_existing_place_id(place_data["client_id"], place_data["branch_id"])
        else:
            print_test("Create place", False, f"Status: {response.status_code}, {response.text[:100]}")
            return None
    except Exception as e:
        print_test("Create place", False, f"Error: {str(e)}")
        return None


def get_existing_place_id(client_id: str, branch_id: str):
    """Obtiene el ID de un lugar existente."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/places/",
            params={"client_id": client_id, "branch_id": branch_id},
            timeout=5
        )
        if response.status_code == 200:
            places = response.json()
            if places and len(places) > 0:
                return places[0].get("place_id")
        return None
    except:
        return None


def test_list_places():
    """Prueba listar lugares."""
    print("\n=== TEST: List Places ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/places/", timeout=5)
        success = response.status_code == 200

        if success:
            places = response.json()
            print_test("List places", True, f"Found {len(places)} places")
        else:
            print_test("List places", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("List places", False, f"Error: {str(e)}")
        return False


def test_get_place(place_id: str):
    """Prueba obtener un lugar específico."""
    print("\n=== TEST: Get Place ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/places/{place_id}", timeout=5)
        success = response.status_code == 200

        if success:
            place = response.json()
            print_test("Get place", True, f"Name: {place.get('name', 'N/A')}")
        else:
            print_test("Get place", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("Get place", False, f"Error: {str(e)}")
        return False


def test_monitor_status():
    """Prueba el estado del monitoreo."""
    print("\n=== TEST: Monitor Status ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/monitor/status", timeout=5)
        success = response.status_code == 200

        if success:
            data = response.json()
            monitoring_active = data.get("monitoring_active", False)
            enabled_places = data.get("enabled_places", 0)
            print_test("Monitor status", True, f"Active: {monitoring_active}, Enabled: {enabled_places}")
        else:
            print_test("Monitor status", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("Monitor status", False, f"Error: {str(e)}")
        return False


def test_list_reviews():
    """Prueba listar reseñas."""
    print("\n=== TEST: List Reviews ===")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/reviews/",
            params={"page": 1, "page_size": 10},
            timeout=5
        )
        success = response.status_code == 200

        if success:
            data = response.json()
            total = data.get("total", 0)
            reviews_count = len(data.get("reviews", []))
            print_test("List reviews", True, f"Total: {total}, Current page: {reviews_count}")
        else:
            print_test("List reviews", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("List reviews", False, f"Error: {str(e)}")
        return False


def test_scraping_workers():
    """Prueba el estado de los workers."""
    print("\n=== TEST: Workers Status ===")
    try:
        response = requests.get(f"{API_BASE_URL}/api/scraping/workers/status", timeout=5)
        success = response.status_code == 200

        if success:
            data = response.json()
            total_workers = data.get("total_workers", 0)
            queued_jobs = data.get("queued_jobs", 0)
            print_test("Workers status", True, f"Workers: {total_workers}, Queued jobs: {queued_jobs}")
        else:
            print_test("Workers status", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_test("Workers status", False, f"Error: {str(e)}")
        return False


def test_docs_available():
    """Prueba que la documentación esté disponible."""
    print("\n=== TEST: API Documentation ===")

    docs_ok = False
    redoc_ok = False

    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        docs_ok = response.status_code == 200
        print_test("Swagger UI (/docs)", docs_ok)
    except Exception as e:
        print_test("Swagger UI (/docs)", False, f"Error: {str(e)}")

    try:
        response = requests.get(f"{API_BASE_URL}/redoc", timeout=5)
        redoc_ok = response.status_code == 200
        print_test("ReDoc (/redoc)", redoc_ok)
    except Exception as e:
        print_test("ReDoc (/redoc)", False, f"Error: {str(e)}")

    return docs_ok and redoc_ok


def main():
    """Ejecuta todas las pruebas."""
    print("=" * 60)
    print("GOOGLE MAPS REVIEWS SCRAPER API - INTEGRATION TESTS")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print("")

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0
    }

    # Test 1: Health check
    results["total"] += 1
    if test_health_check():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print("\n⚠️  WARNING: MongoDB or Redis not available. Some tests may fail.")

    # Test 2: Root endpoint
    results["total"] += 1
    if test_root_endpoint():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 3: Documentation
    results["total"] += 1
    if test_docs_available():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 4: Create place
    results["total"] += 1
    place_id = test_create_place()
    if place_id:
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 5: List places
    results["total"] += 1
    if test_list_places():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 6: Get specific place
    if place_id:
        results["total"] += 1
        if test_get_place(place_id):
            results["passed"] += 1
        else:
            results["failed"] += 1

    # Test 7: Monitor status
    results["total"] += 1
    if test_monitor_status():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 8: List reviews
    results["total"] += 1
    if test_list_reviews():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 9: Workers status
    results["total"] += 1
    if test_scraping_workers():
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests:  {results['total']}")
    print(f"Passed:       {results['passed']} ✓")
    print(f"Failed:       {results['failed']} ✗")
    print(f"Success rate: {(results['passed']/results['total']*100):.1f}%")
    print("=" * 60)

    if results["failed"] == 0:
        print("\n🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit(main())

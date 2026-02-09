"""
HTTP test script for journal filtering API.
Tests various filter combinations to ensure they work correctly.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/publications/journals/public/"

def test_api_endpoint(description, params=None):
    """Test a single API endpoint with given parameters"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    
    url = BASE_URL
    if params:
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{BASE_URL}?{param_str}"
    
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if response is paginated (has count, results) or direct list
            if isinstance(data, dict):
                count = data.get('count', 0)
                results = data.get('results', [])
            else:
                # Direct list response
                results = data
                count = len(results)
            
            print(f"✅ Success!")
            print(f"Total results: {count}")
            print(f"Results in this page: {len(results)}")
            
            if results:
                print(f"\nFirst result:")
                first = results[0]
                print(f"  ID: {first.get('id')}")
                print(f"  Title: {first.get('title')}")
                print(f"  Publisher: {first.get('publisher_name')}")
                print(f"  Language: {first.get('language')}")
                print(f"  Open Access: {first.get('is_open_access')}")
                print(f"  Peer Reviewed: {first.get('peer_reviewed')}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Is the server running?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    print("\n" + "="*80)
    print("JOURNAL FILTERING API - HTTP TESTS")
    print("="*80)
    
    # Test 1: Get all journals (no filters)
    test_api_endpoint("Get all journals (no filters)")
    
    # Test 2: Filter by open access
    test_api_endpoint("Filter by open access", {"access_type": "open_access"})
    
    # Test 3: Filter by language
    test_api_endpoint("Filter by language (English)", {"language": "English"})
    
    # Test 4: Filter by peer reviewed
    test_api_endpoint("Filter by peer reviewed", {"peer_reviewed": "true"})
    
    # Test 5: Search functionality
    test_api_endpoint("Search for 'journal'", {"search": "journal"})
    
    # Test 6: Filter by institution name
    test_api_endpoint("Filter by institution name", {"institutions": "External"})
    
    # Test 7: Multiple filters combined
    test_api_endpoint(
        "Combined filters (open access + peer reviewed + English)",
        {
            "access_type": "open_access",
            "peer_reviewed": "true",
            "language": "English"
        }
    )
    
    # Test 8: Filter by impact factor
    test_api_endpoint("Filter by impact factor >= 1.0", {"impact_factor": "1.0"})
    
    # Test 9: Filter by CiteScore
    test_api_endpoint("Filter by CiteScore >= 2.0", {"cite_score": "2.0"})
    
    # Test 10: Filter by category
    test_api_endpoint("Filter by category (science)", {"category": "science"})
    
    print("\n" + "="*80)
    print("HTTP TESTING COMPLETE")
    print("="*80)
    print("\n✅ If all tests show 200 status, the API is working correctly!")
    print("❌ If tests fail, check:")
    print("  1. Django server is running (python manage.py runserver)")
    print("  2. Server is accessible at http://localhost:8000")
    print("  3. Database has journal data")
    print()

if __name__ == "__main__":
    main()

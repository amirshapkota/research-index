"""
Test script for expanded Author and Institution profile endpoints.
Run the Django server before executing this script.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/auth"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_author_profile_update():
    """Test author profile update with expanded fields"""
    print("\n" + "="*60)
    print("TESTING AUTHOR PROFILE UPDATES")
    print("="*60)
    
    print("\nNote: You need to:")
    print("1. Register as an author")
    print("2. Login to get access token")
    print("3. Use the token below\n")
    
    # Replace with actual token from login
    access_token = input("Enter your author access token (or press Enter to skip): ").strip()
    
    if not access_token:
        print("Skipping author profile tests...")
        return
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Get current profile
    response = requests.get(f"{BASE_URL}/profile/author/", headers=headers)
    print_response("1. Get Current Author Profile", response)
    
    # 2. Update profile with expanded fields (using JSON for non-file fields)
    update_data = {
        "degree": "PhD in Computer Science",
        "gender": "male",
        "bio": "Researcher specializing in AI and Machine Learning with 10+ years of experience.",
        "research_interests": "Artificial Intelligence, Machine Learning, Deep Learning, Natural Language Processing",
        "orcid": "0000-0001-2345-6789",
        "google_scholar": "https://scholar.google.com/citations?user=EXAMPLE",
        "researchgate": "https://www.researchgate.net/profile/John-Doe",
        "linkedin": "https://www.linkedin.com/in/johndoe",
        "website": "https://johndoe-research.com"
    }
    
    response = requests.patch(f"{BASE_URL}/profile/author/", json=update_data, headers=headers)
    print_response("2. Update Author Profile (Text Fields)", response)
    
    # 3. Get updated profile
    response = requests.get(f"{BASE_URL}/profile/author/", headers=headers)
    print_response("3. Get Updated Author Profile", response)
    
    print("\n" + "="*60)
    print("FILE UPLOAD INSTRUCTIONS")
    print("="*60)
    print("\nTo upload profile picture or CV, use multipart/form-data:")
    print("\nExample with curl:")
    print('curl -X PATCH http://localhost:8000/api/auth/profile/author/ \\')
    print('  -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('  -F "profile_picture=@/path/to/image.jpg" \\')
    print('  -F "cv=@/path/to/resume.pdf"')
    print("\nOr use Python requests:")
    print("files = {'profile_picture': open('image.jpg', 'rb'), 'cv': open('resume.pdf', 'rb')}")
    print("requests.patch(url, headers=headers, files=files)")

def test_institution_profile_update():
    """Test institution profile update with expanded fields"""
    print("\n" + "="*60)
    print("TESTING INSTITUTION PROFILE UPDATES")
    print("="*60)
    
    print("\nNote: You need to:")
    print("1. Register as an institution")
    print("2. Login to get access token")
    print("3. Use the token below\n")
    
    # Replace with actual token from login
    access_token = input("Enter your institution access token (or press Enter to skip): ").strip()
    
    if not access_token:
        print("Skipping institution profile tests...")
        return
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Get current profile
    response = requests.get(f"{BASE_URL}/profile/institution/", headers=headers)
    print_response("1. Get Current Institution Profile", response)
    
    # 2. Update profile with expanded fields
    update_data = {
        "institution_type": "university",
        "description": "Leading research university focused on innovation and excellence in science and technology.",
        "address": "123 University Avenue",
        "city": "Cambridge",
        "state": "Massachusetts",
        "country": "United States",
        "postal_code": "02138",
        "phone": "+1-617-555-0100",
        "website": "https://www.example-university.edu",
        "established_year": 1890,
        "research_areas": "Computer Science, Engineering, Physics, Biology, Medicine",
        "total_researchers": 500
    }
    
    response = requests.patch(f"{BASE_URL}/profile/institution/", json=update_data, headers=headers)
    print_response("2. Update Institution Profile", response)
    
    # 3. Get updated profile
    response = requests.get(f"{BASE_URL}/profile/institution/", headers=headers)
    print_response("3. Get Updated Institution Profile", response)
    
    print("\n" + "="*60)
    print("LOGO UPLOAD INSTRUCTIONS")
    print("="*60)
    print("\nTo upload institution logo, use multipart/form-data:")
    print("\nExample with curl:")
    print('curl -X PATCH http://localhost:8000/api/auth/profile/institution/ \\')
    print('  -H "Authorization: Bearer YOUR_TOKEN" \\')
    print('  -F "logo=@/path/to/logo.png"')

def show_profile_fields():
    """Display all available profile fields"""
    print("\n" + "#"*60)
    print("# AVAILABLE PROFILE FIELDS")
    print("#"*60)
    
    print("\n" + "="*60)
    print("AUTHOR PROFILE FIELDS")
    print("="*60)
    print("""
Basic Information:
  - title (Dr., Prof., Mr., Ms., Mrs.)
  - full_name
  - institute
  - designation
  - degree (e.g., "PhD in Computer Science")
  - gender (male, female, other, prefer_not_to_say)
  
Files:
  - profile_picture (image file - jpg, png)
  - cv (PDF or document file)
  
Research Profile:
  - bio (short biography)
  - research_interests (areas of research)
  - orcid (ORCID ID)
  - google_scholar (Google Scholar URL)
  - researchgate (ResearchGate URL)
  - linkedin (LinkedIn URL)
  - website (Personal/academic website)
    """)
    
    print("\n" + "="*60)
    print("INSTITUTION PROFILE FIELDS")
    print("="*60)
    print("""
Basic Information:
  - institution_name
  - institution_type (university, research_institute, government, 
                       private, industry, hospital, other)
  - description
  - established_year
  
Files:
  - logo (image file - jpg, png)
  
Location & Contact:
  - address
  - city
  - state
  - country
  - postal_code
  - phone
  - website
  
Research Information:
  - research_areas
  - total_researchers (number)
    """)

if __name__ == "__main__":
    try:
        print("\n" + "#"*60)
        print("# Profile Update Test Suite")
        print("# Make sure Django server is running on localhost:8000")
        print("#"*60)
        
        # Show available fields
        show_profile_fields()
        
        # Test author profile
        test_author_profile_update()
        
        # Test institution profile
        test_institution_profile_update()
        
        print("\n" + "#"*60)
        print("# Tests completed!")
        print("#"*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to the server.")
        print("Please make sure the Django server is running:")
        print("  python manage.py runserver")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")

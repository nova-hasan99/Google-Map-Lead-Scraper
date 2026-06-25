import os
import time
import re
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import cloudscraper
from bs4 import BeautifulSoup

load_dotenv()
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Smart Email Priority Keywords
PRIORITY_KEYWORDS = ['owner', 'admin', 'info', 'contact', 'hello', 'support', 'sales', 'enquiry']

def get_email_priority(email):
    """ইমেইলটি কতটা গুরুত্বপূর্ণ তা রেটিং করে। রেটিং যত কম, প্রায়োরিটি তত বেশি।"""
    email_lower = email.lower()
    for index, keyword in enumerate(PRIORITY_KEYWORDS):
        if keyword in email_lower:
            return index # কি-ওয়ার্ড পেলে তার ইনডেক্স রিটার্ন করবে (0 সবচেয়ে ভালো)
    return 99 # সাধারণ ইমেইলগুলোর প্রায়োরিটি সবার শেষে থাকবে

def extract_email_from_website(url):
    if url == "N/A":
        return "N/A"
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        response = scraper.get(url, timeout=8)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        emails = set()
        
        # 1. 'mailto:' লিঙ্কগুলো খোঁজা
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('mailto:'):
                email = a['href'].replace('mailto:', '').split('?')[0].strip()
                emails.add(email)
        
        # 2. টেক্সট থেকে Regex দিয়ে খোঁজা
        text = soup.get_text()
        found_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        emails.update(found_emails)
        
        # ভুয়া এক্সটেনশন বাদ দেওয়া
        valid_emails = [e.lower() for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.wixpress.com'))]
        
        if not valid_emails:
            return "Not Found"
            
        # স্মার্ট সর্টিং (Priority অনুযায়ী সাজানো)
        sorted_emails = sorted(valid_emails, key=get_email_priority)
        
        # সর্বোচ্চ ৩টি ইমেইল নেওয়া
        top_emails = sorted_emails[:3]
        
        return ", ".join(top_emails)
        
    except Exception:
        return "Protected/Blocked"

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/leads")
def get_leads(category: str = Query(...), location: str = Query(...), limit: int = Query(20, gt=0)):
    leads_data = []
    search_query = f"{category} in {location}"
    
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": search_query, "key": API_KEY}

    while len(leads_data) < limit:
        response = requests.get(search_url, params=params).json() if 'requests' in globals() else __import__('requests').get(search_url, params=params).json()
        results = response.get("results", [])
        
        for place in results:
            if len(leads_data) >= limit: break
            place_id = place.get("place_id")
            
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,url,business_status,types,current_opening_hours",
                "key": API_KEY
            }
            
            details_response = requests.get(details_url, params=details_params).json() if 'requests' in globals() else __import__('requests').get(details_url, params=details_params).json()
            details = details_response.get("result", {})
            
            website = details.get("website", "N/A")
            email = extract_email_from_website(website) if website != "N/A" else "N/A"
            opening_hours = details.get("current_opening_hours", {})
            open_now = opening_hours.get("open_now", "Unknown")
            
            lead = {
                "name": details.get("name", "N/A"),
                "status": details.get("business_status", "N/A"),
                "types": ", ".join(details.get("types", [])[:2]).replace("_", " ").title(),
                "open_now": "Yes" if open_now == True else ("No" if open_now == False else "N/A"),
                "address": details.get("formatted_address", "N/A"),
                "phone": details.get("formatted_phone_number", "N/A"),
                "website": website,
                "email": email,
                "rating": details.get("rating", "N/A"),
                "reviews": details.get("user_ratings_total", "0"),
                "map_link": details.get("url", "N/A")
            }
            leads_data.append(lead)

        next_page_token = response.get("next_page_token")
        if not next_page_token or len(leads_data) >= limit: break
        time.sleep(2)
        params = {"pagetoken": next_page_token, "key": API_KEY}

    return {"status": "success", "total": len(leads_data), "data": leads_data}
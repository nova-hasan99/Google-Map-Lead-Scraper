# Pro Maps Lead Scraper 

A professional web scraper built with FastAPI and Python. It extracts business leads from Google Maps (using the Places API) and smartly scrapes high-priority emails directly from their websites bypassing bot protections.

## Features
* Smart Email Priority (prioritizes owner, admin, info emails).
* Cloudscraper integration to bypass Cloudflare.
* Extracts Ratings, Reviews, Address, Phone, and Maps Links.
* Dynamic CSV Export.

## Setup Instructions

1. **Clone the repository:**
   \`\`\`bash
   git clone <your-repo-link>
   cd lead_scraper_project
   \`\`\`

2. **Create and activate a virtual environment:**
   * **Windows:**
     \`\`\`bash
     python -m venv venv
     venv\Scripts\activate
     \`\`\`
   * **Mac/Linux:**
     \`\`\`bash
     python3 -m venv venv
     source venv/bin/activate
     \`\`\`

3. **Install Dependencies:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Environment Variables:**
   * Rename `.env.example` to `.env`
   * Add your Google Places API Key: `GOOGLE_PLACES_API_KEY=your_key`

5. **Run the App:**
   \`\`\`bash
   uvicorn main:app --reload
   \`\`\`
   Open your browser and navigate to `http://127.0.0.1:8000`
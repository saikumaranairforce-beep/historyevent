import os
from flask import Flask, request, jsonify, render_template
from supabase import create_client
import requests

app = Flask(__name__, template_folder='templates')

# Initialize Supabase
supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
supabase_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    keyword = data.get('keyword', '')
    
    # 1. Fetch History from API Ninjas
    ninja_url = f"https://api.api-ninjas.com/v1/historicalevents?text={keyword}"
    history_res = requests.get(ninja_url, headers={'X-Api-Key': os.getenv("NINJA_API_KEY")})
    events = history_res.json()

    if not events:
        return jsonify({"error": "No events found"}), 404

    main_event = events[0]

    # 2. Call Gemini
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={os.getenv('GEMINI_API_KEY')}"
    prompt = f"Act as an archivist for PK Digital AI. Based on: '{main_event['event']}' in {main_event['year']}, write a LinkedIn post. Format: Question, News, Takeaway, and CTA: 'Kindly comment your valuable comments.' End with -- Thank PK Digital AI."
    
    gemini_res = requests.post(gemini_url, json={
        "contents": [{"parts": [{"text": prompt}]}]
    })
    post_text = gemini_res.json()['candidates'][0]['content']['parts'][0]['text']

    # 3. Save to Supabase for your Book
    supabase.table('historical_posts').insert({
        "event_year": str(main_event['year']),
        "event_description": main_event['event'],
        "generated_post": post_text,
        "keyword": keyword
    }).execute()

    return jsonify({"post": post_text})

# For local development
#if __name__ == '__main__':
#    app.run(port=5000,debug=True)
@app.route('/')
def home():
    return render_template('index.html')

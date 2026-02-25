import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db
import re

# ফায়ারবেস সেটআপ
secret_val = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if secret_val:
        cred_dict = json.loads(secret_val)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myanimeapp-8d079-default-rtdb.firebaseio.com'
        })
    else:
        print("Error: FIREBASE_CREDENTIALS not found!")
        exit(1)

def clean_id(text):
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Final API Mode) ---")
    
    # এটি বর্তমানে সচল থাকা সবচেয়ে নির্ভরযোগ্য Consumet API
    api_url = "https://consumet-api-shastra-shastra-shastras-projects.vercel.app/anime/gogoanime/recent-episodes"
    base_url = "https://anitaku.pe"

    try:
        print(f"সবচেয়ে নির্ভরযোগ্য সার্ভার থেকে ডেটা আনা হচ্ছে...")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                print(f"✓ সফল! {len(results)} টি নতুন এনিমি পাওয়া গেছে।")
                
                ref = db.reference('animes')
                count = 0
                
                for item in results:
                    try:
                        title = item.get('title')
                        anime_id = clean_id(title)
                        
                        # ডাটাবেসে না থাকলে সেভ করা
                        if not ref.child(anime_id).get():
                            ep_num = item.get('episodeNumber')
                            img_url = item.get('image', 'No Image')
                            watch_link = item.get('url', '')
                            
                            full_link = f"{base_url}{watch_link}" if watch_link.startswith('/') else watch_link

                            ref.child(anime_id).set({
                                'title': title,
                                'image': img_url,
                                'episode': f"Episode {ep_num}",
                                'link': full_link,
                                'type': 'Auto-Update'
                            })
                            print(f"✓ আপলোড সফল: {title}")
                            count += 1
                    except Exception:
                        continue
                        
                print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি ডাটাবেজে যুক্ত হয়েছে।")
            else:
                print("সার্ভার থেকে খালি লিস্ট এসেছে। কোনো নতুন আপডেট নেই।")
        else:
            print(f"API সার্ভার এরর! Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"মারাত্মক সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

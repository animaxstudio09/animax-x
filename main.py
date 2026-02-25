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
    print("--- অটোমেটিক আপডেট শুরু (Enime Master Source) ---")
    
    # Enime API - সবচেয়ে নির্ভরযোগ্য সোর্স
    api_url = "https://api.enime.moe/recent?perPage=30" # একসাথে ৩০টি নতুন এপিসোড আনবে
    
    try:
        print(f"মাস্টার সোর্স থেকে ডেটা আনা হচ্ছে...")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Enime API তে ডেটা 'data' নামের লিস্টে থাকে
            results = data.get('data', [])
            
            if results:
                print(f"✓ সফল! {len(results)} টি নতুন এপিসোড পাওয়া গেছে।")
                
                ref = db.reference('animes')
                count = 0
                
                for item in results:
                    try:
                        # Enime API থেকে ডেটা বের করার নিয়ম
                        anime_info = item.get('anime', {})
                        title = anime_info.get('title', {}).get('romaji', 'Unknown Title')
                        anime_id = clean_id(title)
                        
                        # ডাটাবেসে না থাকলে সেভ করা
                        if not ref.child(anime_id).get():
                            episode_num = item.get('number')
                            img_url = anime_info.get('coverImage', 'No Image')
                            anime_slug = anime_info.get('slug')
                            
                            # সরাসরি দেখার জন্য লিংক তৈরি করা
                            full_link = f"https://anitaku.pe/{anime_slug}-episode-{episode_num}"

                            ref.child(anime_id).set({
                                'title': title,
                                'image': img_url,
                                'episode': f"Episode {episode_num}",
                                'link': full_link,
                                'type': 'Auto-Update'
                            })
                            print(f"✓ আপলোড সফল: {title} - Episode {episode_num}")
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

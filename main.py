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
    return re.sub(r'[.#$\[\]]', '', text).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক এনিমি আপডেট শুরু (GitHub Actions) ---")
    
    # নতুন শক্তিশালী সার্ভার লিস্ট (Amvstr + Consumet)
    api_configs = [
        {
            "url": "https://api.amvstr.me/api/v2/source/gogoanime/recent",
            "type": "amvstr"
        },
        {
            "url": "https://consumet-api-drab.vercel.app/anime/gogoanime/recent-episodes",
            "type": "consumet"
        },
        {
            "url": "https://api.consumet.org/anime/gogoanime/recent-episodes",
            "type": "consumet"
        }
    ]

    results = []
    
    # সার্ভার চেক করা
    for config in api_configs:
        try:
            print(f"চেক করা হচ্ছে: {config['url']} ...")
            response = requests.get(config['url'], timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                
                # যদি Amvstr API হয়
                if config['type'] == "amvstr":
                    # Amvstr এর ডাটা স্ট্রাকচার আলাদা, তাই সেটা ঠিক করা হচ্ছে
                    raw_results = data.get('results', [])
                    for item in raw_results:
                        results.append({
                            'title': item.get('title'),
                            'episodeNumber': item.get('episode').replace('Episode ', '') if 'episode' in item else '0',
                            'image': item.get('image'),
                            'url': f"/{item.get('id')}" # লিংক তৈরি করা
                        })
                
                # যদি Consumet API হয় (আগেরটা)
                else:
                    results = data.get('results', [])
                
                if results:
                    print(f"✓ ডেটা পাওয়া গেছে ({config['type']} সার্ভার থেকে)!")
                    break
        except Exception as e:
            print(f"✗ সার্ভার এরর: {e}")
            continue

    if results:
        ref = db.reference('animes')
        count = 0
        
        for item in results:
            try:
                title = item.get('title')
                anime_id = clean_id(title)
                
                # ডাটাবেসে না থাকলে সেভ করা
                if not ref.child(anime_id).get():
                    episode_num = item.get('episodeNumber')
                    img_url = item.get('image')
                    watch_link = item.get('url')
                    
                    # লিংকের আগে ডোমেইন ঠিক করা
                    full_link = watch_link
                    if watch_link and not watch_link.startswith('http'):
                         # Gogoanime এর লেটেস্ট ডোমেইন
                        full_link = f"https://anitaku.pe{watch_link}"

                    ref.child(anime_id).set({
                        'title': title,
                        'image': img_url,
                        'episode': f"Episode {episode_num}",
                        'link': full_link,
                        'type': 'Auto-Update'
                    })
                    print(f"নতুন আপলোড: {title}")
                    count += 1
            except Exception:
                continue
        print(f"কাজ শেষ! মোট {count}টি নতুন এনিমি যুক্ত হয়েছে।")
    else:
        print("দুঃখিত! সব সার্ভার চেক করা হয়েছে কিন্তু কোনো ডেটা পাওয়া যায়নি।")

if __name__ == "__main__":
    start_auto_upload()

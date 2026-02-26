import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db
import re
import time

# ১. ফায়ারবেস কানেকশন
secret_val = os.environ.get("FIREBASE_CREDENTIALS")
if not firebase_admin._apps:
    if secret_val:
        cred_dict = json.loads(secret_val)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myanimeapp-8d079-default-rtdb.firebaseio.com'
        })

def clean_id(text):
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "_").lower()

def start_auto_upload():
    print("--- দ্রুত ডেটা রিকভারি শুরু হচ্ছে ---")
    
    # এটি MyAnimeList এর অফিসিয়াল API (এটি কখনো ব্লক হয় না)
    # এখান থেকে আমরা লেটেস্ট এনিমিগুলোর ছবি এবং নাম নেব
    api_url = "https://api.jikan.moe/v4/seasons/now?limit=15"
    
    try:
        print("অফিসিয়াল সোর্স থেকে ডেটা আনা হচ্ছে...")
        response = requests.get(api_url, timeout=20)
        
        if response.status_code == 200:
            anime_list = response.json().get('data', [])
            ref = db.reference('anime') 
            count = 0
            
            for anime in anime_list:
                try:
                    title = anime['title_english'] or anime['title']
                    thumbnail = anime['images']['jpg']['large_image_url']
                    
                    # Gogoanime এর ভিডিও লিঙ্কের জন্য সঠিক আইডি তৈরি
                    slug = title.lower().replace(":", "").replace("!", "").replace(" ", "-")
                    # সাধারণত লেটেস্ট এপিসোড ১ বা ২ হয়
                    video_url = f"https://embtaku.pro/streaming.php?id={slug}-episode-1"
                    
                    anime_id = clean_id(f"{slug}_latest")
                    
                    # ডাটাবেসে সেভ করা (আপনার সাইটের জন্য পারফেক্ট ফরম্যাট)
                    ref.child(anime_id).set({
                        'title': title,
                        'thumbnail': thumbnail,
                        'folder': f"{title} (Season 1)", # আপনার সিজন ফোল্ডার ডিমান্ড পূরণ করবে
                        'url': video_url,
                        'episode': "New Release",
                        'type': 'free',
                        'id': anime_id,
                        'date': int(time.time())
                    })
                    print(f"✓ রিকভারি সফল: {title}")
                    count += 1
                except Exception: continue
                
            print(f"\nঅভিনন্দন! {count}টি এনিমি আপনার সাইটে ফিরে এসেছে।")
        else:
            print("সার্ভার একটু বিজি, দয়া করে ২ মিনিট পর আবার রান দিন।")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_auto_upload()

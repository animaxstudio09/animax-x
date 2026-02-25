import os
import json
import firebase_admin
from firebase_admin import credentials, db
import re
import feedparser
import requests

# ১. ফায়ারবেস সেটআপ
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

def get_rss_data(url):
    """ব্রাউজার সেজে RSS ফিড ডাউনলোড করার ফাংশন"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return feedparser.parse(response.content)
    except Exception:
        pass
    return None

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Final Fix) ---")
    
    # দুটি সোর্স (যাতে একটি ব্লক হলে অন্যটি কাজ করে)
    rss_sources = [
        "https://subsplease.org/rss/?t&r=1080",  # Source 1 (খুবই ফাস্ট)
        "https://nyaa.si/?page=rss&c=1_2&f=0"     # Source 2 (ব্যাকআপ)
    ]
    
    entries = []
    
    # সোর্স চেক করা
    for url in rss_sources:
        print(f"চেক করা হচ্ছে: {url} ...")
        feed = get_rss_data(url)
        if feed and feed.entries:
            entries = feed.entries
            print(f"✓ ডেটা পাওয়া গেছে! ({len(entries)} টি আইটেম)")
            break
        else:
            print("✗ এই সোর্স কাজ করেনি, পরেরটায় যাচ্ছি...")

    if entries:
        # লক্ষ্য করুন: আপনার ওয়েবসাইটের ফোল্ডার নাম 'anime' (s ছাড়া)
        ref = db.reference('anime') 
        count = 0
        
        for entry in entries:
            try:
                full_title = entry.title
                
                # টাইটেল ক্লিন করা
                # SubsPlease ফরম্যাট: [SubsPlease] Title - 01 (1080p) [Hash]
                clean_title = re.sub(r'\[.*?\]', '', full_title) # ব্র্যাকেট রিমুভ
                clean_title = re.sub(r'\(.*?\)', '', clean_title) # প্যারেন্থেসিস রিমুভ
                clean_title = clean_title.replace('.mkv', '').strip()
                
                # নাম এবং এপিসোড আলাদা করা
                if ' - ' in clean_title:
                    parts = clean_title.split(' - ')
                    title = parts[0].strip()
                    episode_num = parts[-1].strip()
                else:
                    title = clean_title
                    episode_num = "New"
                
                anime_id = clean_id(f"{title}-{episode_num}")
                
                # ডাটাবেসে চেক করা
                if not ref.child(anime_id).get():
                    # Gogoanime এর ডাইরেক্ট সার্চ লিংক তৈরি করা (যাতে ইউজার ভিডিও পায়)
                    search_slug = title.lower().replace(' ', '-')
                    watch_link = f"https://anitaku.pe/category/{search_slug}"
                    
                    # ডিফল্ট থাম্বনেইল (যেহেতু RSS এ ছবি থাকে না)
                    default_img = "https://wallpapers.com/images/hd/cool-anime-girl-pfp-v2h1y9x9y9x9y9x9.jpg"
                    
                    # আপনার অ্যাপের 'folder-card' ডিজাইনের সাথে মিল রেখে ডেটা
                    ref.child(anime_id).set({
                        'title': title,
                        'thumbnail': default_img, # আপনার কোডে 'thumbnail' খোঁজে
                        'folder': "New Releases", # হোমপেজে শো করার জন্য
                        'url': watch_link,
                        'episode': f"Ep {episode_num}",
                        'type': 'free',
                        'id': anime_id,
                        'date': 2024 # সর্টিং এর জন্য
                    })
                    print(f"✓ ওয়েবসাইটের জন্য রেডি: {title}")
                    count += 1
            except Exception:
                continue
        
        print(f"\nকাজ শেষ! {count}টি নতুন এনিমি 'New Releases' ফোল্ডারে পাঠানো হয়েছে।")
    else:
        print("দুঃখিত, কোনো সোর্স থেকেই ডেটা আসেনি।")

if __name__ == "__main__":
    start_auto_upload()

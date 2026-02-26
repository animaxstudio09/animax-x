import os
import json
import requests
from bs4 import BeautifulSoup
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
    # ডাটাবেসের কি (Key) ক্লিন করা
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "_").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Direct Source Mode) ---")
    
    # Gogoanime এর লেটেস্ট আপডেট পেজ (AJAX)
    # এই লিংকটি সাধারণত ব্লক হয় না
    ajax_url = "https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=1"
    base_embed = "https://embtaku.pro/streaming.php?id="

    try:
        # ব্রাউজার সেজে রিকোয়েস্ট পাঠানো
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(ajax_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('li')
            
            ref = db.reference('anime') 
            count = 0
            
            for item in items:
                try:
                    # ১. এনিমির আসল নাম
                    name_tag = item.find('p', class_='name')
                    title = name_tag.text.strip()
                    
                    # ২. ভিডিও আইডি বের করা (যাতে ভিডিও মিস না হয়)
                    link_tag = item.find('a')
                    raw_id = link_tag['href'].strip('/') 
                    
                    # ৩. আসল ভিডিও লিংক (iframe এ চলার জন্য)
                    video_url = f"{base_embed}{raw_id}"
                    
                    # ৪. থাম্বনেইল
                    thumbnail = item.find('img')['src']
                    
                    # ৫. এপিসোড নম্বর
                    episode = item.find('p', class_='episode').text.strip()
                    
                    # ৬. ফোল্ডার নাম সাজানো (যেমন: One Piece Season 1)
                    folder_name = title
                    if "Season" not in title and "Part" not in title:
                        folder_name = f"{title} (Season 1)"
                    
                    anime_id = clean_id(raw_id)
                    
                    # ডাটাবেসে সেভ করা
                    if not ref.child(anime_id).get():
                        ref.child(anime_id).set({
                            'title': title,
                            'thumbnail': thumbnail,
                            'folder': folder_name,
                            'url': video_url,
                            'episode': episode,
                            'type': 'free',
                            'id': anime_id,
                            'date': 2024
                        })
                        print(f"✓ আপলোড হয়েছে: {title}")
                        count += 1
                except Exception:
                    continue
                    
            print(f"\nমোট {count}টি নতুন ভিডিও আপনার ওয়েবসাইটে যুক্ত হয়েছে।")
        else:
            print(f"সার্ভার এরর {response.status_code}। দয়া করে ১০ মিনিট পর আবার চেষ্টা করুন।")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

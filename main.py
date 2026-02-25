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
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "_").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Direct Link Grabber Mode) ---")
    
    # Gogoanime এর লেটেস্ট আপডেট পেজ (AJAX Endpoint)
    # এটি থেকে সরাসরি সঠিক ID পাওয়া যায়
    ajax_url = "https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=1"
    base_embed = "https://anitaku.pe/embed-episode/" # নতুন এবং স্টেবল প্লেয়ার লিঙ্ক

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        }
        print("সার্ভার থেকে আসল ডেটা আনা হচ্ছে...")
        response = requests.get(ajax_url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('li')
            
            ref = db.reference('anime') 
            count = 0
            
            for item in items:
                try:
                    # ১. সঠিক টাইটেল বের করা
                    name_tag = item.find('p', class_='name')
                    title = name_tag.text.strip()
                    
                    # ২. সিজন ডিটেকশন (Solo Leveling Season 1 ফরম্যাট)
                    display_title = title
                    if "Season" not in title and "Part" not in title:
                        display_title = f"{title} (Season 1)"
                    
                    # ৩. আসল ভিডিও আইডি বের করা (যাতে ৪-০-৪ এরর না আসে)
                    link_tag = item.find('a')
                    # এটি /title-episode-1 ফরম্যাটে থাকে
                    raw_id = link_tag['href'].replace("/", "") 
                    
                    # ৪. ভিডিও প্লেয়ার লিঙ্ক (সরাসরি embed লিঙ্ক)
                    video_url = f"{base_embed}{raw_id}"
                    
                    # ৫. থাম্বনেইল লিঙ্ক
                    img_tag = item.find('img')
                    thumbnail = img_tag['src']
                    
                    # ৬. এপিসোড নম্বর
                    episode_tag = item.find('p', class_='episode')
                    ep_text = episode_tag.text.strip()
                    
                    anime_id = clean_id(raw_id)
                    
                    if not ref.child(anime_id).get():
                        ref.child(anime_id).set({
                            'title': title,
                            'thumbnail': thumbnail,
                            'folder': display_title,
                            'url': video_url,
                            'episode': ep_text,
                            'type': 'free',
                            'id': anime_id,
                            'date': 2024
                        })
                        print(f"✓ সফল: {display_title} - {ep_text}")
                        count += 1
                except Exception:
                    continue
                    
            print(f"\nকাজ শেষ! {count}টি নতুন এনিমি ভিডিওসহ যুক্ত হয়েছে।")
        else:
            print(f"সার্ভার কানেকশন এরর: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

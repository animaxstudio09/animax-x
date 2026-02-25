import os
import json
import firebase_admin
from firebase_admin import credentials, db
from bs4 import BeautifulSoup
import cloudscraper
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
    print("--- অটোমেটিক স্ক্র্যাপিং শুরু (GitHub Actions) ---")
    
    # Gogoanime এর লেটেস্ট ডোমেইনগুলো (একটা কাজ না করলে অন্যটায় যাবে)
    domains = [
        "https://anitaku.pe",
        "https://gogoanime3.co",
        "https://gogoanimehd.io"
    ]
    
    # Cloudflare বাইপাস করার জন্য cloudscraper
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    })

    soup = None
    working_domain = ""

    # ডোমেইন চেক করা
    for domain in domains:
        try:
            print(f"চেক করা হচ্ছে ওয়েবসাইট: {domain} ...")
            response = scraper.get(domain, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # চেক করছি ওয়েবসাইটের কাঠামো ঠিক আছে কিনা
                if soup.find('ul', class_='items'):
                    print("✓ ওয়েবসাইট সফলভাবে লোড হয়েছে!")
                    working_domain = domain
                    break
                else:
                    print("✗ ওয়েবসাইট লোড হয়েছে কিন্তু Cloudflare ব্লক করেছে।")
            else:
                print(f"✗ সার্ভার এরর: {response.status_code}")
        except Exception as e:
            print(f"✗ সমস্যা: {e}")
            continue

    if soup:
        ref = db.reference('animes')
        items_container = soup.find('ul', class_='items')
        anime_items = items_container.find_all('li')
        count = 0
        
        for item in anime_items:
            try:
                name_tag = item.find('p', class_='name')
                if not name_tag: continue
                
                title = name_tag.text.strip()
                anime_id = clean_id(title)
                
                # ফায়ারবেসে আগে থেকে না থাকলে তবেই সেভ করবে
                if not ref.child(anime_id).get():
                    img_tag = item.find('img')
                    episode_tag = item.find('p', class_='episode')
                    link_tag = item.find('a')

                    img_url = img_tag['src'] if img_tag else "No Image"
                    episode = episode_tag.text.strip() if episode_tag else "Unknown"
                    watch_link = link_tag['href'] if link_tag else ""

                    full_link = f"{working_domain}{watch_link}" if watch_link.startswith('/') else watch_link

                    ref.child(anime_id).set({
                        'title': title,
                        'image': img_url,
                        'episode': episode,
                        'link': full_link,
                        'type': 'Auto-Update'
                    })
                    print(f"নতুন আপলোড: {title} ({episode})")
                    count += 1
            except Exception as inner_e:
                continue
        
        print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি যুক্ত হয়েছে।")
    else:
        print("\nদুঃখিত! কোনো ওয়েবসাইট থেকেই ডেটা আনা সম্ভব হয়নি।")

if __name__ == "__main__":
    start_auto_upload()

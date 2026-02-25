import os
import json
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, db
import re
from curl_cffi import requests as c_requests

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
    print("--- অটোমেটিক আপডেট শুরু (Anti-Cloudflare Mode) ---")
    
    # GogoAnime এর বর্তমান ডোমেইন
    domain = "https://anitaku.pe"
    
    try:
        print(f"ওয়েবসাইটে প্রবেশ করা হচ্ছে: {domain} ...")
        
        # এখানেই ম্যাজিক! impersonate="chrome110" গিটহাবকে আসল ক্রোম ব্রাউজার বানিয়ে দেবে
        response = c_requests.get(domain, impersonate="chrome110", timeout=30)
        
        if response.status_code == 200:
            # lxml পার্সার ব্যবহার করছি যা অনেক দ্রুত এবং নির্ভুল
            soup = BeautifulSoup(response.text, 'lxml')
            items_container = soup.find('ul', class_='items')
            
            if items_container:
                anime_items = items_container.find_all('li')
                print(f"✓ Cloudflare বাইপাস সফল! {len(anime_items)} টি আইটেম পাওয়া গেছে।")
                
                ref = db.reference('animes')
                count = 0
                
                for item in anime_items:
                    try:
                        name_tag = item.find('p', class_='name')
                        if not name_tag: continue
                        
                        title = name_tag.text.strip()
                        anime_id = clean_id(title)
                        
                        # ডাটাবেসে না থাকলে তবেই সেভ করবে
                        if not ref.child(anime_id).get():
                            img_tag = item.find('img')
                            episode_tag = item.find('p', class_='episode')
                            link_tag = item.find('a')

                            img_url = img_tag['src'] if img_tag else "No Image"
                            episode = episode_tag.text.strip() if episode_tag else "Unknown"
                            watch_link = link_tag['href'] if link_tag else ""

                            full_link = f"{domain}{watch_link}" if watch_link.startswith('/') else watch_link

                            ref.child(anime_id).set({
                                'title': title,
                                'image': img_url,
                                'episode': episode,
                                'link': full_link,
                                'type': 'Auto-Update'
                            })
                            print(f"নতুন আপলোড: {title}")
                            count += 1
                    except Exception as inner_e:
                        continue
                
                print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি যুক্ত হয়েছে।")
            else:
                print("✗ ওয়েবসাইট লোড হয়েছে কিন্তু Cloudflare ব্লক করেছে (Empty List)।")
        else:
            print(f"✗ সার্ভার এরর: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

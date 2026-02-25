import os
import json
import cloudscraper
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
    return re.sub(r'[.#$\[\]]', '', text).replace(" ", "-").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (Updated AJAX Mode) ---")
    
    # সঠিক সার্ভার লিংক (আগেরটা gogo-load ছিল, এখন gogocdn হবে)
    ajax_url = "https://ajax.gogocdn.net/ajax/page-recent-release.html?page=1&type=1"
    base_url = "https://anitaku.pe" 

    # Cloudscraper ব্যবহার করছি যাতে সার্ভার ব্লক না করে
    scraper = cloudscraper.create_scraper()

    try:
        print(f"সঠিক সার্ভারে কানেক্ট করা হচ্ছে: {ajax_url} ...")
        
        response = scraper.get(ajax_url, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            anime_list = soup.find_all('li')
            
            if anime_list:
                print(f"✓ সফল! {len(anime_list)} টি নতুন এনিমি পাওয়া গেছে।")
                
                ref = db.reference('animes')
                count = 0
                
                for item in anime_list:
                    try:
                        name_tag = item.find('p', class_='name')
                        if not name_tag: continue
                        
                        title = name_tag.find('a').text.strip()
                        anime_id = clean_id(title)
                        
                        if not ref.child(anime_id).get():
                            ep_tag = item.find('p', class_='episode')
                            episode = ep_tag.text.strip() if ep_tag else "New Episode"
                            
                            img_tag = item.find('img')
                            img_url = img_tag['src'] if img_tag else ""
                            
                            link_tag = item.find('a')
                            partial_link = link_tag['href'] if link_tag else ""
                            full_link = f"{base_url}{partial_link}"
                            
                            ref.child(anime_id).set({
                                'title': title,
                                'image': img_url,
                                'episode': episode,
                                'link': full_link,
                                'type': 'Auto-Update'
                            })
                            print(f"✓ আপলোড: {title}")
                            count += 1
                    except Exception:
                        continue
                
                print(f"\nমোট {count}টি নতুন এনিমি ডাটাবেজে আপডেট হয়েছে।")
            else:
                print("সার্ভার থেকে খালি লিস্ট এসেছে।")
        else:
            print(f"সার্ভার এরর! Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

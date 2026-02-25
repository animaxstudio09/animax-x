import os
import json
import firebase_admin
from firebase_admin import credentials, db
import re
import feedparser

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
    print("--- অটোমেটিক আপডেট শুরু (Website Fix Mode) ---")
    
    # Nyaa RSS Feed (সবচেয়ে নির্ভরযোগ্য সোর্স)
    rss_url = "https://nyaa.si/?page=rss&c=1_2&f=0"
    
    try:
        print(f"RSS Feed থেকে ডেটা আনা হচ্ছে...")
        feed = feedparser.parse(rss_url)
        
        if feed.entries:
            print(f"✓ ডেটা পাওয়া গেছে! এখন ওয়েবসাইটে পাঠানো হচ্ছে...")
            
            # লক্ষ্য করুন: এখানে 'animes' এর বদলে 'anime' করা হয়েছে যাতে ওয়েবসাইটে শো করে
            ref = db.reference('anime') 
            count = 0
            
            for entry in feed.entries:
                try:
                    full_title = entry.title
                    
                    # টাইটেল থেকে নাম বের করা
                    match = re.search(r'\] (.*?) - (\d+)', full_title)
                    if not match:
                        title = full_title[:30] # যদি ম্যাচ না করে, সাধারণ টাইটেল
                        episode_num = "New"
                    else:
                        title = match.group(1).strip()
                        episode_num = match.group(2).strip()
                    
                    anime_id = clean_id(f"{title}-{episode_num}")
                    
                    # ডাটাবেসে চেক করা
                    if not ref.child(anime_id).get():
                        # আপনার ওয়েবসাইটের কোড অনুযায়ী ফিল্ডগুলো ঠিক করা হলো:
                        # 1. thumbnail (আপনার সাইট 'image' এর বদলে 'thumbnail' খোঁজে)
                        # 2. folder (আপনার সাইট ফোল্ডার ছাড়া শো করে না)
                        
                        ref.child(anime_id).set({
                            'title': title,
                            'thumbnail': "https://i.ibb.co/6nB0Y58/placeholder.png", # অটোমেটিক ইমেজের জন্য ডিফল্ট
                            'folder': "New Releases", # যাতে হোমপেজে শো করে
                            'url': entry.link,
                            'episode': f"Ep {episode_num}",
                            'type': 'free',
                            'id': anime_id
                        })
                        print(f"✓ ওয়েবসাইটে যুক্ত হয়েছে: {title}")
                        count += 1
                except Exception:
                    continue
            
            print(f"\nকাজ শেষ! মোট {count}টি নতুন এনিমি ওয়েবসাইটে দেখা যাচ্ছে।")
        else:
            print("RSS Feed লোড হয়নি।")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

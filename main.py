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
    return re.sub(r'[.#$\[\]]', '', str(text)).replace(" ", "_").lower()

def start_auto_upload():
    print("--- অটোমেটিক আপডেট শুরু (AniList + Embed Video Mode) ---")
    
    # AniList API (এটি গিটহাবে কখনো ব্লক হয় না)
    query = '''
    query {
      Page(page: 1, perPage: 15) {
        media(sort: UPDATED_AT_DESC, type: ANIME, isAdult: false) {
          title { romaji english }
          coverImage { extraLarge }
          episodes
          nextAiringEpisode { episode }
          season
        }
      }
    }
    '''
    url = 'https://graphql.anilist.co'

    try:
        print("AniList থেকে ডেটা আনা হচ্ছে...")
        response = requests.post(url, json={'query': query}, timeout=15)
        
        if response.status_code == 200:
            anime_list = response.json()['data']['Page']['media']
            
            # আপনার ওয়েবসাইটের সঠিক ফোল্ডার
            ref = db.reference('anime') 
            count = 0
            
            for anime in anime_list:
                try:
                    # টাইটেল বের করা
                    title = anime['title']['english'] if anime['title']['english'] else anime['title']['romaji']
                    
                    # সিজন নম্বর বের করা (যাতে ফোল্ডারে Season 1 লেখা থাকে)
                    season_text = ""
                    if "Season" not in title and "Part" not in title:
                        season_text = " (Season 1)"
                    
                    folder_name = f"{title}{season_text}"
                    
                    # এপিসোড নম্বর
                    current_ep = anime['nextAiringEpisode']['episode'] - 1 if anime['nextAiringEpisode'] else (anime['episodes'] if anime['episodes'] else 1)
                    
                    # Gogoanime এর ডাইরেক্ট ভিডিও প্লেয়ার লিংক (Embed Link) তৈরি করা
                    slug = title.lower()
                    slug = re.sub(r'[^a-z0-9 ]', '', slug) # স্পেশাল ক্যারেক্টার রিমুভ
                    slug = slug.replace(' ', '-')
                    slug = re.sub(r'-+', '-', slug) # ডবল ড্যাশ রিমুভ
                    
                    # এটি হলো আসল প্লেয়ার লিংক যা আপনার iframe এ সরাসরি চলবে
                    video_url = f"https://embtaku.pro/streaming.php?id={slug}-episode-{current_ep}"
                    
                    anime_id = clean_id(f"{title}_ep_{current_ep}")
                    
                    # ডাটাবেসে চেক করা
                    if not ref.child(anime_id).get():
                        ref.child(anime_id).set({
                            'title': title,
                            'thumbnail': anime['coverImage']['extraLarge'], # আপনার সাইটের জন্য thumbnail
                            'folder': folder_name, 
                            'url': video_url,      # ভিডিও প্লেয়ারের লিংক
                            'episode': f"Episode {current_ep}",
                            'type': 'free',
                            'id': anime_id,
                            'date': 2024
                        })
                        print(f"✓ সফলভাবে আপলোড হয়েছে: {folder_name} - Ep {current_ep}")
                        count += 1
                except Exception:
                    continue
                    
            print(f"\nকাজ শেষ! {count}টি নতুন ভিডিও আপনার সাইটে লাইভ হয়েছে।")
        else:
            print(f"সার্ভার এরর: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

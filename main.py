import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, db
import re
import time

# ফায়ারবেস কানেকশন
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
    print("--- হারানো ডেটা পুনরুদ্ধারের চেষ্টা শুরু ---")
    
    # এটি বর্তমানে সবচেয়ে স্টেবল এনিমি ডাটাবেস (AniList)
    query = '''
    query {
      Page(page: 1, perPage: 25) { # একসাথে ২৫টি এনিমি চেক করবে
        media(sort: UPDATED_AT_DESC, type: ANIME, isAdult: false) {
          title { english romaji }
          coverImage { extraLarge }
          id
          nextAiringEpisode { episode }
          episodes
        }
      }
    }
    '''
    
    try:
        response = requests.post('https://graphql.anilist.co', json={'query': query}, timeout=15)
        if response.status_code == 200:
            anime_list = response.json()['data']['Page']['media']
            ref = db.reference('anime') 
            count = 0
            
            for anime in anime_list:
                try:
                    title = anime['title']['english'] or anime['title']['romaji']
                    # Gogoanime এর জন্য লিঙ্ক তৈরি (ID ভিত্তিক)
                    raw_slug = title.lower().replace(":", "").replace("!", "").replace(" ", "-")
                    
                    # এপিসোড নম্বর
                    ep_num = anime['nextAiringEpisode']['episode'] - 1 if anime['nextAiringEpisode'] else (anime['episodes'] or 1)
                    
                    # আপনার সাইটের iframe এ চলার জন্য একদম সঠিক এমবেড লিঙ্ক
                    video_url = f"https://embtaku.pro/streaming.php?id={raw_slug}-episode-{ep_num}"
                    
                    anime_id = clean_id(f"{raw_slug}_{ep_num}")
                    
                    # এখানে আমরা চেক করছি, যদি আগে থেকে না থাকে তবেই অ্যাড করবে (কিছুই ডিলিট করবে না)
                    if not ref.child(anime_id).get():
                        display_folder = title if "Season" in title else f"{title} (Season 1)"
                        
                        ref.child(anime_id).set({
                            'title': title,
                            'thumbnail': anime['coverImage']['extraLarge'],
                            'folder': display_folder,
                            'url': video_url,
                            'episode': f"Episode {ep_num}",
                            'type': 'free',
                            'id': anime_id,
                            'date': int(time.time())
                        })
                        print(f"✓ ডেটা রিকভারি সফল: {title}")
                        count += 1
                except Exception: continue
            print(f"\nকাজ শেষ! {count}টি এনিমি আপনার সাইটে আবার ফিরে এসেছে।")
        else:
            print("সার্ভার ওভারলোডেড। গিটহাব ১ ঘণ্টা পর আবার চেষ্টা করবে।")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_auto_upload()

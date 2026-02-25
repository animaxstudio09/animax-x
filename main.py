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
    print("--- অটোমেটিক আপডেট শুরু (AniList Advanced Mode) ---")
    
    # AniList API Query (নতুন রিলিজ হওয়া এনিমি খোঁজার জন্য)
    query = '''
    query {
      Page(page: 1, perPage: 10) {
        media(sort: UPDATED_AT_DESC, type: ANIME, isAdult: false) {
          id
          title {
            romaji
            english
          }
          coverImage {
            large
            extraLarge
          }
          bannerImage
          status
          episodes
          nextAiringEpisode {
            episode
          }
        }
      }
    }
    '''
    
    url = 'https://graphql.anilist.co'

    try:
        print(f"AniList ডাটাবেস চেক করা হচ্ছে...")
        response = requests.post(url, json={'query': query}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            anime_list = data['data']['Page']['media']
            
            if anime_list:
                print(f"✓ সফল! {len(anime_list)} টি ট্রেন্ডিং এনিমি পাওয়া গেছে।")
                
                # আপনার ওয়েবসাইটের ফোল্ডার স্ট্রাকচার: 'anime'
                ref = db.reference('anime') 
                count = 0
                
                for anime in anime_list:
                    try:
                        # নাম ঠিক করা (ইংরেজি থাকলে ইংরেজি, না হলে রোমানজি)
                        title = anime['title']['english'] if anime['title']['english'] else anime['title']['romaji']
                        
                        # এপিসোড নম্বর বের করা
                        current_ep = anime['nextAiringEpisode']['episode'] - 1 if anime['nextAiringEpisode'] else (anime['episodes'] if anime['status'] == 'FINISHED' else 1)
                        
                        # ফোল্ডারের নাম তৈরি করা (যেমন: Solo Leveling Season 1)
                        folder_name = f"{title}"
                        
                        # থাম্বনেইল (HD কোয়ালিটি)
                        thumbnail = anime['coverImage']['extraLarge']
                        
                        # Gogoanime এর ভিডিও লিংক তৈরি করা (অনুমান করে)
                        slug = title.lower().replace(' ', '-').replace(':', '').replace('!', '')
                        video_url = f"https://anitaku.pe/{slug}-episode-{current_ep}"
                        
                        # ডাটাবেসে সেভ করা
                        anime_id = clean_id(f"{title}_ep_{current_ep}")
                        
                        if not ref.child(anime_id).get():
                            # আপনার ওয়েবসাইটের ডিজাইনের জন্য ডেটা স্ট্রাকচার
                            anime_data = {
                                'title': title,
                                'thumbnail': thumbnail,
                                'folder': folder_name, # ফোল্ডার নাম হিসেবে টাইটেল ব্যবহার করছি
                                'url': video_url,
                                'episode': f"Episode {current_ep}",
                                'type': 'free',
                                'id': anime_id,
                                'status': anime['status'],
                                'description': f"Watch {title} Episode {current_ep} in HD quality.",
                                'date': 2024
                            }
                            
                            ref.child(anime_id).set(anime_data)
                            print(f"✓ আপলোড সফল: {folder_name} - Ep {current_ep}")
                            count += 1
                    except Exception:
                        continue
                        
                print(f"\nকাজ শেষ! মোট {count}টি নতুন এপিসোড আপনার ওয়েবসাইটে লাইভ হয়েছে।")
            else:
                print("AniList থেকে কোনো ডেটা আসেনি।")
        else:
            print(f"AniList সার্ভার এরর! Status Code: {response.status_code}")
            
    except Exception as e:
        print(f"সমস্যা: {e}")

if __name__ == "__main__":
    start_auto_upload()

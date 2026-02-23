// --- FIREBASE CONFIG ---
const firebaseConfig = {
    apiKey: "AIzaSyBcWE5TCxamMSnJxqSm5X4mgSwSccIXcBI",
    authDomain: "myanimeapp-8d079.firebaseapp.com",
    databaseURL: "https://myanimeapp-8d079-default-rtdb.firebaseio.com",
    projectId: "myanimeapp-8d079",
    storageBucket: "myanimeapp-8d079.firebasestorage.app",
    messagingSenderId: "37482342893",
    appId: "1:37482342893:web:bebc7352e4bc102b725fe4"
};
if (!firebase.apps.length) firebase.initializeApp(firebaseConfig);
const auth = firebase.auth(), db = firebase.database();

let currentUser = null, isPremium = false, currentVideoId = null;
let isMovieContent = false;

// Plyr Setup
const player = new Plyr('#main-video', { controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'fullscreen'] });
let hlsInstance = null;

// --- AUTH SYSTEM ---
auth.onAuthStateChanged(user => {
    if (user) {
        currentUser = user;
        document.getElementById('profile-name').innerText = user.email.split('@')[0].toUpperCase();
        checkPremium(user.uid);
        if (document.getElementById('auth-screen').style.display === 'flex') {
            document.getElementById('auth-screen').style.display = 'none';
            switchTab('profile'); 
        }
    } else {
        currentUser = null; isPremium = false;
        document.getElementById('vip-badge').innerText = "FREE PLAN";
        document.getElementById('vip-badge').style.background = "#222";
        document.getElementById('vip-badge').style.color = "#888";
        if(document.getElementById('profile-view').style.display === 'block') switchTab('home');
    }
});

function handleAuth(type) {
    const e = document.getElementById(type === 'login' ? 'email-in' : 'remail-in').value;
    const p = document.getElementById(type === 'login' ? 'pass-in' : 'rpass-in').value;
    if (type === 'login') auth.signInWithEmailAndPassword(e, p).catch(err => alert(err.message));
    else auth.createUserWithEmailAndPassword(e, p).catch(err => alert(err.message));
}
function toggleAuth() {
    const l = document.getElementById('login-form'), r = document.getElementById('reg-form');
    l.style.display = l.style.display === 'none' ? 'block' : 'none';
    r.style.display = r.style.display === 'none' ? 'block' : 'none';
}

function checkPremium(uid) {
    db.ref(`users/${uid}`).on('value', s => {
        const d = s.val();
        if(d && d.premiumExpiry > Date.now()) {
            isPremium = true;
            document.getElementById('vip-badge').innerText = "PREMIUM VIP";
            document.getElementById('vip-badge').style.background = "var(--gold)";
            document.getElementById('vip-badge').style.color = "#000";
        } else { isPremium = false; }
    });
}

// --- NAVIGATION ---
function switchTab(tab) {
    document.querySelectorAll('.app-view').forEach(d => d.style.display = 'none');
    document.getElementById('auth-screen').style.display = 'none'; 
    closeSearch();
    
    if (tab === 'home') document.getElementById('main-app').style.display = 'block';
    if (tab === 'profile') {
        if (currentUser) document.getElementById('profile-view').style.display = 'block';
        else document.getElementById('auth-screen').style.display = 'flex';
    }
    
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    document.querySelector(`.nav-item[data-tab="${tab}"]`).classList.add('active');
}

function switchInterface(to) {
    document.querySelectorAll('.app-view').forEach(d => d.style.display = 'none');
    if(to === 'movie') { document.getElementById('movie-box-view').style.display = 'block'; } 
    else { document.getElementById('main-app').style.display = 'block'; }
}

// --- PERFECT LIVE SEARCH LOGIC ---
document.getElementById('search-input').addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase().trim();
    const resDiv = document.getElementById('search-results');
    resDiv.innerHTML = "";
    
    if(query.length === 0) {
        resDiv.innerHTML = '<div class="empty-search">Type something to search...</div>';
        return;
    }

    let found = false;

    // Search Anime
    if(window.animeData) {
        Object.keys(window.animeData).forEach(name => {
            if(name.toLowerCase().includes(query)) {
                found = true;
                let thumb = window.animeData[name][0].thumbnail;
                resDiv.innerHTML += `
                    <div class="poster-card" style="max-width:100%;" onclick="closeSearch(); openFolder('${name.replace(/'/g, "\\'")}')">
                        <img src="${thumb}">
                        <div class="poster-title">${name}</div>
                    </div>`;
            }
        });
    }

    // Search Movies
    if(window.movieData) {
        window.movieData.forEach(m => {
            if(m.title.toLowerCase().includes(query)) {
                found = true;
                let safeId = m.id || m.title.replace(/[^a-zA-Z0-9]/g, '_');
                resDiv.innerHTML += `
                    <div class="poster-card" style="max-width:100%;" onclick="closeSearch(); playVideo('${m.title}', '${m.url}', '${safeId}', true, -1)">
                        <img src="${m.thumbnail}">
                        <div class="poster-title">${m.title}</div>
                    </div>`;
            }
        });
    }

    if(!found) {
        resDiv.innerHTML = '<div class="empty-search">No results found</div>';
    }
});

function openSearch() { document.getElementById('search-overlay').style.display = 'flex'; document.getElementById('search-input').focus(); }
function closeSearch() { document.getElementById('search-overlay').style.display = 'none'; document.getElementById('search-input').value = ""; document.getElementById('search-results').innerHTML = '<div class="empty-search">Type something to search...</div>'; }

// --- DATA LOADING & RENDERING ---
function loadContent() {
    db.ref('anime').on('value', snap => {
        const trendGrid = document.getElementById('trending-row'); 
        const newGrid = document.getElementById('new-row');
        trendGrid.innerHTML = ""; newGrid.innerHTML = "";
        
        let folders = {};
        snap.forEach(c => { let d = c.val(); let f = (d.folder || 'Misc').trim(); if(!folders[f]) folders[f] = []; folders[f].push(d); });
        
        let keys = Object.keys(folders);
        
        // Setup Hero Banner automatically from the first item
        if(keys.length > 0) {
            let heroItem = folders[keys[0]][0];
            document.getElementById('hero-content').innerHTML = `
                <img src="${heroItem.thumbnail}" class="hero-bg-img" style="position:absolute; inset:0; z-index:-1;">
                <h1 class="hero-title">${keys[0]}</h1>
                <div class="hero-tags"><span>${heroItem.type === 'premium' ? 'VIP' : 'Free'}</span><span>Action</span><span>Sub/Dub</span></div>
                <button class="hero-btn" onclick="openFolder('${keys[0].replace(/'/g, "\\'")}')"><i class="fas fa-play"></i> Play Now</button>
            `;
        }

        keys.forEach((name, idx) => {
            let cardHTML = `<div class="poster-card" onclick="openFolder('${name.replace(/'/g, "\\'")}')"><img src="${folders[name][0].thumbnail}"><div class="poster-title">${name}</div></div>`;
            if(idx % 2 === 0) trendGrid.innerHTML += cardHTML; // Just splitting dummy logic
            else newGrid.innerHTML += cardHTML;
        });
        window.animeData = folders;
    });
}

function loadMovies() {
    db.ref('movies').on('value', snap => {
        const grid = document.getElementById('movie-grid'); grid.innerHTML = ""; window.movieData = []; 
        let isFirst = true;

        snap.forEach(c => {
            let d = c.val(); window.movieData.push(d);
            let safeId = d.id || d.title.replace(/[^a-zA-Z0-9]/g, '_');

            if(isFirst) {
                document.getElementById('movie-hero-content').innerHTML = `
                    <img src="${d.thumbnail}" class="hero-bg-img" style="position:absolute; inset:0; z-index:-1;">
                    <h1 class="hero-title">${d.title}</h1>
                    <div class="hero-tags"><span>Movie</span><span>HD</span></div>
                    <button class="hero-btn" onclick="playVideo('${d.title}', '${d.url}', '${safeId}', true, -1)"><i class="fas fa-play"></i> Play Movie</button>
                `;
                isFirst = false;
            }

            grid.innerHTML += `<div class="poster-card" style="max-width:100%;" onclick="playVideo('${d.title}', '${d.url}', '${safeId}', true, -1)"><img src="${d.thumbnail}"><div class="poster-title">${d.title}</div></div>`;
        });
    });
}

// Player / Folder Logic (Same logic, adapted to new UI)
function openFolder(name) {
    const ep = window.animeData[name]; if(!ep || ep.length===0) return;
    playVideo(ep[0].title, ep[0].url, ep[0].id || ep[0].title.replace(/[^a-zA-Z0-9]/g, '_'), ep[0].type === 'premium', 0);
    const sel = document.getElementById('season-select'); sel.innerHTML = "";
    Object.keys(window.animeData).forEach(k => { let opt = document.createElement('option'); opt.value = k; opt.innerText = k; if(k===name) opt.selected = true; sel.appendChild(opt); });
    
    const cont = document.getElementById('episode-pill-container'); cont.innerHTML = "";
    ep.forEach((e, i) => {
        let btn = document.createElement('div'); btn.className = 'ep-pill'; btn.innerText = i+1; btn.id = `ep-btn-${i}`;
        btn.onclick = () => playVideo(e.title, e.url, e.id || e.title.replace(/[^a-zA-Z0-9]/g, '_'), e.type === 'premium', i);
        cont.appendChild(btn);
    });
}
function switchSeason(newFolder) { openFolder(newFolder); }

function playVideo(title, url, id, isPrem, index) {
    if(isPrem && !isPremium) { alert("PREMIUM REQUIRED! Please Upgrade."); switchTab('profile'); return; }
    
    currentVideoId = id; document.getElementById('player-title').innerText = title;
    isMovieContent = (index === -1);
    document.getElementById('content-type-badge').innerText = isMovieContent ? "Movie" : "Anime";
    document.querySelector('.resources-section').style.display = isMovieContent ? 'none' : 'block';

    if(!isMovieContent) {
        document.querySelectorAll('.ep-pill').forEach(b => b.classList.remove('active'));
        let activeBtn = document.getElementById(`ep-btn-${index}`); if(activeBtn) activeBtn.classList.add('active');
    }

    const videoElement = document.getElementById('main-video');
    if(hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }

    if(url.includes('.m3u8') && Hls.isSupported()) {
        hlsInstance = new Hls(); hlsInstance.loadSource(url); hlsInstance.attachMedia(videoElement);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, () => player.play());
    } else {
        videoElement.src = url; player.play();
    }

    document.getElementById('player-view').style.display = 'block';
    switchPlayerTab('foryou');
    loadForYouVideos(); loadSocialData(id);

    if(currentUser) db.ref(`users/${currentUser.uid}/watchlist/${id}`).set({ title: title, date: Date.now() });
}

function closePlayer() {
    player.stop(); if(hlsInstance) { hlsInstance.destroy(); hlsInstance = null; }
    document.getElementById('player-view').style.display = 'none';
}

function switchPlayerTab(tab) {
    document.querySelectorAll('.tab-item').forEach(e => e.classList.remove('active'));
    document.getElementById('tab-btn-' + tab).classList.add('active');
    document.getElementById('tab-content-foryou').style.display = tab==='foryou' ? 'block' : 'none';
    document.getElementById('tab-content-comments').style.display = tab==='comments' ? 'block' : 'none';
}

function loadForYouVideos() {
    const grid = document.getElementById('dynamic-rec-grid'); grid.innerHTML = "";
    if(isMovieContent && window.movieData) {
        window.movieData.forEach(m => grid.innerHTML += `<div class="poster-card" style="max-width:100%;" onclick="playVideo('${m.title}', '${m.url}', '${m.id}', true, -1)"><img src="${m.thumbnail}"><div class="poster-title">${m.title}</div></div>`);
    } else if(window.animeData) {
        Object.keys(window.animeData).forEach(fName => grid.innerHTML += `<div class="poster-card" style="max-width:100%;" onclick="openFolder('${fName.replace(/'/g, "\\'")}')"><img src="${window.animeData[fName][0].thumbnail}"><div class="poster-title">${fName}</div></div>`);
    }
}

// Like & Comments
function loadSocialData(id) {
    if(currentUser) {
        db.ref(`likes/${id}/${currentUser.uid}`).on('value', s => {
            const btn = document.getElementById('like-btn');
            if(s.exists()) { btn.classList.add('liked'); btn.innerHTML = `<i class="fas fa-check"></i><span>Added</span>`; } 
            else { btn.classList.remove('liked'); btn.innerHTML = `<i class="fas fa-plus"></i><span>My List</span>`; }
        });
    }
    
    const list = document.getElementById('comments-list'); list.innerHTML = "";
    db.ref(`comments/${id}`).on('child_added', s => {
        const c = s.val();
        list.innerHTML = `<div class="comment-box"><div class="c-avatar">${c.user[0]}</div><div class="c-body"><h4>${c.user}</h4><p>${c.text}</p></div></div>` + list.innerHTML;
    });
}

function toggleLike() {
    if(!currentUser) return;
    const ref = db.ref(`likes/${currentVideoId}/${currentUser.uid}`);
    ref.once('value', s => { if(s.exists()) ref.remove(); else ref.set(true); });
}

function postComment() {
    if(!currentUser) return;
    const txt = document.getElementById('comment-input').value; if(!txt) return;
    db.ref(`comments/${currentVideoId}`).push({ user: currentUser.email.split('@')[0], text: txt, time: Date.now() });
    document.getElementById('comment-input').value = "";
}

// History & Premium
function openHistory() {
    document.getElementById('history-view').style.display = 'block';
    if(!currentUser) return;
    db.ref(`users/${currentUser.uid}/watchlist`).limitToLast(20).on('value', s => {
        const c = document.getElementById('history-list-container'); c.innerHTML = "";
        if(!s.exists()) return c.innerHTML = "<p style='color:#666; text-align:center;'>Empty List</p>";
        s.forEach(i => {
            c.innerHTML = `<div style="background:#111; padding:15px; margin-bottom:10px; border-radius:8px; display:flex; justify-content:space-between;">
                <span style="color:#fff; font-size:14px; font-weight:600;">${i.val().title}</span>
            </div>` + c.innerHTML;
        });
    });
}
function closeHistory() { document.getElementById('history-view').style.display = 'none'; }
function redeemCode() {
    const code = document.getElementById('prem-code').value.trim();
    db.ref(`premium_codes/${code}`).once('value', s => {
        if(s.exists() && s.val().status === 'unused') {
            const expiry = Date.now() + ((s.val().days || 30) * 86400000);
            db.ref(`premium_codes/${code}`).update({status: 'used'});
            db.ref(`users/${currentUser.uid}`).update({premiumExpiry: expiry});
            alert(`SUCCESS! Premium Activated.`); location.reload();
        } else alert("Invalid Code.");
    });
}
function buyPremium() { window.open(`https://t.me/aminezone09`, '_blank'); }

// Init
loadContent(); loadMovies(); switchTab('home');

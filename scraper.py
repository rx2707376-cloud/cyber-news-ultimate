import feedparser, urllib.parse, re, db_news, requests, html, time
import trafilatura
from googlenewsdecoder import gnewsdecoder
from bs4 import BeautifulSoup

class NewsAggregator:
    def __init__(self):
        self.base_url = "https://news.google.com/rss/search"
        self.categories = {
            "KORUPSI": "korupsi OR KPK OR suap OR gratifikasi",
            "KRIMINAL": "kriminal OR pembunuhan OR perampokan OR narkoba",
            "NASIONAL": "politik OR presiden OR DPR OR pemerintah",
            "DAERAH": "pemkab OR pemkot OR gubernur OR bupati",
            "HUKUM": "pengadilan OR kejaksaan OR vonis OR sidang"
        }
        # Header Super Lengkap (Meniru Chrome di Windows)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def get_full_article(self, title, url, rss_summary):
        # 1. Ambil HTML dengan Requests (Header Super)
        html_content = None
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code == 200:
                html_content = res.text
        except Exception:
            pass

        # 2. Jika HTML didapat, ekstrak dengan Trafilatura
        if html_content:
            try:
                text = trafilatura.extract(html_content, include_comments=False)
                if text and len(text.split()) > 30:
                    clean_text = text.replace(title, "").strip()
                    if len(clean_text.split()) > 20:
                        print(f"     [✓] Sukses Ekstrak ({len(clean_text.split())} kata)")
                        return clean_text[:5000] + "..."
            except Exception:
                pass

        # 3. Jika Gagal, Gunakan Ringkasan RSS
        clean_rss = BeautifulSoup(rss_summary, "html.parser").get_text(separator=" ").strip()
        clean_rss = re.sub(r'<[^>]+>', '', clean_rss) # Bersihkan sisa HTML
        # Buang teks "Google News" bawaan jika ada
        clean_rss = clean_rss.replace("Comprehensive, up-to-date news coverage, aggregated from sources all over the world by Google News.", "").strip()

        if len(clean_rss.split()) > 15:
            print(f"     [✓] Fallback RSS ({len(clean_rss.split())} kata)")
            return clean_rss + "\n\n(Redaksi: Teks ini diambil dari ringkasan sistem agregasi karena situs asli memberlakukan proteksi tinggi.)"

        # 4. Benar-benar kosong
        print(f"     [x] Gagal total. Situs sangat dilindungi.")
        return "REDAKSI_NOTE"

    def fetch(self, query, cat):
        params = {"q": f"{query} when:7d", "hl": "id", "gl": "ID", "ceid": "ID:id"}
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        count = 0
        
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            if res.status_code != 200: return 0
            
            feed = feedparser.parse(res.text)
            
            for entry in feed.entries[:4]:
                title = html.unescape(entry.get('title', ''))
                google_link = entry.get('link', '')
                source = title.split(" - ")[-1] if " - " in title else "Media"
                
                # Decode URL
                real_url = google_link
                try:
                    decoded_data = gnewsdecoder(google_link)
                    if decoded_data and decoded_data.get('status') == True:
                        real_url = decoded_data.get('decoded_url')
                except Exception:
                    pass
                
                raw_summary = html.unescape(entry.get('summary', ''))
                image_url = ""
                m = re.search(r'src="([^"]+)"', raw_summary)
                if m: image_url = m.group(1)
                
                print(f"\n  -> Target: {title[:40]}...")
                full_content = self.get_full_article(title, real_url, raw_summary)
                
                if db_news.add_auto(title, cat, source, real_url, image_url, full_content):
                    count += 1
        except Exception as e:
            print(f"    [!] Gagal kategori {cat}: {str(e)}")
        return count

    def run_all(self):
        print("[*] Memulai Ekstraksi Tingkat Tinggi...")
        total = 0
        for cat, q in self.categories.items():
            print(f"\n  [Kategori: {cat}]")
            total += self.fetch(q, cat)
            time.sleep(2)
            
        print(f"\n[+] Selesai! {total} berita diproses.")
        return total

if __name__ == "__main__":
    db_news.init_db()
    NewsAggregator().run_all()

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

FILE_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.zip', '.rar', '.csv']
MAX_PAGES = 20  # Limit for crawling to avoid abuse

def is_file_link(href):
    return any(href.lower().endswith(ext) for ext in FILE_EXTENSIONS)

def crawl_site(base_url):
    visited = set()
    to_visit = [base_url]
    found_files = set()
    base_domain = urlparse(base_url).netloc

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_href = urljoin(url, href)
                parsed_href = urlparse(full_href)
                # Only crawl internal links
                if parsed_href.netloc == base_domain:
                    if is_file_link(full_href):
                        found_files.add(full_href)
                    else:
                        if full_href not in visited and not is_file_link(full_href):
                            to_visit.append(full_href)
        except Exception:
            continue
    return list(found_files)

@app.route('/api/crawl', methods=['GET'])
def crawl_files():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    try:
        files = crawl_site(url)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
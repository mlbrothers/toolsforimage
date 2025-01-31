# Author: Siddharth1India
import os
import io
import time
import json
import uuid
import queue
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFilter
from rembg import remove
from io import BytesIO

from flask import (
    Flask, abort, g, jsonify, redirect, render_template, request,
    send_file, send_from_directory, url_for, Response
)
from jinja2 import TemplateNotFound

from all_blog_data import blogs_list


app = Flask(__name__)

# At the top of your file, add:
supported_languages = ['en', 'hi', 'fr', 'zh', 'es']  # Add more as needed

@app.before_request
def before_request():
    # Exclude static files from language handling
    if request.path.startswith('/static/'):
        return  # Skip setting language for static file requests

    # Extract language from URL if present
    parts = request.path.split('/')
    if len(parts) > 1 and parts[1] in supported_languages:
        g.lang = parts[1]
    else:
        g.lang = 'en'  # Default to English

from werkzeug.exceptions import NotFound

@app.route('/<lang>/<path:subpath>')
def localized_route(lang, subpath):
    if lang not in supported_languages:
        # If language is not supported, redirect to English version
        return redirect(f'/en/{subpath}')
    
    # Set the language for this request
    g.lang = lang
    
    # Create a MapAdapter bound to the current host
    url_adapter = app.url_map.bind(request.host)
    
    try:
        # Try to match the subpath to a route
        endpoint, arguments = url_adapter.match('/' + subpath)
        return app.view_functions[endpoint](**arguments)
    except NotFound:
        # If no matching route found, try to render a template
        template_path = f'{lang}/{subpath}.html'
        if os.path.exists(os.path.join(app.template_folder, template_path)):
            return render_template(template_path)
        elif os.path.exists(os.path.join(app.template_folder, f'en/{subpath}.html')):
            return render_template(f'en/{subpath}.html')
        else:
            abort(404)

@app.route('/')
@app.route('/<lang>/')
def index(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/')
    return render_template(f'{lang}/index.html')

@app.route('/image-compression')
@app.route('/<lang>/image-compression')
def image_compression(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-compression')
    return render_template(f'{lang}/compress_en.html')

@app.route('/image-rotate')
@app.route('/<lang>/image-rotate')
def image_rotate(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-rotate')
    return render_template(f'{lang}/rotate_en.html')

@app.route('/image-crop')
@app.route('/<lang>/image-crop')
def image_crop(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-crop')
    return render_template(f'{lang}/crop_en.html')

@app.route('/image-resize')
@app.route('/<lang>/image-resize')
def image_resize(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-resize')
    return render_template(f'{lang}/resize_en.html')

@app.route('/image-effects')
@app.route('/<lang>/image-effects')
def image_effects(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-effects')
    return render_template(f'{lang}/image_effects_en.html')

@app.route('/convert-image-format')
@app.route('/<lang>/convert-image-format')
def convert_image_format(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/convert-image-format')
    return render_template(f'{lang}/convert_en.html')

@app.route('/convert/<from_format>-to-<to_format>')
@app.route('/<lang>/convert/<from_format>-to-<to_format>')
def convert_image_format_route(lang='en', from_format='', to_format=''):
    if lang not in supported_languages:
        return redirect(f'/en/convert/{from_format}-to-{to_format}')
    
    supported_formats = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp', 'ico']
    
    # Normalize formats
    from_format = from_format.lower()
    to_format = to_format.lower()
    
    # Validate formats
    if from_format not in supported_formats or to_format not in supported_formats:
        return render_template(f'{lang}/error.html', error="Unsupported image format"), 400
    
    # Prevent unnecessary conversions
    if from_format == to_format:
        return render_template(f'{lang}/error.html', error="Source and target formats are the same"), 400
    
    template_name = f'{from_format}-to-{to_format}.html'
    
    # Check if a specific template exists, otherwise use a generic template
    if os.path.exists(os.path.join(app.template_folder, f'{lang}/{template_name}')):
        return render_template(f'{lang}/{template_name}')
    else:
        return render_template(f'{lang}/generic_convert.html', from_format=from_format, to_format=to_format)

@app.route('/image-watermarking')
@app.route('/<lang>/image-watermarking')
def image_watermarking(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-watermarking')
    return render_template(f'{lang}/watermark_en.html')

@app.route('/blur-face')
@app.route('/<lang>/blur-face')
def image_blur(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/blur-face')
    return render_template(f'{lang}/blur_en.html')

@app.route('/remove-background')
@app.route('/<lang>/remove-background')
def remove_background_page(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/remove-background')
    return render_template(f'{lang}/remove-background.html')

@app.route('/blur-background')
@app.route('/<lang>/blur-background')
def blur_background_page(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/blur-background')
    return render_template(f'{lang}/blur-background.html')

@app.route('/apply-background-blur', methods=['POST'])
@app.route('/<lang>/apply-background-blur', methods=['POST'])
def apply_background_blur(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/apply-background-blur')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Read the input image
        input_image = Image.open(image_file)
        
        # Remove the background
        output_image = remove(input_image)
        
        # Blur the original image
        blurred_image = input_image.filter(ImageFilter.GaussianBlur(10))
        
        # Overlay the extracted foreground onto the blurred image
        blurred_image.paste(output_image, (0, 0), output_image)
        
        # Save the resulting image to a BytesIO object
        img_io = io.BytesIO()
        blurred_image.save(img_io, format='PNG')
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"blurred_bg_{uuid.uuid4().hex}_{int(time.time())}.png"

        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=unique_filename
        )
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500



# Consolidate static page routes
@app.route('/about')
@app.route('/<lang>/about')
def about(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/about')
    return render_template(f'{lang}/about.html')

@app.route('/contact-us')
@app.route('/<lang>/contact-us')
def contact_us(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/contact-us')
    return render_template(f'{lang}/contact_us.html')

@app.route('/help')
@app.route('/<lang>/help')
def help(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/help')
    return render_template(f'{lang}/help.html')

@app.route('/faq')
@app.route('/<lang>/faq')
def faq(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/faq')
    return render_template(f'{lang}/faq.html')

@app.route('/media')
@app.route('/<lang>/media')
def media(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/media')
    return render_template(f'{lang}/media.html')

@app.route('/legal')
@app.route('/<lang>/legal')
def legal(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/legal')
    return render_template(f'{lang}/legal.html')

@app.route('/blogs')
@app.route('/<lang>/blogs')
def blogs(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/blogs')

    # Get the blogs for the selected language
    blog_data = blogs_list.get(lang, blogs_list['en'])
    return render_template(f'{lang}/blogs.html', blogs=blog_data, lang=lang)

@app.route('/blogs/<blog_slug>')
@app.route('/<lang>/blogs/<blog_slug>')
def blog_post(blog_slug, lang='en'):
    if lang not in supported_languages:
        return redirect(url_for('blog_post', blog_slug=blog_slug, lang='en'))
    
    try:
        return render_template(f'{lang}/blogs/{blog_slug}.html')
    except TemplateNotFound:
        return redirect(url_for('blogs', lang=lang))

@app.route('/our-story')
@app.route('/<lang>/our-story')
def our_story(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/our-story')
    return render_template(f'{lang}/our_story.html')

@app.route('/team')
@app.route('/<lang>/team')
def team(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/team')
    return render_template(f'{lang}/team.html')

@app.route('/features')
@app.route('/<lang>/features')
def features(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/features')
    return render_template(f'{lang}/features.html')

@app.route('/pricing')
@app.route('/<lang>/pricing')
def pricing(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/pricing')
    return render_template(f'{lang}/pricing.html')

@app.route('/languages')
@app.route('/<lang>/languages')
def languages(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/languages')
    return render_template(f'{lang}/languages.html')

@app.route('/tools')
@app.route('/<lang>/tools')
def tools(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/tools')
    return render_template(f'{lang}/tools.html')

@app.route('/privacy_policy')
@app.route('/<lang>/privacy_policy')
def privacy_policy(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/privacy_policy')
    return render_template(f'{lang}/privacy_policy.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('en/error.html', error="404 - Page Not Found"), 404

@app.route('/svgs-and-icons')
def svg_and_icon():
    svg_folder = os.path.join('static', 'svgicons')
    svg_categories = {}
    print(f'hello:{svg_folder}')
    
    # Iterate through subdirectories in svgicons
    for category in os.listdir(svg_folder):
        category_path = os.path.join(svg_folder, category)
        
        if os.path.isdir(category_path):
            # Find SVG files in the category subdirectory
            svg_files = [f for f in os.listdir(category_path) if f.endswith('.svg')]
            
            # Create names by removing .svg extension and replacing underscores
            svg_names = [os.path.splitext(f)[0] for f in svg_files]
            
            # Store category information
            svg_categories[category] = list(zip(svg_files, svg_names))
    
    return render_template('en/svgs-and-icons.html', 
                           svg_categories=svg_categories)

@app.route('/api/get-svgs')
def get_svgs():
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 24))
    search_term = request.args.get('search', '').lower()

    svg_base_folder = os.path.join('static', 'svgicons')
    
    # If no category selected, use all categories
    if not category:
        svg_files = []
        for subdir in os.listdir(svg_base_folder):
            subdir_path = os.path.join(svg_base_folder, subdir)
            if os.path.isdir(subdir_path):
                category_files = [
                    (subdir, f) for f in os.listdir(subdir_path) 
                    if f.endswith('.svg') and 
                    (not search_term or search_term in f.lower())
                ]
                svg_files.extend(category_files)
    else:
        # If a specific category is selected
        svg_folder = os.path.join(svg_base_folder, category)
        svg_files = [
            (category, f) for f in os.listdir(svg_folder) 
            if f.endswith('.svg') and 
            (not search_term or search_term in f.lower())
        ]

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page
    paginated_files = svg_files[start:end]

    # Prepare response
    svgs_data = []
    for cat, svg in paginated_files:
        svgs_data.append({
            'name': os.path.splitext(svg)[0],
            'filename': svg,
            'category': cat  # Add category to the response
        })

    return jsonify({
        'svgs': svgs_data,
        'has_more': end < len(svg_files)
    })

@app.route('/svgs-and-icons/<string:svg_name>.html')
def svg_detail(svg_name):
    # Remove .html extension if present
    svg_name = svg_name.replace('.html', '')
    
    # Find the SVG in all categories
    svg_base_folder = os.path.join('static', 'svgicons')
    svg_info = None
    
    # Search through all categories to find the SVG
    for category in os.listdir(svg_base_folder):
        category_path = os.path.join(svg_base_folder, category)
        if os.path.isdir(category_path):
            for svg_file in os.listdir(category_path):
                if svg_file.startswith(svg_name + '.'):
                    svg_info = {
                        'name': svg_name,
                        'filename': svg_file,
                        'category': category,
                        'path': f'/static/svgicons/{category}/{svg_file}'
                    }
                    break
    
    if svg_info is None:
        return abort(404)
        
    return render_template('en/svg-detail.html', svg=svg_info)

class CrawlProgress:
    def __init__(self):
        self.lock = Lock()
        self.progress = {}
    
    def init_session(self, session_id):
        with self.lock:
            self.progress[session_id] = {
                'scanned': 0,
                'added': 0,
                'queued': 1,
                'url_queue': queue.Queue(),
                'visited_urls': set(),
                'seen_urls': set(),
                'sitemap_entries': [],
                'active_threads': 0,
                'processing_complete': False
            }
    
    def increment(self, session_id, key, amount=1):
        with self.lock:
            if session_id in self.progress:
                self.progress[session_id][key] += amount
    
    def decrement(self, session_id, key, amount=1):
        with self.lock:
            if session_id in self.progress:
                self.progress[session_id][key] -= amount
    
    def get_progress(self, session_id):
        with self.lock:
            if session_id in self.progress:
                return {
                    'scanned': self.progress[session_id]['scanned'],
                    'added': self.progress[session_id]['added'],
                    'queued': self.progress[session_id]['queued']
                }
            return None
    
    def cleanup(self, session_id):
        with self.lock:
            if session_id in self.progress:
                del self.progress[session_id]

crawl_progress = CrawlProgress()

@app.route('/sitemap-progress/<session_id>')
def sitemap_progress(session_id):
    def generate():
        try:
            while True:
                progress = crawl_progress.get_progress(session_id)
                if not progress:
                    break
                
                # Check if crawling is complete and no more URLs are queued
                session_data = crawl_progress.progress[session_id]
                if (session_data['processing_complete'] and 
                    session_data['queued'] == 0 and 
                    session_data['active_threads'] == 0):
                    break
                    
                yield f"data: {json.dumps(progress)}\n\n"
                time.sleep(1)
        except GeneratorExit:
            crawl_progress.cleanup(session_id)
    
    return Response(generate(), mimetype='text/event-stream')

def is_valid_url(url, domain):
    try:
        parsed = urlparse(url)
        return parsed.netloc == domain and parsed.scheme in ("http", "https")
    except:
        return False

def assign_priority(url, depth):
    priorities = {
        0: 1.0,
        1: 0.8,
        2: 0.6,
        3: 0.4,
    }
    return priorities.get(depth, 0.2)

import multiprocessing

# Get the number of available CPU cores
max_workers = min(8, (multiprocessing.cpu_count() or 1) * 2) 
print(max_workers)

def process_url(url, depth, session_id, domain):
    """Worker function to process a single URL"""
    try:
        progress = crawl_progress.progress[session_id]
        
        with progress['lock']:
            if url in progress['visited_urls']:
                crawl_progress.decrement(session_id, 'queued')
                return []
            progress['visited_urls'].add(url)
            progress['active_threads'] += 1
        
        crawl_progress.increment(session_id, 'scanned')
        crawl_progress.decrement(session_id, 'queued')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        
        # Skip if not HTML
        if 'text/html' not in content_type:
            return []

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")
        new_links = []
        
        # Extract URLs from <a> tags
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith('#') or href.startswith('javascript:'):
                continue

            abs_url = clean_url(urljoin(url, href))
            
            if abs_url and is_valid_url(abs_url, domain):
                normalized_url = abs_url.rstrip('/')
                with progress['lock']:
                    if normalized_url not in progress['seen_urls']:
                        progress['seen_urls'].add(normalized_url)
                        new_links.append((normalized_url, depth + 1))
                        progress['url_queue'].put((normalized_url, depth + 1))
                        crawl_progress.increment(session_id, 'queued')

        # Extract URLs from <img> tags (including SVGs)
        for img in soup.find_all("img", src=True):
            src = img["src"]
            abs_url = clean_url(urljoin(url, src))
            
            if abs_url and is_valid_url(abs_url, domain):
                normalized_url = abs_url.rstrip('/')
                with progress['lock']:
                    if normalized_url not in progress['seen_urls']:
                        progress['seen_urls'].add(normalized_url)
                        # Add SVG or image URL to sitemap entries
                        priority = 0.5  # Lower priority for images
                        progress['sitemap_entries'].append((normalized_url, priority))
                        crawl_progress.increment(session_id, 'added')

        # Extract URLs from <link> tags (e.g., stylesheets, icons)
        for link in soup.find_all("link", href=True):
            href = link["href"]
            abs_url = clean_url(urljoin(url, href))
            
            if abs_url and is_valid_url(abs_url, domain):
                normalized_url = abs_url.rstrip('/')
                with progress['lock']:
                    if normalized_url not in progress['seen_urls']:
                        progress['seen_urls'].add(normalized_url)
                        # Add link URL to sitemap entries
                        priority = 0.5  # Lower priority for assets
                        progress['sitemap_entries'].append((normalized_url, priority))
                        crawl_progress.increment(session_id, 'added')

        # Extract URLs from <script> tags
        for script in soup.find_all("script", src=True):
            src = script["src"]
            abs_url = clean_url(urljoin(url, src))
            
            if abs_url and is_valid_url(abs_url, domain):
                normalized_url = abs_url.rstrip('/')
                with progress['lock']:
                    if normalized_url not in progress['seen_urls']:
                        progress['seen_urls'].add(normalized_url)
                        # Add script URL to sitemap entries
                        priority = 0.5  # Lower priority for scripts
                        progress['sitemap_entries'].append((normalized_url, priority))
                        crawl_progress.increment(session_id, 'added')

        return new_links

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return []
    finally:
        with progress['lock']:
            progress['active_threads'] -= 1
            
@app.route('/generate-sitemap', methods=['GET', 'POST'])
def sitemap_generator():
    if request.method == 'GET':
        return render_template('en/sitemap-generator.html')

    try:
        data = request.get_json()
        if not data or 'url' not in data or 'sessionId' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400

        start_url = clean_url(data['url'])
        session_id = data['sessionId']

        if not start_url:
            return jsonify({'error': 'Invalid URL format'}), 400

        domain = urlparse(start_url).netloc.replace('www.', '')
        
        # Initialize session
        crawl_progress.init_session(session_id)
        progress = crawl_progress.progress[session_id]
        progress['lock'] = Lock()  # Add a lock for this session's data
        progress['url_queue'].put((start_url, 0))
        progress['processing_complete'] = False

        def crawler():
            try:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = set()
                    max_depth = 10
                    timeout_counter = 0
                    max_timeouts = 5  # Maximum number of consecutive timeouts
                    
                    while True:
                        try:
                            # Clean up completed futures
                            futures = {f for f in futures if not f.done()}
                            
                            # Try to get a new URL from the queue
                            try:
                                url, depth = progress['url_queue'].get(timeout=1)
                                timeout_counter = 0  # Reset timeout counter on successful get
                                
                                if depth <= max_depth:
                                    future = executor.submit(process_url, url, depth, session_id, domain)
                                    futures.add(future)
                            except queue.Empty:
                                timeout_counter += 1
                                # Only break if we've had multiple consecutive timeouts AND no active futures
                                if timeout_counter >= max_timeouts and not futures:
                                    break
                                continue
                            
                            # Process completed futures
                            done_futures = {f for f in futures if f.done()}
                            for future in done_futures:
                                try:
                                    future.result()  # Get the result to catch any exceptions
                                except Exception as e:
                                    print(f"Future error: {e}")
                                futures.remove(future)
                            
                            # If queue is empty and no active futures, wait a bit and check again
                            if progress['url_queue'].empty() and not futures:
                                time.sleep(0.5)
                                if progress['url_queue'].empty():  # Double check after waiting
                                    timeout_counter += 1
                                    if timeout_counter >= max_timeouts:
                                        break
                            
                            # Prevent too many concurrent futures
                            while len(futures) >= 10:
                                time.sleep(1)
                                futures = {f for f in futures if not f.done()}
                                
                        except Exception as e:
                            print(f"Crawler loop error: {e}")
                            continue
                    
                    # Wait for remaining futures to complete
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            print(f"Final future error: {e}")
            
            finally:
                progress['processing_complete'] = True

        # Start crawler in a separate thread
        crawler_thread = threading.Thread(target=crawler)
        crawler_thread.start()
        
        # Wait for crawler to complete with a timeout
        max_wait_time = 300  # 5 minutes maximum wait time
        wait_interval = 0.5
        total_waited = 0
        
        while not progress['processing_complete'] and total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            # Check if we have any entries already
            if progress['sitemap_entries'] and progress['url_queue'].empty():
                break
        
        # Force completion if we've waited too long
        if total_waited >= max_wait_time:
            progress['processing_complete'] = True
        
        crawler_thread.join(timeout=1)  # Give thread one last second to cleanup

        sitemap_entries = progress['sitemap_entries']
        if not sitemap_entries:
            crawl_progress.cleanup(session_id)
            return jsonify({'error': 'No URLs found'}), 400

        # Generate sitemap file
        sitemap_file = BytesIO()
        sitemap_file.write('<?xml version="1.0" encoding="UTF-8"?>\n'.encode('utf-8'))
        sitemap_file.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'.encode('utf-8'))

        for url, priority in sitemap_entries:
            sitemap_file.write("  <url>\n".encode('utf-8'))
            sitemap_file.write(f"    <loc>{url}</loc>\n".encode('utf-8'))
            sitemap_file.write(f"    <lastmod>{time.strftime('%Y-%m-%d')}</lastmod>\n".encode('utf-8'))
            sitemap_file.write("    <changefreq>daily</changefreq>\n".encode('utf-8'))
            sitemap_file.write(f"    <priority>{priority:.1f}</priority>\n".encode('utf-8'))
            sitemap_file.write("  </url>\n".encode('utf-8'))

        sitemap_file.write("</urlset>".encode('utf-8'))
        sitemap_file.seek(0)

        crawl_progress.cleanup(session_id)
        
        return send_file(
            sitemap_file,
            mimetype='application/xml',
            as_attachment=True,
            download_name='sitemap.xml'
        )

    except Exception as e:
        crawl_progress.cleanup(session_id)
        return jsonify({'error': str(e)}), 500

def clean_url(url):
    """Cleans and normalizes the URL."""
    try:
        parsed_url = urlparse(url)
        # Ensure we have scheme and netloc
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return None
        # Return normalized URL
        return parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path.rstrip('/')
    except:
        return None
    
if __name__ == '__main__':
    app.run(debug=True)
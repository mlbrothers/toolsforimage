# Author: Siddharth1India
import base64
from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, send_from_directory, url_for
from jinja2 import TemplateNotFound
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont, ImageColor
from html2image import Html2Image
from all_blog_data import blogs_list
import io
import time
import uuid
import os
import numpy as np
import json
import cv2
from rembg import remove


app = Flask(__name__)
hti = Html2Image()

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

def process_image(image_file):
    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format
        
        # Optionally resize the image to a smaller dimension (e.g., max width/height = 1024)
        max_dimension = 1024
        if max(image.size) > max_dimension:
            ratio = max_dimension / float(max(image.size))
            new_size = tuple([int(x * ratio) for x in image.size])
            image = image.resize(new_size, Image.LANCZOS)

        # Compress the image
        img_io = io.BytesIO()
        image.save(img_io, format=img_format, optimize=True, quality=50)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return img_io, img_format, unique_filename
    except Exception as e:
        raise e

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

if __name__ == '__main__':
    app.run(debug=True)
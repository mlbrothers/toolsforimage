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

@app.route('/compress-image', methods=['POST'])
@app.route('/<lang>/compress-image', methods=['POST'])
def compress_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/compress-image')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        img_io, img_format, unique_filename = process_image(image_file)
        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500

@app.route('/image-rotate')
@app.route('/<lang>/image-rotate')
def image_rotate(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-rotate')
    return render_template(f'{lang}/rotate_en.html')

@app.route('/rotate-image', methods=['POST'])
@app.route('/<lang>/rotate-image', methods=['POST'])
def rotate_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/rotate-image')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get rotation angle from form data
        rotation = int(request.form.get('rotation', 0))

        # Rotate the image
        rotated_image = image.rotate(-rotation, expand=True)

        # Save the rotated image
        img_io = io.BytesIO()
        rotated_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"rotated_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500

@app.route('/image-crop')
@app.route('/<lang>/image-crop')
def image_crop(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-crop')
    return render_template(f'{lang}/crop_en.html')

@app.route('/crop-image', methods=['POST'])
@app.route('/<lang>/crop-image', methods=['POST'])
def crop_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/crop-image')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get crop dimensions from form data
        x = int(request.form.get('crop-x', 0))
        y = int(request.form.get('crop-y', 0))
        width = int(request.form.get('crop-width', 0))
        height = int(request.form.get('crop-height', 0))

        # Crop the image
        cropped_image = image.crop((x, y, x + width, y + height))

        # Save the cropped image
        img_io = io.BytesIO()
        cropped_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"cropped_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500


@app.route('/convert-url-to-image', methods=['POST'])
@app.route('/<lang>/convert-url-to-image', methods=['POST'])
def convert_url_to_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/convert-url-to-image')

    url = request.form.get('url')
    if not url:
        return render_template(f'{lang}/error.html', error="No URL provided"), 400

    try:
        # Generate a unique filename for download purposes
        unique_filename = f"webpage_{uuid.uuid4().hex}_{int(time.time())}.png"

        # Create a BytesIO object to store the image in memory
        img_io = io.BytesIO()

        # Convert URL to image directly into BytesIO using Html2Image
        hti = Html2Image(
            output_path='.'
        )
        
        # Adding headless Chrome options to avoid dbus and GPU errors
        hti.screenshot(
            url=url, 
            save_as=unique_filename
        )
        
        # Write the generated image file to BytesIO
        with open(unique_filename, 'rb') as f:
            img_io.write(f.read())
        
        # Remove the temporary file after reading it
        os.remove(unique_filename)

        # Reset the pointer to the start of the BytesIO object
        img_io.seek(0)
        
        # Send the image directly from BytesIO
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=unique_filename
        )

    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500

@app.route('/image-resize')
@app.route('/<lang>/image-resize')
def image_resize(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-resize')
    return render_template(f'{lang}/resize_en.html')

@app.route('/resize-image', methods=['POST'])
@app.route('/<lang>/resize-image', methods=['POST'])
def resize_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/resize-image')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get resize dimensions and type from form data
        width = int(request.form.get('width', 0))
        height = int(request.form.get('height', 0))
        resize_type = request.form.get('resizeType', 'pixel')

        # Resize the image
        if resize_type == 'percentage':
            width = int(image.width * (width / 100))
            height = int(image.height * (height / 100))

        resized_image = image.resize((width, height), Image.LANCZOS)

        # Save the resized image
        img_io = io.BytesIO()
        resized_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"resized_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500

@app.route('/image-effects')
@app.route('/<lang>/image-effects')
def image_effects(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/image-effects')
    return render_template(f'{lang}/image_effects_en.html')

@app.route('/apply-effects', methods=['POST'])
@app.route('/<lang>/apply-effects', methods=['POST'])
def apply_effects(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/apply-effects')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get all active effects from the form data
        active_effects = request.form.get('effect', '').split(',')
        print(active_effects)
        # Apply all active effects
        if 'grayscale' in active_effects:
            image = image.convert('L').convert('RGB')
        
        if 'blur' in active_effects:
            image = image.filter(ImageFilter.GaussianBlur(radius=5))
        
        if 'sharpen' in active_effects:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
        
        if 'sepia' in active_effects:
            sepia_matrix = [
                0.393, 0.769, 0.189, 0,
                0.349, 0.686, 0.168, 0,
                0.272, 0.534, 0.131, 0
            ]
            image = image.convert('RGB', matrix=sepia_matrix)
        
        if 'invert' in active_effects:
            if image.mode == 'RGBA':
                r, g, b, a = image.split()
                rgb_image = Image.merge('RGB', (r, g, b))
                inverted_image = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted_image.split()
                image = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                image = ImageOps.invert(image)
        
        if 'brightness' in active_effects:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.5)
        
        if 'contrast' in active_effects:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
        
        if 'saturation' in active_effects:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.5)

        # Save the edited image
        img_io = io.BytesIO()
        image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        effects_applied = '_'.join(active_effects) if active_effects else 'no_effect'
        unique_filename = f"{effects_applied}_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500

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

@app.route('/watermark-image', methods=['POST'])
@app.route('/<lang>/watermark-image', methods=['POST'])
def watermark_image(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/watermark-image')

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    watermark_text = request.form.get('watermarkText', '')
    watermark_color = request.form.get('watermarkColor', '#000000')
    watermark_opacity = float(request.form.get('watermarkOpacity', 0.5))
    watermark_font_size = int(request.form.get('watermarkFontSize', 20))
    watermark_position = request.form.get('watermarkPosition', 'bottom-right')
    watermark_font_style = request.form.get('watermarkFontStyle', 'normal')

    try:
        # Open the image file
        image = Image.open(image_file)

        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # Set up the font
        font = ImageFont.load_default()
        font = font.font_variant(size=watermark_font_size)

        # Calculate text size
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Calculate position
        if watermark_position == 'top-left':
            x, y = 10, 10
        elif watermark_position == 'top-right':
            x, y = image.width - text_width - 10, 10
        elif watermark_position == 'bottom-left':
            x, y = 10, image.height - text_height - 10
        elif watermark_position == 'bottom-right':
            x, y = image.width - text_width - 10, image.height - text_height - 10
        else:  # center
            x, y = (image.width - text_width) // 2, (image.height - text_height) // 2

        # Apply watermark
        color = ImageColor.getrgb(watermark_color)
        opacity = int(255 * watermark_opacity)

        # Create a new image for the watermark text
        txt = Image.new('RGBA', image.size, (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)

        # Draw the text
        d.text((x, y), watermark_text, font=font, fill=color + (opacity,))

        # Applying font style effects
        if watermark_font_style == 'bold':
            d.text((x-1, y), watermark_text, font=font, fill=color + (opacity,))
            d.text((x+1, y), watermark_text, font=font, fill=color + (opacity,))
        elif watermark_font_style == 'italic':
            # Simulate italic by shearing the text
            txt = txt.transform(txt.size, Image.AFFINE, (1, 0.2, 0, 0, 1, 0), resample=Image.BICUBIC)
        elif watermark_font_style == 'bold-italic':
            d.text((x-1, y), watermark_text, font=font, fill=color + (opacity,))
            d.text((x+1, y), watermark_text, font=font, fill=color + (opacity,))
            txt = txt.transform(txt.size, Image.AFFINE, (1, 0.2, 0, 0, 1, 0), resample=Image.BICUBIC)

        # Combine the original image with the watermark text
        watermarked = Image.alpha_composite(image.convert('RGBA'), txt)

        # Save the image to a BytesIO object
        img_io = io.BytesIO()
        watermarked.convert('RGB').save(img_io, format='PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/blur-face')
@app.route('/<lang>/blur-face')
def image_blur(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/blur-face')
    return render_template(f'{lang}/blur_en.html')

@app.route('/apply-blur', methods=['POST'])
@app.route('/<lang>/apply-blur', methods=['POST'])
def apply_blur(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/apply-blur')

    try:
        # Get blur data from the request
        blur_data = request.json
        # Get the image data from the request
        image_data = blur_data.get('image')
        if not image_data:
            return render_template(f'{lang}/error.html', error="No image data provided"), 400

        # Strip base64 prefix if present and decode
        try:
            base64_data = image_data.split(',')[1] if ',' in image_data else image_data
            image = Image.open(io.BytesIO(base64.b64decode(base64_data)))
        except Exception as decode_err:
            return render_template(f'{lang}/error.html', error=f"Error decoding base64 image data: {str(decode_err)}"), 500
        
        # Check the format of the image
        img_format = image.format or 'PNG'  # Default to PNG if format is not detected

        # Calculate blur coordinates
        x = int(blur_data['x'] * image.width)
        y = int(blur_data['y'] * image.height)
        width = int(blur_data['width'] * image.width)
        height = int(blur_data['height'] * image.height)

        # Ensure the region to blur is within the image boundaries
        x = max(0, min(x, image.width - 1))
        y = max(0, min(y, image.height - 1))
        width = max(1, min(width, image.width - x))
        height = max(1, min(height, image.height - y))

        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Apply blur to the specified region
        roi = cv_image[y:y+height, x:x+width]
        if roi.size == 0:
            return render_template(f'{lang}/error.html', error="Invalid blur region"), 400
        blurred_roi = cv2.GaussianBlur(roi, (157, 157), 0)
        cv_image[y:y+height, x:x+width] = blurred_roi

        # Convert back to PIL Image
        blurred_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

        # Save the image to a BytesIO stream
        img_io = io.BytesIO()
        blurred_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"blurred_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        print(f"Error in apply_blur function: {str(e)}")
        return render_template(f'{lang}/error.html', error=str(e)), 500


@app.route('/remove-background')
@app.route('/<lang>/remove-background')
def remove_background_page(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/remove-background')
    return render_template(f'{lang}/remove-background.html')

@app.route('/remove-background', methods=['POST'])
@app.route('/<lang>/remove-background', methods=['POST'])
def remove_background(lang='en'):
    if lang not in supported_languages:
        return redirect('/en/remove-background')

    if 'image' not in request.files:
        return render_template(f'{lang}/error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template(f'{lang}/error.html', error="No selected file"), 400

    try:
        # Read the input image
        input_image = image_file.read()

        # Remove the background
        output_image = remove(input_image)

        # Create a BytesIO object to store the output image
        img_io = io.BytesIO(output_image)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"no_bg_{uuid.uuid4().hex}_{int(time.time())}.png"

        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=unique_filename
        )
    except Exception as e:
        return render_template(f'{lang}/error.html', error=str(e)), 500


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
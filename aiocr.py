#!/usr/bin/env python3
# * AI OCR : OCR Images via API and copy result to cliboard

# ** LICENSE
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# ** Commentary
# This program:
# 1. Creates a random filename, christened by pwgen
# 2. Takes a screenshot with scrot and stores it in /tmp/OCR
# 3. Gets its mimetype (ancient artifact)
# 4. encodes to base64
# 5. OCR’s via API
# 6. Copies result to clipboard with xclip
# 7. Writes result to file in /tmp/OCR
# 8. Sends a notification with notify-send

# ** Required Tools:
# - pwgen
# - scrot
# - base64
# - xclip
# - notify-send

import subprocess
import base64
import os  # Only used for os.makedirs and os.path.join
import requests

def generate_filename():
    """Generates a random filename using pwgen."""
    try:
        result = subprocess.run(['pwgen', '-s', '10', '-n', '1'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error generating filename: {e}. Make sure pwgen is installed.")
        exit(1)

def capture_screenshot(filepath):
    """Captures a screenshot using scrot and saves it to the given filepath."""
    try:
        subprocess.run(['scrot', '-s', '-q', '100', filepath], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error capturing screenshot: {e}")
        exit(1)

def get_image_mimetype(filepath):
    """Gets the MIME type of the image using the 'file' command."""
    try:
      result = subprocess.run(['file', '--mime-type', '-b', filepath], capture_output=True, text=True, check = True)
      mime_type = result.stdout.strip()
      if not mime_type.startswith("image/"):
            print("Unsupported image format. Please use JPEG, PNG, or WebP.")
            exit(1)
      return mime_type
    except(subprocess.CalledProcessError, FileNotFoundError) as e:
      print(f"Error getting file type: {e}")
      exit(1)


def encode_image_to_base64(filepath):
    """Encodes the image at the given filepath to base64."""
    try:
        result = subprocess.run(['base64', '-w', '0', filepath], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error Encoding File: {e}")
        exit(1)

def perform_ocr(image_base64, mime_type):
    """Performs OCR on the image using requests and OpenRouter."""
    openrouter_key = "YOUR_KEY_HERE"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openrouter_key}"
    }
    data = {
        "model": "qwen/qwen2.5-vl-72b-instruct:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "OCR this image, include newlines.  Use Org-Mode syntax, but don't make headings and don't fence the output in backticks.  Guide to Org-Mode syntax: Surround with / for italics, * for bold, _ for underline, ~ for single line code.  For multiple lines of code, surround with #+begin_src lang and #+end_src.  For quotes, surround with #+begin_quote and #+end_quote.  For superscript, surround with ^{ and }.  For subscript, surround with _{ and }."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    except requests.exceptions.RequestException as e:
        print(f"Error during OCR request: {e}")
        print(f"Response Content: {response.text}")
        exit(1)
    except KeyError as e:
        print(f"KeyError: {e}, Response: {response.text}")
        exit(1)


def copy_to_clipboard(text):
    """Copies the text to the clipboard using xclip."""
    try:
        subprocess.run(['xclip', '-selection', 'c'], input=text, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error copying to clipboard: {e}.  Ensure xclip is installed.")

def save_text_to_file(text, filepath):
    """Saves the text to the specified file."""
    try:
      with open(filepath, "w") as f:
          f.write(text)
    except Exception as e:
      print(f"Could not save to {filepath}. error: {e}")
      exit(1)

def send_notification(text):
    """Sends a desktop notification using notify-send."""
    try:
        subprocess.run(['notify-send', 'OCR', text], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error sending notification: {e}")

def main():
    """Main function to perform OCR."""
    fname = generate_filename()
    output_dir = "/tmp/OCR"
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"{fname}.jpg")
    text_path = os.path.join(output_dir, f"{fname}.txt")

    print(f"Using {image_path}")
    capture_screenshot(image_path)
    mime_type = get_image_mimetype(image_path)
    image_base64 = encode_image_to_base64(image_path)
    extracted_text = perform_ocr(image_base64, mime_type)

    if extracted_text:
      copy_to_clipboard(extracted_text)
      save_text_to_file(extracted_text, text_path)
      print("-------------------------------")
      print(extracted_text)
      send_notification(extracted_text)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# exit on error
set -o errexit

# Define storage directory
STORAGE_DIR=/opt/render/project/.render

# Check if Google Chrome is already downloaded
if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
  rm ./google-chrome-stable_current_amd64.deb
  cd $HOME/project/src # Make sure we return to where we were
else
  echo "...Using Chrome from cache"
fi

# Install system dependencies (including libGL for OpenCV)
echo "...Installing system dependencies"
apt-get update
apt-get install -y libgl1-mesa-glx

# Install Python dependencies
echo "...Installing Python dependencies"
pip install -r requirements.txt

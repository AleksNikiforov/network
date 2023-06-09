#Preparation of environment:
#!/bin/bash
sudo apt install python3-pip
sudo apt install python3-venv
sudo apt install zip
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
#Preparation google_ghrome and ghromedriver for selenium
cd ~/stuff/
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/
cd ../
export PATH=$PATH:/usr/bin/chromedriver

#Preparation of environment:
#!/bin/bash
sudo apt install libmariadbclient-dev
sudo apt install python3-pip
sudo apt install python3-venv
sudo apt install python3-dev 
sudo apt install zip
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
pip install scrapli[asyncssh]
#Preparation google_ghrome and ghromedriver for selenium
cd ~/scout-crawler/stuff/
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/
cd ../
export PATH=$PATH:/usr/bin/chromedriver
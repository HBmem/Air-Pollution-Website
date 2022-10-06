# Air-Pollution-Website  

use git clone to install the repo  
enter the command prompt  
cd into the folder that has manage.py in it  
run python -m pip install -r requirements.txt  
go to our sprint 3 folder on the one drive and download the .env file thats in the sprint 3 folder, put it in the same folder as manage.py  
run python manage.py runserver  
in a browser go to 127.0.0.1:8000  
upload files from our practice folder, then download them, and upload them to google earth


alternatively you can use the website from here http://airpollutionvisualizer.pythonanywhere.com/
this way you dont need to bother with all these steps, still need the files from the practice folder though




Changes for python anywhere
Views.py  line 83 changed to kmlPath = os.path.join(prevdir, 'air_pollution_website/kml')

Settings.py SECRET_KEY changed to SECRET_KEY = os.getenv('SECRET_KEY') and add to imports 'from pathlib import Path'

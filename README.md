Installs all you need to run your flask app
pip install -r requirements.txt

==========================================

MULTILINGUAL SITE WITH FLASK BABEL
https://python-babel.github.io/flask-babel/

Install Flask Babel
pip install Flask-Babel

Directories
Create /translations directory at the root of the project

Create /lg directory for each supported language (e.g. /en, /hy,…)

Create /LC_MESSAGES folder under each supported language add & configure babel.cfg file at the root of the project
[jinja2: templates/**.html]
[python: **.py]

Extract text strings from our HTML templates and .py files
pybabel extract -F babel.cfg -o messages.pot . 
It creates a messages.pot file

Then initialize language translation files, it will create a .po file, here for Armenian (hy)
pybabel init -i messages.pot -d translations -l hy

Note: if you want to later update the .po file after creating a new messages.pot file
pybabel update -d translations -i messages.pot -l fr

Translate the strings
Then translate all the msgid entries in the .po file as msgstr


Finally, compile the .po file to a .mo file
pybabel compile -d translations

Don't forget to import babel as shown in our boilerplate
from flask_babel import Babel, _,lazy_gettext as _l, gettext

============================================================
DATABASE INSTALATION

Restore the database from the dump. Open the CMD in current folder and run the following command
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS db"
mysql -u root -p db < Dump.sql

==============================================================
Ngnx image dir permissions

# recursively hand ownership to your service user
sudo chown -R www-data:www-data /var/www/mammysbread/static/images

# directories need `+x` so they can be entered
sudo find /var/www/mammysbread/static/images -type d -exec chmod 755 {} \;

# files only need read/write
sudo find /var/www/mammysbread/static/images -type f -exec chmod 644 {} \;


-------------------

# Make www-data own the folder (and everything inside)
sudo chown -R www-data:www-data /var/www/mammysbread/static/images

# Give owner (www-data) and group (www-data) read/write/execute,
# others read/execute only:
sudo chmod -R 775 /var/www/mammysbread/static/images


======================

# 1. Update your remote‐tracking branch
git fetch origin

# 2. Discard any staged changes in templates/ and reset them to origin/main
git restore --source=origin/main --staged -- templates/

# 3. Discard any unstaged (working‐tree) changes in templates/
git restore --source=origin/main -- templates/



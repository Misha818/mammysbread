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
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS blog_db"
mysql -u root -p blog_db < Dump.sql
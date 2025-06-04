from flask import Flask, session, redirect, jsonify, request, g
from mmb_db import get_db
from dotenv import load_dotenv
from flask_babel import Babel, _, lazy_gettext as _l, gettext
from werkzeug.utils import secure_filename
from functools import wraps
from bs4 import BeautifulSoup
from datetime import datetime, date
import logging
import mysql.connector
from mysql.connector import pooling, Error
import os
import re
import random
import string
import time
import requests
import cssutils


def with_conn(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        conn = get_db()
        return f(conn, *args, **kwargs)
    return wrapper

load_dotenv()

# Determine the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the static folder path relative to the current script's directory
static_folder_path = os.path.join(current_dir, 'static')
target_directory = os.path.join(static_folder_path, 'images/quilljs')
os.makedirs(target_directory, exist_ok=True)

MAIN_CURRENCY = os.getenv('MAIN_CURRENCY')

def action_info():
    return session.get('action_info')

def init_sysadmin_context(app):
    @app.context_processor
    def inject_action_info():
        # whatever keys you return here will be global in templates
        return {
            'actionInfo': action_info()
        }

def get_db_connection(use_dict_cursor=False):
    retries = 3
    for i in range(retries):
        try:
            db_connection = mysql.connector.connect(
                user=os.getenv('MYSQL_USER'),
                password=os.getenv('PASSWORD'),
                host=os.getenv('LOCALHOST'),
                database=os.getenv('DATABASE'),
                connection_timeout=10
            )
            if db_connection.is_connected():
                # Create a cursor with dictionary=True if needed
                cursor = db_connection.cursor(dictionary=use_dict_cursor)
                return db_connection, cursor
        except mysql.connector.Error as err:
            print(f"Attempt {i + 1} failed: {err}")
            if i < retries - 1:
                time.sleep(5)  # Wait before retrying
            else:
                raise


def close_connection(db_connection):
    if db_connection.is_connected():
        db_connection.close()

@with_conn
def sqlSelect(
    conn,
    sqlQuery: str,
    sqlParams: tuple | None = None,
    as_dict: bool = False
):
    """
    Execute a SELECT query and return rows, row‐count, and any error.
    Connections are returned to the pool automatically via Flask’s teardown.
    """
    # conn = get_db()
    cursor = conn.cursor(dictionary=as_dict)
    try:
        cursor.execute(sqlQuery, sqlParams or ())
        rows = cursor.fetchall()
        return {
            "data": rows,
            "length": len(rows),
            "error": None
        }
    except Error as e:
        logging.exception("Failed to execute SELECT")
        return {
            "data": [],
            "length": 0,
            "error": str(e)
        }

@with_conn
def sqlInsert(
    conn,
    sqlQuery: str,
    sqlParams: tuple | None = None
) -> dict:
    """
    Execute an INSERT statement and return status, inserted_id, and rows_affected.
    """
    # conn = get_db()
    params = sqlParams or ()
    status = 0

    try:
        # 1) Use a context-manager so the cursor is always closed
        with conn.cursor() as cursor:
            cursor.execute(sqlQuery, params)
            conn.commit()

            rows = cursor.rowcount
            new_id = cursor.lastrowid

        # 2) Build a clear, typed response
        if rows > 0:
            msg = gettext(
                "Inserted successfully, %(count)d rows affected.", count=rows
            )
            status = 1
        else:
            msg = gettext(
                "Query executed successfully, but no rows were affected."
            )
            status = 1

        return {
            "status": status,               
            "answer": msg,
            "inserted_id": new_id,
            "rows_affected": rows,
        }

    except mysql.connector.Error as err:
        # 3) Roll back on any DB error, and log the full stack
        conn.rollback()
        logging.exception("Failed to execute INSERT")
        return {
            "status": 0,
            "message": gettext("An error occurred: %(error)s", error=str(err)),
            "inserted_id": None,
            "rows_affected": 0,
        }

@with_conn
def sqlUpdate(conn, sqlQuery, sqlValuesTuple=''):
    # Update the content from the MySQL database
    # db_connection = get_db()
    db_connection = conn
    rows_affected = None
    status = '-1'
    try:
        with db_connection.cursor() as cursor:
            cursor.execute(sqlQuery, sqlValuesTuple)
            
            # Commit the transaction
            db_connection.commit()
            
            # Check how many rows were affected
            rows_affected = cursor.rowcount

            # Close the cursor
            # cursor.close()
            
            # Check if rows were affected
            if rows_affected > 0:
                answer = f"Query executed successfully, {rows_affected} rows affected."
                status = '1'
                # answer = gettext('Done!')
            else:
                answer = "Query executed successfully, but no rows were affected."
                status = '1'

    except Exception as e:
        db_connection.rollback()
        logging.exception("Failed to execute update query")
        answer = f"An error occurred: {e}"
    # finally:
    #     db_connection.close()        # returns to pool now
    #     g.pop("db_conn", None)       # so teardown doesn’t double-close it

    return {'status': status, 'answer': answer, 'rows_affected': rows_affected}


@with_conn
def sqlDelete(conn, sqlQuery, sqlValuesTuple):
    
    try:
        # Get a connection from the pool
        # conn = get_db()
        cursor = conn.cursor()
        
        # Execute the DELETE statement
        cursor.execute(sqlQuery, sqlValuesTuple)
        
        # Commit the transaction
        conn.commit()
        
        answer = "Record deleted successfully"
        status = '1'
    except mysql.connector.Error as err:
        answer = f"An error occurred: {err}"
        status = '-1'

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        # if conn:
        #     conn.close()

    return {'status': status, 'answer': answer}


def getLangID():

    defLang = getDefLang()
    langID = defLang['id']

    currentLangPrefix = session.get('lang', defLang['Prefix'])
    supportedLangs = supported_langs()
    for lang in supportedLangs:
        if currentLangPrefix == lang['Prefix']:
            langID = lang['Language_ID']
   
    return langID


def getLangdata(Prefix):

    content = {}
    supportedLangs = supported_langs()
    for lang in supportedLangs:
        if Prefix == lang['Prefix']:
            content['ID'] = lang['Language_ID']
            content['Language'] = lang['Language']
            content['Prefix'] = lang['Prefix']

    return content


def get_pc_ref_key(pc_id):
    sqlQuery = "SELECT `PC_Ref_Key` FROM `product_c_relatives` WHERE `PC_ID` = %s"
    sqlValTuple = (pc_id,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        for val in result['data']:
            if val['PC_Ref_Key'] > 0:
                return val['PC_Ref_Key']
    else:
        return False
    

def get_ac_ref_key(pc_id):
    sqlQuery = "SELECT `AC_Ref_Key` FROM `article_c_relatives` WHERE `AC_ID` = %s"
    sqlValTuple = (pc_id,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        for val in result['data']:
            if val['AC_Ref_Key'] > 0:
                return val['AC_Ref_Key']
    else:
        return False


def  get_pc_id_by_lang(pcRefKey):
    sqlQuery = "SELECT `PC_ID` FROM `product_c_relatives` WHERE `PC_Ref_Key` = %s AND Language_ID = %s"
    langID = getLangID()
    sqlValTuple = (pcRefKey, langID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        return result['data'][0]['PC_ID']
    else:
        return False


def  get_ac_id_by_lang(pcRefKey):
    sqlQuery = "SELECT `AC_ID` FROM `article_c_relatives` WHERE `AC_Ref_Key` = %s AND Language_ID = %s"
    langID = getLangID()
    sqlValTuple = (pcRefKey, langID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        return result['data'][0]['AC_ID']
    else:
        return False

# Get product id by language
def  get_pr_id_by_lang(RefKey, langID):
    sqlQuery = "SELECT `P_ID` FROM `product_relatives` WHERE `P_Ref_Key` = %s AND Language_ID = %s"
    sqlValTuple = (RefKey, langID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        return result['data'][0]['P_ID']
    else:
        return False

# Get article id by language
def  get_ar_id_by_lang(RefKey, langID):
    sqlQuery = "SELECT `A_ID` FROM `article_relatives` WHERE `A_Ref_Key` = %s AND Language_ID = %s"
    sqlValTuple = (RefKey, langID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        return result['data'][0]['A_ID']
    else:
        return False


# Check if product name exists
def pr_name_check(productName, languageID, productID): 
    myResponse = {'status': '0'}
    update = ''
    sqlQueryCheck3Val = (productName, languageID)

    if productID is not None:
        update = ' AND `ID` != %s'
        sqlQueryCheck3Val = (productName, languageID, productID)
    
    sqlQueryCheck3 = f"""SELECT `ID` FROM `product` WHERE `Title` = %s  AND Language_ID = %s {update}"""
    result3 = sqlSelect(sqlQueryCheck3, sqlQueryCheck3Val, True)

    if result3['length'] > 0:
        myResponse['status'] = '1'    
        myText = f"""'{productName}' Product Exists!"""
        myResponse['answer'] = gettext(myText)    

    return myResponse


# Check if article name exists
def ar_name_check(productName, languageID, productID): 
    myResponse = {'status': '0'}
    update = ''
    sqlQueryCheck3Val = (productName, languageID)

    if productID is not None:
        update = ' AND `ID` != %s'
        sqlQueryCheck3Val = (productName, languageID, productID)
    
    sqlQueryCheck3 = f"""SELECT `ID` FROM `article` WHERE `Title` = %s  AND Language_ID = %s {update}"""
    result3 = sqlSelect(sqlQueryCheck3, sqlQueryCheck3Val, True)

    if result3['length'] > 0:
        myResponse['status'] = '1'    
        myText = f"""'{productName}' Article Exists!"""
        myResponse['answer'] = gettext(myText)    

    return myResponse

# Check if product link exists
def pr_url_check(productLink, languageID, productID):
    myResponse = {'status': '0'}
    update = ''
    sqlQueryCheck5Val = (productLink, languageID)
    
    if productID is not None:
        update = ' AND `ID` != %s'
        sqlQueryCheck5Val = (productLink, languageID, productID)

    sqlQueryCheck5 = f"""SELECT `ID` FROM `product` WHERE `Url` = %s AND Language_ID = %s {update}"""
    result5 = sqlSelect(sqlQueryCheck5, sqlQueryCheck5Val, True)

    if result5['length'] > 0:
        myResponse['status'] = '1'   
        myText = f"""'{productLink}' Link Exists!"""
        myResponse['answer'] = gettext(myText)  
    
    return myResponse


# Check if product link exists
def ar_url_check(productLink, languageID, productID):
    myResponse = {'status': '0'}
    update = ''
    sqlQueryCheck5Val = (productLink, languageID)
    
    if productID is not None:
        update = ' AND `ID` != %s'
        sqlQueryCheck5Val = (productLink, languageID, productID)

    sqlQueryCheck5 = f"""SELECT `ID` FROM `article` WHERE `Url` = %s AND Language_ID = %s {update}"""
    result5 = sqlSelect(sqlQueryCheck5, sqlQueryCheck5Val, True)

    if result5['length'] > 0:
        myResponse['status'] = '1'   
        myText = f"""'{productLink}' Link Exists!"""
        myResponse['answer'] = gettext(myText)  
    
    return myResponse


def fileUpload(file, uploadDir):
   
    # uploadDir = 'images/thumbnails'
    # Save the file
    unique_filename = ''
    if file:
        # Split the filename into name and extension
        upload_to = os.path.join(static_folder_path, uploadDir)
        filename = secure_filename(file.filename)
        
        # name, ext = os.path.splitext(filename)
        file_path = os.path.join(upload_to, filename)
        
        unique_filename = filename
        
       # Check if the filename exists and create a unique filename if it does
        while os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            if '_' in name: # Check if the name contains an underscore
                arr = name.rsplit('_', 1)  # Split the name from the last underscore
                if arr[-1].isdigit(): # Check if the part after the underscore is a digit
                    # Increment the number and create a new unique filename
                    last_num = int(arr[-1]) + 1
                    unique_filename = f"{arr[0]}_{last_num}{ext}"
                   
                else:
                    unique_filename = f"{name}_1{ext}" # Append '_1' to the name to create a new unique filename
            else:
                unique_filename = f"{name}_1{ext}"  # Append '_1' to the name to create a new unique filename
            
            filename = unique_filename
            
            # Update the file path with the new unique filename
            file_path = os.path.join(upload_to, unique_filename)
            
        file.save(file_path)

    return unique_filename


def removeRedundantFiles(fileName, fileDir):
   
    # fileDir = 'images/thumbnails'
    # fileName = 'photo.jpg'

    # Create path to the file
    remove_from = os.path.join(static_folder_path, fileDir, fileName)

    if os.path.exists(remove_from):
        os.remove(remove_from)
        return True
    else:
        return False


def checkForRedundantFiles(fileName, colonName, tableName):

    sqlQuery = f"""SELECT  {colonName} FROM {tableName} WHERE {colonName} = %s; """
    sqlValTuple = (fileName,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    if result['length'] == 1:
        return True
    else:
        return False     


def getFileName(colonName, tableName, idName, idVal):
    sqlQuery = f"""SELECT {colonName} FROM {tableName} WHERE {idName} = %s;"""
    sqlValTuple = (idVal,)
    row = sqlSelect(sqlQuery, sqlValTuple, True)

    if row['length'] > 0 and row['data'][0][colonName] is not None:
        if len(row['data'][0][colonName]) > 0:
            return row['data'][0][colonName]
        else:
            return None
    else:
        return None
    

def get_meta_tags(content):
    ImageUrl = os.path.join(static_folder_path, 'static', content['ImageUrl'])

    # Facebook and instagram metatags
    metaMetaTags = f"""
        <meta property="og:title" content="{content['Title']}" />
        <meta property="og:description" content="{content['ShortDescription']}" />
        <meta property="og:image" content="{ImageUrl}" />
        <meta property="og:url" content="{content['Url']}" />
        <meta property="og:type" content="website" />
        <link rel="canonical" href="{content['Url']}" />
        <meta property="og:site_name" content="{content['SiteName']}" />
    """

    # Google metatags
    headline = content['Title']
    description = content['ShortDescription']
    image_url = ImageUrl
    author_name = "Author Name"
    publisher_name = "Publisher Name"
    logo_url = "https://www.example.com/logo.jpg"
    article_url = "https://www.example.com/article-page.html"
    date_published = 0 
    date_modified = 0

    if content['DatePublished'] is None:
        content['DatePublished'] = 0   
    elif content['DateModified'] is None:
        content['DateModified'] = 0   
    elif content['DatePublished'] > content['DateModified']:
        date_published = content['DatePublished'] 
        date_modified = content['DatePublished']
    else:
        date_published = content['DatePublished'] 
        date_modified = content['DateModified']


   

    # Create the meta tags with variables
    googleMetaTags = f"""
        <script type="application/ld+json">
        {{
        "@context": "https://schema.org",
        "@type": "Product",
        "headline": "{headline}",
        "description": "{description}",
        "image": "{image_url}",
        
        "datePublished": "{date_published}",
        "dateModified": "{date_modified}",
        "mainEntityOfPage": {{
            "@type": "WebPage",
            "@id": "{content['Url']}"
        }}
        }}
        </script>
    """
    
    # "author": {{
    #     "@type": "Person",
    #     "name": "{author_name}"
    # }},
    
    # "publisher": {{
    #     "@type": "Organization",
    #     "name": "{publisher_name}",
    #     "logo": {{
    #     "@type": "ImageObject",
    #     "url": "{logo_url}"
    #     }}
    # }},

    metaTags = metaMetaTags + googleMetaTags
    return metaTags


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        
        userID = session.get("user_id")
        Action = f.__name__

        exeptionActions = ['stuff', 'login', 'logout']

        if Action not in exeptionActions:
            if permissions(userID, Action) == False:
                return redirect("/login")
                
        return f(*args, **kwargs)
    return decorated_function


def permissions(stuffID, Action):
    sqlQuery =  """
                SELECT 
                    `actions`.`Action`,
                    `actions`.`ActionName`,
                    `rol`.`Rol`
                FROM `actions` 
                    LEFT JOIN `rol` ON find_in_set(`actions`.`ID`, `rol`.`actionIDs`)
                    LEFT JOIN `position` ON find_in_set(`rol`.`ID`, `position`.`rolIDs`)
                    LEFT JOIN `stuff` ON `stuff`.`PositionID` = `position`.`ID`
                WHERE `stuff`.`ID` = %s AND `stuff`.`Status` = 1
                """
    sqlValTuple = (stuffID,)
    result = sqlSelect(sqlQuery, sqlValTuple, False)

    if result['length'] == 0:
        session.clear()
        return False
    
    # print(stuffID)
    for actionTuple in result['data']:
        # print(actionTuple[0] + ' ' + Action + '\n')
        if actionTuple[0] == Action:
            session['action_info'] = {'actionName': actionTuple[1], 'role': actionTuple[2]}
            action_info()
            return True
        
    return False

def generate_random_string():
    length = random.randint(35, 40)
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def generate_random_unique_string(table):
    randomStr = generate_random_string()
    sqlQuery = f"SELECT `Url` FROM {table} WHERE `Url` = %s;"
    sqlValTuple = (randomStr,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    while result['length'] > 0:
        randomStr = generate_random_string()
        sqlQuery = f"SELECT `Url` FROM {table} WHERE `Url` = %s;"
        sqlValTuple = (randomStr,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
    
    return randomStr



def get_full_website_name():
    # Get the scheme (http or https)
    scheme = request.scheme
    # Get the host (including www if present)
    host = request.host
    # Combine them to get the full URL
    full_website_name = f"{scheme}://{host}"
    return full_website_name


def dataModified(articleID):

    sqlQuery = "UPDATE `article` SET `DateModified` = CURDATE() WHERE `ID` = %s"
    sqlUpdateVal = (articleID,)
    result = sqlUpdate(sqlQuery, sqlUpdateVal)

    if result['status'] == '1':
        return True
    else:
        return False


def supportedLangsValues():   
    
    supportedLangsData = supported_langs()
    if len(supportedLangsData) > 1:
        for prefix in supported_langs:
            supportedLangsData.append(getLangdata(prefix))
    else:
        supportedLangsData = getLangdata(supported_langs[0])

    return supportedLangsData

def getDefLang():
    return {'id': 1, 'Prefix': 'hy', 'Language': 'Հայերեն'}
    # return {'id': 2, 'Prefix': 'en', 'Language': 'English'}


def getSupportedLangs():
    return ['en', 'hy', 'ru']

def getSupportedLangIDs():
    arr = supported_langs()
    return [lang['Language_ID'] for lang in arr]

def supported_langs():
    arr = [
            {'Language_ID': 1, 'Language': 'Հայերեն', 'Prefix':	'hy', 'Flag': 'am.svg'},
            {'Language_ID': 2, 'Language': 'English', 'Prefix':	'en', 'Flag': 'gb.svg'},
            {'Language_ID': 8, 'Language': 'Русский', 'Prefix':	'ru', 'Flag': 'ru.svg'}
          ]
    return arr


def getLangdatabyID(langID):
    if not isinstance(langID, int):
        langID = int(langID)
        
    supportedLangs = supported_langs()
    content = []
    for lang in supportedLangs:
        if lang['Language_ID'] == langID:
            content = lang  
            
    return content

    
def getUserID():
    return session.get('user_id', None)

def replace_spaces_in_text_nodes(html_content):
    def replace_spaces(match):
        text = match.group(1)
        # Replace only sequences of two or more spaces with the corresponding number of non-breaking spaces
        return re.sub(r' {2,}', lambda m: '&nbsp;' * len(m.group(0)), text)
    
    # Regex explanation:
    # 1. `>([^<]+)<` matches text content between any tags.
    # 2. `re.DOTALL` allows the `.` to match newlines as well.
    return re.sub(r'>([^<]+)<', lambda m: f">{replace_spaces(m)}<", html_content, flags=re.DOTALL)

# Dicts inside a list, tuple, set
def filter_multy_dict(data, filter):
    arr = set()
    
    for val in data:
        arr.add(val.get(filter, None))

    return arr


def totalNumRows(tableName, where='', sqlValTuple=()):
    sqlQuery = f""" SELECT * FROM {tableName} {where};"""
    # sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return result['length']




def generate_pagination_urls(page, numRows, pagination):
    urls = {
        "prev": None,
        "pages": [],
        "next": None
    }
    
    # Calculate the total number of pages
    total_pages = (numRows // pagination) + ( (numRows % pagination) // (numRows % pagination) )
    
    # Generate the URL for the previous page if page > 1
    if page > 1:
        url_prev = f"{url_for('team', _external=True)}/{page - 1}"
        urls["prev"] = url_prev
    
    # Generate URLs for each page
    for i in range(1, total_pages + 1):
        url_page = f"{url_for('team', _external=True)}/{i}"
        urls["pages"].append({
            "url": url_page,
            "active": (i == page)
        })
    
    # Generate the URL for the next page if page < total_pages
    if page < total_pages:
        url_next = f"{url_for('team', _external=True)}/{page + 1}"
        urls["next"] = url_next
    print(urls)
    return urls


def checkSPSSDataLen(spsID, languageID):
    if request.form.get('spsID'):
        longData = 0
        spssAnswer = ""
        sqlQuerySPS = """
        SELECT 
            `sub_product_specification`.`ID`,
            `sub_product_specification`.`Name`,
            `sub_product_specifications`.`Name` AS `Text`,
            `sub_product_specifications`.`ID` AS `spssID`,
            `sub_product_specifications`.`Status` AS `spssStatus`
        FROM `sub_product_specification`
            LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
            LEFT JOIN `sub_product_specifications` ON `sub_product_specifications`.`spsID` = `sub_product_specification`.`ID`
        WHERE `sps_relatives`.`Language_ID` = %s AND `sub_product_specification`.`ID` = %s
        ORDER BY `sub_product_specifications`.`Order`;
        """
        sqlValTupleSPS = (languageID, spsID)
        resultSPS = sqlSelect(sqlQuerySPS, sqlValTupleSPS, True)

        for row in resultSPS['data']:
            if request.form.get(str(row['spssID'])):
                Text = request.form.get(str(row['spssID']))
                
                if len(Text) > 255:
                    longData = 1
                    spssAnswer = spssAnswer + gettext('Text is too long for field ') + row['Text'] + '.<br/>'
        return [longData, spssAnswer]


def clientID_contactID(data): # returns clientID from table `clients` and contactID from table `client_contacts` 
    clientID, phoneID, emailID, addressID = [None, None, None, None]
   
    sqlQuery = "SELECT * FROM `clients` WHERE `Firstname` = %s AND `Lastname` = %s;"
    result = sqlSelect(sqlQuery, (data['firstname'].strip(), data['lastname'].strip()), True)
    if result['length'] > 0:
        clientID = result['data'][0]['ID']
    else:
        sqlQueryInsert = "INSERT INTO `clients` (`Firstname`, `Lastname`) VALUES (%s, %s);"
        sqlQueryTuple = (data['firstname'].strip(), data['lastname'].strip())
        result = sqlInsert(sqlQueryInsert, sqlQueryTuple)
        clientID = result['inserted_id']

        
    if data['email']:
        sqlQuery = "SELECT * FROM `emails` WHERE `email` = %s;"
        result = sqlSelect(sqlQuery, (data['email'].strip(),), True)
        if result['length'] > 0:
            email = data['email']
            emailID = result['data'][0]['ID']

    phone = data['phone'].strip()

    # Remove all parentheses, hyphens, spaces and 0 at the beggining
    phone = re.sub(r'[()\-\s]', '', phone)
    phone = data['country-code'] + re.sub(r'^0', '', phone)

    sqlQuery = "SELECT * FROM `phones` WHERE `phone` = %s;"
    result = sqlSelect(sqlQuery, (phone.strip(),), True)
    if result['length'] > 0:
        phoneID = result['data'][0]['ID']
    else:
        sqlInsertPhone = "INSERT INTO `phones` (`phone`, `clientID`) VALUES (%s, %s);"
        result = sqlInsert(sqlInsertPhone, (phone, clientID))
        phoneID = result['inserted_id']

    sqlQueryAddress = "SELECT * FROM `addresses` WHERE `address` = %s;"
    result = sqlSelect(sqlQuery, (data['address'].strip(),), True)
    if result['length'] > 0:
        addressID = result['data'][0]['ID']
    else:
        sqlQueryInsert = "INSERT INTO `addresses` (`address`, `clientID`) VALUES (%s, %s);"
        sqlQueryTuple = (data['address'].strip(), clientID)
        result = sqlInsert(sqlQueryInsert, sqlQueryTuple)
        addressID = result['inserted_id']


    if data['email'] and emailID == None:
        langID = getLangID()
        sqlQueryInsert = "INSERT INTO `emails` (`email`, `clientID`, `langID`) VALUES (%s, %s, %s);"
        sqlQueryTuple = (data['email'].strip(), clientID, langID)
        result = sqlInsert(sqlQueryInsert, sqlQueryTuple)
        emailID = result['inserted_id']

    
    sqlQueryContacts = "SELECT * FROM `client_contacts` WHERE `emailID` = %s AND `phoneID` = %s AND `addressID` = %s;"
    sqlValTuple = (emailID, phoneID, addressID)
    result = sqlSelect(sqlQueryContacts, sqlValTuple, True)
    if result['length'] > 0:
        contactID = result['data'][0]['ID']
    else:
        sqlQueryInsert = "INSERT INTO `client_contacts` (`emailID`, `phoneID`, `addressID`) VALUES (%s, %s, %s);"
        sqlValTuple = (emailID, phoneID, addressID)
        result = sqlInsert(sqlQueryInsert, sqlValTuple)
        contactID = result['inserted_id']

    return {'clientID': clientID, 'contactID': contactID}


def get_promo_code_id_affiliateID(promo):
    sqlQuery = """
                    SELECT 
                        `promo_code`.`ID`,
                        `stuff`.`ID` AS `affiliateID`      
                    FROM `promo_code`
                        LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`
                    WHERE `promo_code`.`Promo` = %s AND `promo_code`.`Status` = 1 AND `promo_code`.`expDate` >= CURRENT_DATE()      
                ;"""
    result = sqlSelect(sqlQuery, (promo,), True)
    if result['length'] > 0:
        return result['data'][0]
    else:
        return False

def get_create_email_id(email):
    sqlQuery = "SELECT `ID` FROM `emails` WHERE `email` = %s;"
    result = sqlSelect(sqlQuery, (email,), True)
    if result['length'] > 0:
        return result['data'][0]['ID']
    else:
        sqlQueryInsert = "INSERT INTO `emails` (`email`) VALUES (%s);"
        result = sqlInsert(sqlQueryInsert, (email,))    
        return result['inserted_id']
    

def calculate_price_promo(products, promo):
    
    if promo != '':
        # check products and promo validity 
        ptIDs = ''
        for row in products:
            ptIDs = ptIDs + str(row['ptID']) + ','

        ptIDs = ptIDs[:-1]    
        sqlQuery =  """
                    SELECT 
                        `product_type`.`ID` AS `ptID`,
                        `product_type`.`Price`,
                        `discount`.`discount`
                        -- `discount`.`discount_status`
                    FROM `promo_code` 
                        LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `discount`.`ptID`
                        LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                    WHERE `promo_code`.`Promo` = %s 
                        AND `promo_code`.`expDate` >= CURRENT_DATE() 
                        AND `promo_code`.`Status` = 1
                        AND `product`.`Product_Status` = 2
                        AND FIND_IN_SET(`product_type`.`ID`, %s)
                        AND `discount`.`Status` = 1
                    """
        sqlValTuple = (promo, ptIDs)
        # sqlValTuple = (promo, ptIDs)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        if result['length'] == 0:
            return {'status': "0", 'answer': "Invalid Promo Code"}

        # Deside prices with discount
        discountPrice = 0
        for row in result['data']:
            for r in products:
                if row['ptID'] == r['ptID']:
                    discountPrice = discountPrice + (row['Price'] * int(r['quantity']) * row['discount'] / 100)
        
        return {'status': "1", 'answer': discountPrice}

    else:
        return calculate_price(products)    
   

def calculate_price(products):
    ptIDs = ''
    for row in products:
        ptIDs = ptIDs + str(row['ptID']) + ','

    ptIDs = ptIDs[:-1]    
    sqlQuery =  """
                SELECT 
                    `product_type`.`ID` AS `ptID`,
                    `product_type`.`Price`                    
                FROM `product_type`
                WHERE find_in_set(`product_type`.`ID`, %s)
                    
                """
    sqlValTuple = (ptIDs,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        return {'status': "2"}

    # Calculate total price prices with discount
    totalPrice = 0
    for row in result['data']:
        for r in products:
            if row['ptID'] == r['ptID']:
                totalPrice = totalPrice + row['Price'] * int(r['quantity'])
    
    return {'status': "1", 'answer': totalPrice}


def insertIntoBuffer(data, pdID, smthWrong, languageID):
    # IMPORTANT
    # Do not forget to take into consideration the max quantity as well
    bufferQuantities = []
    bufferInsertRows = ''
    sqlUpdateQuantity = "UPDATE `quantity` SET `Quantity` = %s WHERE `ID` = %s;"
    ptIDs = ''

    for row in data['ptData']:
        ptIDs = ptIDs + str(row['ptID']) + ','

    ptIDs = ptIDs[:-1]    
    sqlQuaryStore = f"""
                    SELECT 
                        `quantity`.`ID` AS `quantityID`,
                        `quantity`.`Quantity`,
                        `quantity`.`maxQuantity`,
                        (SELECT SUM(q.`Quantity`) FROM `quantity` `q`
                            WHERE find_in_set(`q`.`ptRefKey`, `quantity`.`ptRefKey`)
                        AND `Status` = '1'
                        AND `expDate` >= CURDATE()) AS `totalQuantity`,
                        -- `product_type`.`ID` AS `ptID`,
                        `product_type_relatives`.`PT_Ref_Key` AS `ptID`,
                        `product_type`.`Price`,
                        `promo_code`.`Promo`,
                        `promo_code`.`ID` AS `promoID`,
                        `discount`.`discount`,
                        `discount`.`revard_value`,
                        `discount`.`revard_type`,
                        `stuff`.`ID` AS `affiliateID`
                    FROM `quantity` 
                        LEFT JOIN `store` ON `store`.`ID` = `quantity`.`storeID`
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_Ref_Key` = `quantity`.`ptRefKey` 
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
                        LEFT JOIN `promo_code` ON `promo_code`.`Promo` = %s 
                        LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID` 
                            AND `discount`.`ptRefKey` = `product_type_relatives`.`PT_Ref_Key`
                        LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`
                    WHERE find_in_set(`product_type_relatives`.`PT_Ref_Key`, %s)
                        AND `product_type_relatives`.`Language_ID` = %s 
                        AND `quantity`.`Quantity` > 0
                        AND `quantity`.`Status` = '1'
                        AND `quantity`.`expDate` >= CURDATE()
                    ORDER BY  `product_type`.`ID`,  `quantity`.`expDate`, `quantity`.`Quantity` DESC, `quantity`.`maxQuantity` DESC;
    """

    sqlValTuple = (data['promo'], ptIDs, languageID)
    result = sqlSelect(sqlQuaryStore, sqlValTuple, True)
    if result['length'] == 0:
        return {'status': "0", 'answer': smthWrong}  
    
    if data['promo'] != '' and result['data'][0]['promoID'] is None:
        return {'status': "2"}
    
    # This checks if there is corresponding amount of product in store
    for checkRow in data['ptData']:
        for checkR in result['data']:
            if checkRow['ptID'] == checkR['ptID']:
                QUANTITY = checkRow['quantity']
                maxAllowdQuantity = checkR['totalQuantity']
                if checkR['maxQuantity'] is not None:
                    maxAllowdQuantity = checkR['maxQuantity']

                if maxAllowdQuantity < QUANTITY:  
                    return {'status': "0", 'answer': smthWrong}  
                    # return {'status': "0", 'answer': smthWrong + 'maxAllowdQuantity is ' + str(maxAllowdQuantity) + ' and QUANTITY is ' + str(QUANTITY) + ' and ptID is ' + str(checkRow['ptID'])}  

    totalPrice = 0
    for row in data['ptData']:
        # print(f'showing row of ptData {row}')
        QUANTITY = row['quantity']
        for r in result['data']:
            if QUANTITY == 0:
                break
            
            if row['ptID'] == r['ptID']:
                # print(f'quantity before: ptID is {r["ptID"]} quantity is {r["Quantity"]} and QUANTITY is {QUANTITY}')
                                
                if r['Quantity'] >= QUANTITY:
                    if r['discount'] is not None:
                        totalPrice = totalPrice +  r['Price'] * QUANTITY - r['Price'] * QUANTITY * r['discount'] / 100
                    else:
                        totalPrice = totalPrice + r['Price'] * QUANTITY
                        


                    sqlUpdate(sqlUpdateQuantity, (r['Quantity']-QUANTITY, r['quantityID']))
                    bufferQuantities.append(
                        {
                            'quantityID': r['quantityID'],
                            'quantity': QUANTITY, 
                            'promo_code_id': r['promoID'], 
                            'promo_code': r['Promo'], 
                            'discount': r['discount'], 
                            'affiliateID': r['affiliateID'], 
                            'price': r['Price'], 
                            'ptID': r['ptID'],
                            'payment_details_id': pdID
                        })
                    break

                if r['Quantity'] < QUANTITY:
                    if r['discount'] is not None:
                        totalPrice = totalPrice + r['Price'] * r['Quantity']  - r['Price'] * r['Quantity'] * r['discount'] / 100
                    else:
                        totalPrice = totalPrice + r['Price'] * r['Quantity']
                        

                    sqlUpdate(sqlUpdateQuantity, (0, r['quantityID']))
                    QUANTITY = QUANTITY - r['Quantity']

                    bufferQuantities.append(
                        {
                            'quantityID': r['quantityID'],
                            'quantity': r['Quantity'], 
                            'promo_code_id': r['promoID'], 
                            'promo_code': r['Promo'], 
                            'discount': r['discount'], 
                            'affiliateID': r['affiliateID'], 
                            'price': r['Price'], 
                            'ptID': r['ptID'],
                            'payment_details_id': pdID
                        })
                    
                # print(f'quantity after: ptID is {r["ptID"]} quantity is {r["Quantity"]} and QUANTITY is {QUANTITY}')

    # insert into `buffer_store` bufferQuantities
    bufferInsertRows = "(%s, %s, %s, %s, %s, %s, %s, %s, %s)," * len(bufferQuantities)
    bufferValuePrototype = []
    for row in bufferQuantities:
        for key, val in row.items():
            bufferValuePrototype.append(val)
    
    
    sqlInsertBuffer = f"INSERT INTO `buffer_store` (`quantityID`, `quantity`,`promo_code_id`, `promo_code`,  `discount`, `affiliateID`, `price`, `ptRefKey`,  `payment_details_id`) VALUES {bufferInsertRows[:-1]};"
    sqlValTupleBuffer = tuple(bufferValuePrototype)
    result = sqlInsert(sqlInsertBuffer, sqlValTupleBuffer)

    return {'status': '1', 'answer': bufferQuantities, 'totalPrice': totalPrice}

# INSERT into purchase_histore
# UPDATE payment_details
def insertPUpdateP(pdID, paymentData):
    sqlQuery = """
                SELECT 
                `ptRefKey` AS `ptID`,
                SUM(`quantity`) AS `quantity`,
                `payment_details_id`,
                `promo_code_id`,
                `promo_code`,
                `discount`,
                `price`,
                `affiliateID`
            FROM `buffer_store` WHERE `payment_details_id` = %s 
            GROUP BY `ptRefKey`, `payment_details_id`, `promo_code_id`, `promo_code`, `discount`, `price`, `affiliateID`
            ;"""
    result = sqlSelect(sqlQuery, (pdID,), True)
    if result['length'] == 0:

        # print('FFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        # print(result['error'])
        # print('FFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        return {'status': '0', 'answer': result['error']}
    
    promoID, promo, affiliateID = [None, None, None]
    protoTuple = []
    answer = []
    for row in result['data']:
        if row['promo_code_id'] is not None:
            promoID = row['promo_code_id']
            promo = row['promo_code']

        if row['affiliateID'] is not None:    
            affiliateID = row['affiliateID']

        protoTuple.append(row['ptID'])
        protoTuple.append(row['quantity'])
        protoTuple.append(row['payment_details_id'])
        protoTuple.append(row['price'])
        protoTuple.append(row['discount'])
        protoTuple.append(2)

        answer.append({'ptID': int(row['ptID']), 'quantity': int(row['quantity'])})
    
    sqlValTuple = tuple(protoTuple)

    values = "(%s, %s, %s, %s, %s, %s)," * len(result['data'])
    sqlQueryInsert = f"""
                    INSERT INTO `purchase_history` 
                    (`ptRefKey`, `quantity`, `payment_details_id`, `price`, `discount`, `Status`)
                    VALUES {values[:-1]};
                    """
    
    result = sqlInsert(sqlQueryInsert, sqlValTuple)
    if result['status'] == 0:
        return {'status': '0', 'answer': result['answer']}
    

    if affiliateID is not None:
        sqlQueryAff = """SELECT
                            `purchase_history`.`ID`,	
                            `purchase_history`.`ptRefKey` AS `ptID`,	
                            `purchase_history`.`quantity`,		
                            `purchase_history`.`price`,	
                            -- `purchase_history`.`discount`,
                            `discount`.`promo_code_id`,
                            `promo_code`.`Promo` AS `promo_code`,
                            `discount`.`revard_value`,
                            `discount`.`revard_type`
                        FROM `purchase_history` 
                            LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                            LEFT JOIN `discount` ON `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                            LEFT JOIN `promo_code` ON `discount`.`promo_code_id` = `promo_code`.`ID`
                        WHERE `payment_details_id` = %s AND `purchase_history`.`discount` is not null;"""
        
        resultAff = sqlSelect(sqlQueryAff, (pdID,), True)
        values = "(%s, %s, %s, %s, %s, %s)," * resultAff['length']
        protoTupleAff = []
        sqlQueryInsertAFF = f"INSERT INTO `affiliate_history` (`purchase_history_id`, `affiliateID`, `promo_code_id`, `promo_code`, `revard_value`, `revard_type`) VALUES{values[:-1]}"
        for row in resultAff['data']:
            protoTupleAff.append(row['ID'])
            protoTupleAff.append(affiliateID)
            protoTupleAff.append(row['promo_code_id'])
            protoTupleAff.append(row['promo_code'])
            protoTupleAff.append(row['revard_value'])
            protoTupleAff.append(row['revard_type'])
        
        sqlVTAff = tuple(protoTupleAff)
        resultInsertAff = sqlInsert(sqlQueryInsertAFF, sqlVTAff)
        if resultInsertAff['status'] == 0:
            return {'status': '0', 'answer': resultInsertAff['answer']}
    
    sqlQueryPaymentD = """
                        UPDATE `payment_details` SET 
                            `promo_code_id` = %s,
                            `promo_code` = %s,
                            `affiliateID` = %s,
                            `final_price` = %s,
                            `payment_method` = %s,
                            `CMD` = %s,
                            `payment_status` = %s,
                            `timestamp` = NOW(),
                            `Status` = 2 
                        WHERE `ID` = %s
                        ;"""
    sqlUpdate(sqlQueryPaymentD, (promoID, promo, affiliateID, paymentData['finalPrice'], paymentData['paymentMethod'], paymentData['CMD'], paymentData['paymentStatus'], pdID))
    return {'status': '1', 'answer': answer}


# delete from bufer and update table quantity
# update payment_details with id pdID
def deletePUpdateP(pdID):
    sqlQuery = """"
            SELECT 
                `quantityID`,
                `quantity`
        FROM `buffer_store` WHERE `payment_details_id` = %s 
        ;"""
    result = sqlSelect(sqlQuery, (pdID,), True)
    if result['length'] == 0:
        return {'status': '0'}
    
    for row in result['data']:
        sqlUpdateQuantity = "UPDATE `quantity` SET `Quantity` = `Quantity` + %s WHERE `ID` = %s;"
        sqlUpdate(sqlUpdateQuantity, (row['quantity'], row['quantityID']))
    
    sqlQueryDelete = "DELETE FROM `buffer_store` WHERE `payment_details_id` = %s;"
    sqlDelete(sqlQueryDelete, (pdID,))
    
    sqlQueryPaymentD = """
                        UPDATE `payment_details` SET
                            `Status` = 3 -- 3 means canceled
                        WHERE `ID` = %s
                        ;"""
    sqlUpdate(sqlQueryPaymentD, (pdID,))
    return {'status': '1'}


def get_affiliate_reward_progress(affiliateID):
    languageID = getLangID()
    sqlQuery = f"""
                SELECT
                    `payment_details`.`affiliateID`,

                    -- SUM UP Voided Revards
                    (SELECT
                        SUM(CASE
                            WHEN `discount`.`revard_type` =  1
                                THEN `discount`.`revard_value` * `purchase_history`.`quantity`
                            ELSE  `purchase_history`.`quantity` * `purchase_history`.`price` * `discount`.`revard_value` / 100
                        END)
                    FROM `purchase_history`
                        LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                        LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_Ref_Key` = `purchase_history`.`ptRefKey` 
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
                        LEFT JOIN `discount` ON `discount`.`ptRefKey` = `product_type_relatives`.`PT_Ref_Key`
                            AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                    WHERE `payment_details`.`affiliateID` = %s
                        AND `product_type_relatives`.`Language_ID` = %s
                        AND `payment_details`.`Status` = 0
                        AND `purchase_history`.`discount` is not null
                    GROUP BY `payment_details`.`Status`) AS `Voided`,

                    -- SUM UP Pending Revards
                    (SELECT
                        SUM(CASE
                            WHEN `discount`.`revard_type` =  1
                                THEN `discount`.`revard_value` * `purchase_history`.`quantity`
                            ELSE  `purchase_history`.`quantity` * `purchase_history`.`price` * `discount`.`revard_value` / 100
                        END)
                    FROM `purchase_history`
                        LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                        LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_Ref_Key` = `purchase_history`.`ptRefKey` 
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
                        LEFT JOIN `discount` ON `discount`.`ptRefKey` = `product_type_relatives`.`PT_Ref_Key`
                            AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                    WHERE `payment_details`.`affiliateID` = %s
                        AND `product_type_relatives`.`Language_ID` = %s
                        AND `payment_details`.`Status` in (2,3,4)
                        AND `purchase_history`.`discount` is not null
                    GROUP BY `payment_details`.`affiliateID`) AS `Pending`,

                    -- SUM UP Approved Revards
                    (SELECT
                        SUM(CASE
                            WHEN `discount`.`revard_type` =  1
                                THEN `discount`.`revard_value` * `purchase_history`.`quantity`
                            ELSE  `purchase_history`.`quantity` * `purchase_history`.`price` * `discount`.`revard_value` / 100
                        END)
                    FROM `purchase_history`
                        LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                        LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_Ref_Key` = `purchase_history`.`ptRefKey`
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
                        LEFT JOIN `discount` ON `discount`.`ptRefKey` = `product_type_relatives`.`PT_Ref_Key`
                            AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                    WHERE `payment_details`.`affiliateID` = %s
                        AND `product_type_relatives`.`Language_ID` = %s
                        AND `payment_details`.`Status` = 5
                        AND `purchase_history`.`discount` is not null
                    GROUP BY `payment_details`.`Status`) AS `Approved`,

                    -- SUM UP Settled Revards
                    (SELECT SUM(`amount`) FROM `partner_payments` WHERE `affiliateID` = %s AND `type` = 1) AS `Settled`

                FROM `payment_details`
                    LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                    LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
                    LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                WHERE `payment_details`.`affiliateID` = %s 
                GROUP BY `payment_details`.`affiliateID`;
                """
    sqlValTuple = (affiliateID, languageID, affiliateID, languageID, affiliateID, languageID, affiliateID, affiliateID) 
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return result


def get_affiliates(filters=''):


    sqlQuery =  f"""SELECT 
                            `stuff`.`ID`,
                            CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `Initials`, 
                            `position`.`Position`
                        FROM `stuff`
                            LEFT JOIN `position` ON `position`.`ID` = `stuff`.`PositionID`
                        WHERE `stuff`.`Status` = %s 
                            AND find_in_set(%s, `position`.`rolIDs`)
                            {filters}; 
                    """
    return sqlSelect(sqlQuery, (1,1), True) 


def check_alias(alias, languageID):
    sqlQuery = f""" SELECT `url` FROM `product`
                    WHERE `ID` = (SELECT `P_ID` FROM `product_relatives` WHERE `P_Ref_Key` = %s AND `Language_ID` = %s);"""

    sqlValTuple = (alias, languageID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    
    if result['length'] > 0:
        return result['data'][0]['url']
    else:
        return False
    
def get_order_status_list():
    return {
        '0': gettext('Cancelled'),
        '1': gettext('Pending'),
        '2': gettext('Purchased'),
        '3': gettext('Preparing'),
        '4': gettext('Ready'),
        '5': gettext('Delivered')
    }



# Send email

MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')  
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')

# recipient = 'misha818m@gmail.com'

def send_email_mailgun(credentials):
    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": credentials['Sender'] + ' ' + credentials['From'],
            "to": [{credentials['To']}],
            "subject": credentials['Subject'],
            "text": "Testing Mailgun email sending with tracking.",
            "html": f"<html><body>{credentials['Content']}</body></html>",  
            "o:tracking": "yes"  # Enable tracking
        }
    )
    
    if response.status_code == 200:
        print("This is email ID ", response.json().get('id'))
        return {'status': '1', 'emailID': response.json().get('id')}  # Message ID for tracking
    else:
        print("This is Error Message ", response.text)
        return {'status': '0', 'answer': "Failed to send email:" + response.text} 

def check_delivery_status(message_id):
    # print("Waiting for status update...")
    time.sleep(10)  # Wait a bit to allow Mailgun to process
    response = requests.get(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/events",
        auth=("api", MAILGUN_API_KEY),
        params={"message-id": message_id}  # Remove <> from ID
    )
    
    if response.status_code == 200:
        events = response.json().get('items', [])
        answer = False
        for event in events:
            # print(f"Event: {event.get('event')}, Timestamp: {event.get('timestamp')}")
            if event.get('event') == 'delivered':
                answer = True
                
        return answer
    else:
        # print("Failed to fetch delivery status:", response.text)
        return answer


def check_rol_id(rollID):
    if not rollID.isdigit():
        return False
    
    sqlQuery =  """SELECT 
                        `stuff`.`ID`
                    FROM `stuff`
                        LEFT JOIN `position` ON `position`.`ID` = `stuff`.`PositionID`
                    WHERE `stuff`.`ID` = %s AND find_in_set(%s, `position`.`rolIDs`);
                """
    result = sqlSelect(sqlQuery, (session.get('user_id'), rollID), True)
    if result['length'] == 0:
        return False
    return True


# ── Silence cssutils warnings (they validate against CSS 2.1 by default) ──
cssutils.log.setLevel(logging.CRITICAL)

def inline_css(html_str: str, css_urls: list[str]) -> str:
    """
    Inlines class-based CSS from the given list of external stylesheets
    directly into each element’s `style` attribute, then removes `class="…"`
    from every element. Also adds `margin: 0; padding: 0;` to all <p> tags.

    Args:
        html_str (str): The input HTML as a unified string.
        css_urls (list[str]): Full URLs to CSS files (e.g. ["https://…/quill.snow.css"]).

    Returns:
        str: The modified HTML where every class-based rule has been inlined,
             all `class` attributes are stripped, and every <p> has zero margins/padding.
    """
    # 1) Build a mapping of classname -> concatenated CSS rules (cssText).
    class_styles: dict[str, str] = {}

    for url in css_urls:
        resp = requests.get(url)
        resp.raise_for_status()
        sheet = cssutils.parseString(resp.text)

        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                style_text = rule.style.cssText.strip()
                if not style_text:
                    continue

                for sel in rule.selectorText.split(','):
                    found = re.findall(r'\.([A-Za-z0-9_-]+)', sel)
                    for cls_name in found:
                        if cls_name in class_styles:
                            class_styles[cls_name] += '; ' + style_text
                        else:
                            class_styles[cls_name] = style_text

    # 2) Parse the HTML and inline all matching class styles onto each element.
    soup = BeautifulSoup(html_str, 'html.parser')

    for elem in soup.find_all(attrs={'class': True}):
        classes = elem.get('class', [])
        combined_rules: list[str] = []

        for cls in classes:
            if cls in class_styles:
                combined_rules.append(class_styles[cls])

        if combined_rules:
            existing = elem.get('style', '').rstrip(';')
            class_css = '; '.join(combined_rules).strip()
            if existing:
                new_style = existing + '; ' + class_css
            else:
                new_style = class_css
            elem['style'] = new_style.strip()

        del elem['class']

    # 3) Ensure every <p> has margin: 0; padding: 0;
    for p in soup.find_all('p'):
        existing = p.get('style', '').rstrip(';')
        extra = 'margin: 0; padding: 0'
        if existing:
            p['style'] = existing + '; ' + extra
        else:
            p['style'] = extra

    return str(soup)


def send_confirmation_email(pdID, trackOrderUrl):
    """
    Sends a confirmation email to the user after successful order placement.
    """

    sqlQuery = f"""
    SELECT 
        `payment_details`.`ID`,
        `payment_details`.`payment_method`,
        `payment_details`.`CMD`,
        `payment_details`.`promo_code`,   
        `payment_details`.`final_price`,   
        `clients`.`FirstName`,
        `clients`.`LastName`,
        `phones`.`phone`,
        `emails`.`email`,
        `addresses`.`address`,    
        `notes`.`note`,
        `product`.`Title` AS `prTitle`,
        `product_type`.`Title` AS `ptTitle`,
        `purchase_history`.`quantity`,
        `purchase_history`.`price`,
        `purchase_history`.`discount`
    FROM `payment_details` 
            LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
            LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
            LEFT JOIN `phones` ON `client_contacts`.`phoneID` = `phones`.`ID`
            LEFT JOIN `emails` ON `client_contacts`.`emailID` = `emails`.`ID`
            LEFT JOIN `addresses` ON `client_contacts`.`addressID` = `addresses`.`ID`
            LEFT JOIN `notes` ON `payment_details`.`notesID` = `notes`.`ID`
            LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
            LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_Ref_Key` = `purchase_history`.`ptRefKey` 
            LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
            -- LEFT JOIN `product_type` ON ``.`ptID` = `product_type`.`ID`
            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
    WHERE `payment_details`.`ID` = %s AND `product_type_relatives`.`Language_ID` = %s
    ORDER BY `product`.`Order`, `product_type`.`Order`;
"""
    result = sqlSelect(sqlQuery, (pdID, getLangID()), True)
    if result['length'] == 0:
        return False
    
    display = "display: none;"
    cp_price = ""
    if any(map(lambda row: row.get('discount'), result['data'])):
        display = ""
        cp_price = "text-decoration: line-through !important;"

    
    data = {
        "data": result['data'],
        "langPrefix": session.get('lang', 'en'),
        "type": "mailersend",
        "template": "dynemic.html",
        "subject": gettext("Payment Confirmation"),
        "mail_from": "info@mammysbread.am",
        "mail_from_user": gettext("company"),
        "mail_to": result['data'][0]['FirstName'] + ' ' + result['data'][0]['LastName'],
        "mail_to_email": result['data'][0]['email'],
        "main_url": get_full_website_name(),
        "logo_url": get_full_website_name() + '/static/images/logo.jpg',
        "logo_alt": gettext("company"),
        "text_0": gettext("Dear") + ' ' + result['data'][0]['FirstName'] + '! ' + gettext("Thank you for shopping with us. We are preparing your order now!"),
        "delivery_info": gettext("Delivery Information"),
        "Order": gettext("Order"),
        "order_number": "#" + str(pdID),
        "order_details": gettext("Order Details"),
        "product": gettext("Product"),
        "price": gettext("Price"),
        "total": gettext("Total"),
        "discount": gettext("Discount"),
        "discounted_price": gettext("Discounted Price"),
        "display": display,
        "cp_price": cp_price,
        "payment_method": gettext("Payment Method"),
        # "payment_details": result['data'][0]["payment_method"] + " **** " + str(result['data'][0]["CMD"]),
        "continue_shopping": gettext("Continue Shopping"),
        "continue_shopping_url": get_full_website_name() + '/products-client',
        "contact_us": gettext("Contact US"),
        "contact_us_url": get_full_website_name() + '/contacts',
        "track_order": gettext("Track Your Order"),
        "track_order_url": trackOrderUrl,
        "title": gettext("Order Confirmed!"),
        "header": gettext("Order Confirmed!"),
        'company_name': gettext("company"),
        'company_rights': gettext("Your Company. All rights reserved."),
        "company_address": "",
        "unsubscribe": gettext("unsubscribe"),
        "unsubscribe_url": get_full_website_name() + '/unsubscribe',
        "year": datetime.now().year,
        "fb_icon": "https://cdn-images.mailchimp.com/icons/social-block-v2/color-facebook-48.png",
        "insta_icon": "https://cdn-images.mailchimp.com/icons/social-block-v2/color-instagram-48.png",
        "youtube_icon": "https://cdn-images.mailchimp.com/icons/social-block-v2/color-youtube-48.png",
        "whatsapp_icon": "https://cdn-images.mailchimp.com/icons/social-block-v2/color-whatsapp-48.png",
        "telegram_icon": "",
        "fb_url": "",
        "insta_url": "",
        "youtube_url": "",
        "whatsapp_url": "",
        "telegram_url": "",
        "main_currency": MAIN_CURRENCY
    }
    # print(data)
    # resp = {'status_code': None}
    resp = requests.post("http://localhost:8000/send", json=data)
    return True if resp.status_code == 200 else False

# Usage
# msg_id = send_email_mailgun()
# if msg_id:
#     check_delivery_status(msg_id)
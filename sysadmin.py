from flask import session, redirect, jsonify, request
from dotenv import load_dotenv
from flask_babel import Babel, _, lazy_gettext as _l, gettext
from werkzeug.utils import secure_filename
from functools import wraps

import mysql.connector
from mysql.connector import pooling
import os
import re
import base64
import uuid
import random
import string
import time

load_dotenv()

# Determine the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the static folder path relative to the current script's directory
static_folder_path = os.path.join(current_dir, 'static')
target_directory = os.path.join(static_folder_path, 'images/quilljs')
os.makedirs(target_directory, exist_ok=True)

# Create a connection to the MySQL database
# db_connection = mysql.connector.connect(
#     host=os.getenv('LOCALHOST'),
#     user=os.getenv('USER'),
#     password=os.getenv('PASSWORD'),
#     database=os.getenv('DATABASE'),
#     connection_timeout=10
# )


dbconfig = {
    "database": os.getenv('DATABASE'),
    "user": os.getenv('MYSQL_USER'),
    "password": os.getenv('PASSWORD'),
    "host": os.getenv('LOCALHOST')
}

# dbconfig = {
#     "database": os.getenv('MYSQL_DATABASE'),
#     "user": os.getenv('MYSQL_USER'),
#     "password": os.getenv('MYSQL_PASSWORD'),
#     "host": os.getenv('MYSQL_HOST', 'db'),
#     "port": int(os.getenv('MYSQL_PORT', 3306))  # Use the correct port number
# }

pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    **dbconfig
)

# To get a connection from the pool
db_connection = pool.get_connection()


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


def sqlSelect(sqlQuery, sqlValuesTuple, myDict):
    error_message = 'No errors detected'
    myData = []
    dataLen = 0

    try:
        if myDict:
            myData = {}
            # cursor = db_connection.cursor(dictionary=True)
            db_connection, cursor = get_db_connection(True)
        else:
            db_connection, cursor = get_db_connection()

        if sqlValuesTuple:
            cursor.execute(sqlQuery, sqlValuesTuple)
        else:
            cursor.execute(sqlQuery)

        myData = cursor.fetchall()
        db_connection.commit()
        close_connection(db_connection)
        # cursor.close()
        if myData is not None:
            dataLen = len(myData)
        
    except Exception as e:
        error_message = f"An error occurred: {e}"

    return {'data': myData, 'length': dataLen, 'error': error_message}


def sqlInsert(sqlQuery, sqlValuesTuple):
    # Insert the content into the MySQL database
    inserted_id = None
    rows_affected = None
    status = 0
    try:
        cursor = db_connection.cursor()
        cursor.execute(sqlQuery, sqlValuesTuple)
        
        # Commit the transaction
        db_connection.commit()
        
        # Check how many rows were affected
        rows_affected = cursor.rowcount
        inserted_id = cursor.lastrowid        

        # Close the cursor
        cursor.close()
        
        # Check if rows were affected
        if rows_affected > 0:
            status = 1
            answer = f"Query executed successfully, {rows_affected} rows affected."
        else:
            status = 1
            answer = "Query executed successfully, but no rows were affected."

    except Exception as e:
        answer = f"An error occurred: {e}"

    return {'answer': answer, 'inserted_id': inserted_id, 'rows_affected': rows_affected, 'status': status}



def sqlUpdate(sqlQuery, sqlValuesTuple=''):
    # Update the content from the MySQL database
    rows_affected = None
    status = '-1'
    try:
        cursor = db_connection.cursor()
        cursor.execute(sqlQuery, sqlValuesTuple)
        
        # Commit the transaction
        db_connection.commit()
        
        # Check how many rows were affected
        rows_affected = cursor.rowcount

        # Close the cursor
        cursor.close()
        
        # Check if rows were affected
        if rows_affected > 0:
            answer = f"Query executed successfully, {rows_affected} rows affected."
            status = '1'
            # answer = gettext('Done!')
        else:
            answer = "Query executed successfully, but no rows were affected."
            status = '1'

    except Exception as e:
        answer = f"An error occurred: {e}"

    return {'status': status, 'answer': answer, 'rows_affected': rows_affected}


def sqlDelete(sqlQuery, sqlValuesTuple):
    
    try:
        # Get a connection from the pool
        conn = pool.get_connection()
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
        if conn:
            conn.close()

    return {'status': status, 'answer': answer}

def getLangID():

    defLang = getDefLang()

    currentLangPrefix = session.get('lang', defLang['Prefix'])
    supportedLangs = supported_langs()
    for lang in supportedLangs:
        if currentLangPrefix == lang['Prefix']:
            langID = lang['Language_ID']

    return langID


# def getLangdata(Prefix):

#     sqlQuery = "SELECT * FROM `languages` WHERE `Prefix` = %s"
    
#     sqlValueTuple = (Prefix,)

#     result = sqlSelect(sqlQuery, sqlValueTuple, True)

#     content = {}
    
#     content['ID'] = result['data'][0]['Language_ID']
#     content['Language'] = result['data'][0]['Language']
#     content['Prefix'] = result['data'][0]['Prefix']

#     return content




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
        "@type": "Article",
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
                SELECT `actions`.`Action`
                    FROM `actions` 
                    LEFT JOIN `rol` ON find_in_set(`actions`.`ID`, `rol`.`actionIDs`)
                    LEFT JOIN `stuff` ON `stuff`.`RolID` = `rol`.`ID`
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
            return True
        
    return False

def generate_random_string():
    length = random.randint(35, 40)
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


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
        for prefix in supportedLangs:
            supportedLangsData.append(getLangdata(prefix))
    else:
        supportedLangsData = getLangdata(supportedLangs[0])

    return supportedLangsData

def getDefLang():
    return {'id': 2, 'Prefix': 'en', 'Language': 'English'}


def getSupportedLangs():
    return ['en', 'hy', 'ru']

def supported_langs():
    arr = [
            {'Language_ID': 2, 'Language': 'English', 'Prefix':	'en'},
            {'Language_ID': 8, 'Language': 'Русский', 'Prefix':	'ru'},
            {'Language_ID': 1, 'Language': 'Հայերեն', 'Prefix':	'hy'}
          ]
    return arr


def getLangdatabyID(langID):
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


def totalNumRows(tableName):
    sqlQuery = f""" SELECT * FROM {tableName};"""
    sqlValTuple = ()
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




# def replace_spaces_in_text_nodes(html_content):
#     # This regex will match text between HTML tags while ignoring attributes and tags themselves
#     def replace_spaces(match):
#         # Replace spaces in the text node with &nbsp;
#         return match.group(1).replace(' ', '&nbsp;')
    
#     # Regex explanation:
#     # 1. `>(.*?)<` matches text content between any tags.
#     # 2. `re.DOTALL` allows the `.` to match newlines as well.
#     return re.sub(r'>([^<]+)<', lambda m: f">{replace_spaces(m)}<", html_content, flags=re.DOTALL)


# Call the function
# if __name__ == "__main__":
#     removeRedundantFiles()

from flask import Flask, render_template, request, jsonify, session, redirect, g, url_for
from flask_babel import Babel, _, lazy_gettext as _l, gettext
from products import checkCategoryName, get_RefKey_LangID_by_link, get_article_category_images, edit_p_h, submit_reach_text, add_p_c_sql, edit_p_c_view, edit_p_c_sql, get_product_categories, get_thumbnail_images, add_product, productDetails, constructPrData, add_product_lang
from sysadmin import getLangdatabyID, supported_langs, get_full_website_name, generate_random_string, get_meta_tags, removeRedundantFiles, checkForRedundantFiles, getFileName, fileUpload, get_pr_id_by_lang, getDefLang, getSupportedLangs, getLangID, sqlSelect, sqlInsert, sqlUpdate, get_pc_id_by_lang, get_pc_ref_key, login_required
from werkzeug.security import check_password_hash, generate_password_hash

import os
from werkzeug.datastructures import FileStorage
from io import BytesIO
import json
import re

current_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

defLang = getDefLang()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['BABEL_DEFAULT_LOCALE'] = defLang['Prefix']
app.config['BABEL_SUPPORTED_LOCALES'] = getSupportedLangs()  # Supported languages here

babel = Babel(app)

def side_bar_stuff():
    stuffID = session.get("user_id")

    sqlQuery = f"""
    SELECT 
        `stuff`.`Firstname`,
        `stuff`.`Lastname`,
        `rol`.`Rol`,
        `actions`.`ActionName`,
        `actions`.`ActionDir`,
        `actions`.`ActionGroup`,
        `actions`.`ActionType`,
        `actions`.`Img`,
        `languages`.`Language`,
        `languages`.`Prefix`
    FROM `stuff`
    LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID`
    LEFT JOIN `actions` ON find_in_set(`actions`.`ID`, `rol`.`ActionIDs`)
    LEFT JOIN `languages` ON `languages`.`Language_ID` = `stuff`.`languageID`
    WHERE `stuff`.`ID` = %s AND `stuff`.`Status` = 1 AND `ActionType` = 1;    
    """

    sqlValTuple = (stuffID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    supportedLangsData = supported_langs()

    return render_template('side-bar-stuff.html', result=result['data'], supportedLangsData=supportedLangsData, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes
    # return result

# Handle Ajax request to submit content
@app.route('/submit_reach_text', methods=['POST'])
@login_required
def submit_r_t():
    # Get the content from the request data
    html_content = request.form.get('content')
    languageID = request.form.get('language-id')
    RefKey = request.form.get('RefKey')

    productID = get_pr_id_by_lang(RefKey, languageID)
    answer = submit_reach_text(html_content, productID)
    return jsonify({'status': answer['status']})
    

def get_locale():
    # Check if the language query parameter is set and valid
    supportedLangs = getSupportedLangs()
    if 'lang' in request.args:
        lang = request.args.get('lang')        
        if lang in supportedLangs:
            session['lang'] = lang
            return session['lang']
    # If not set via query, check if we have it stored in the session
    elif 'lang' in session:
        return session.get('lang')
    # Otherwise, use the browser's preferred language
    return request.accept_languages.best_match(supportedLangs)


def get_timezone():
    user = getattr(g, 'user', None)
    if user is not None:
        return user.timezone

babel = Babel(app, locale_selector=get_locale, timezone_selector=get_timezone)


@app.route('/setlang')
def setlang():
    defLang = getDefLang()
    lang = request.args.get('lang', defLang['Prefix'])
    session['lang'] = lang
    return redirect(request.referrer)


@app.context_processor
def inject_babel():
    return dict(_=gettext)

@app.context_processor
def inject_locale():
    # This makes the function available directly, allowing you to call it in the template
    return {'get_locale': get_locale}

@app.context_processor
def inject_babel():
    return dict(_=gettext)


@app.route('/')
def home():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`Language_ID` = %s
                    AND `Article_Status` = 2
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# Render the index.html template
@app.route('/<myLinks>')
def index(myLinks):
    content = get_RefKey_LangID_by_link(myLinks)
    supportedLangsData = []

    metaTags = ''
    if content is not None:  
        langData = getLangdatabyID(content['LanguageID'])
        session['lang'] = langData['Prefix']
        articleStatus = ' AND `article`.`Article_Status` = 2; '
        prData = constructPrData(content['RefKey'], articleStatus)
        articleStatusResult = prData.get('Status', 1)
        if articleStatusResult == 2:
            myHtml = 'article_client.html'
                        
            metaContent = prData
            metaContent['SiteName'] = request.host
            metaContent['Url'] = request.host + '/' + prData['Url']
            imageDir = 'images/thumbnails/' + prData['Thumbnail']
            metaContent['ImageUrl'] = url_for('static', filename=imageDir)

            prData['test'] = metaContent['ImageUrl']
            metaTags = get_meta_tags(prData)

            # Get active languages
            RefKey = content['RefKey']
            # sqlQueryL = "SELECT `Language_ID` FROM `article_relatives` WHERE `A_Ref_Key` = %s;"
            sqlQueryL = """
                        SELECT 
                            `article_relatives`.`Language_ID`,
                            `Url`
                        FROM `article_relatives`
                        LEFT JOIN `article` ON `article`.`ID` = `article_relatives`.`A_ID`
                        WHERE `A_Ref_Key` = %s AND `article`.`Article_Status` = 2;
                        """
            sqlValL = (RefKey,)
            resultL = sqlSelect(sqlQueryL, sqlValL, False)
            supportedLangsData = []
            if resultL['length'] > 1:
                langueges = supported_langs()

                for langdata in resultL['data']:
                    print('AAAAAAAAA')
                    print(langdata)
                    print('NNNNNNNNN')
                    for lang in langueges:
                        if lang['Language_ID'] == langdata[0]:
                            arr = (langdata[1], lang['Language'], lang['Prefix'])
                            supportedLangsData.append(arr)                        
        else:
            myHtml = 'error.html'
    else:
        myHtml = 'error.html'
        prData = ''
    return render_template(myHtml, prData=prData, supportedLangsData=supportedLangsData, metaTags=metaTags, current_locale=get_locale())


# Edit thumbnail image
@app.route('/thumbnail/<RefKey>', methods=['GET'])
@login_required
def thumbnail(RefKey):
    languageID = getLangID()
    sqlQuery = f"""
                    SELECT `thumbnail`, `AltText` FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`A_Ref_Key` = %s
                    AND  `article_relatives`.`Language_ID` = %s
                """ 
    
    sqlValTuple = (RefKey, languageID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    result['content'] = True
    if result['length'] == 0:
        result['content'] = False   
   
    
    # Get thumbnail images from other languages of the same article
    sqlQueryIMG = f"""
                    SELECT `thumbnail`, `AltText` FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`A_Ref_Key` = %s
                    AND `article_relatives`.`Language_ID` != %s
                """ 
    
    sqlValTupIMG = (RefKey, languageID)
    resultIMG = sqlSelect(sqlQueryIMG, sqlValTupIMG, True)

    thumbnailImages = get_thumbnail_images(RefKey)

    return render_template('thumbnail.html', content=result, resultIMG=resultIMG, thumbnailImages=thumbnailImages, languageID=languageID, RefKey=RefKey, errorMessage=False, current_locale=get_locale() ) 


# Render the article.html template
@app.route('/article/<RefKey>', methods=['GET'])
@login_required
def pd(RefKey):
    productTemplate = 'product.html'
    root_url = url_for('home', _external=True)
    errorMessage = False
    languageID = getLangID()
    supportedLangsData = supported_langs()

    productCategory = get_product_categories(None, languageID)
    prData = ''
    if RefKey is None:
         errorMessage = True
    if 'new' in RefKey.lower():      
        productTemplate = 'add_product.html'

        if len(RefKey) > 3:
            errorMessage = True
    else: 
        if RefKey.isdigit(): # Check if the variable is numeric
            prData = constructPrData(RefKey, '')

            if prData['content'] == True == prData['headers']: 
                productTemplate = 'product.html' 
                        
            if prData['content'] == True and prData['headers'] == False:
                
                pr_id = prData['ID']
                productCategory = get_product_categories(pr_id, languageID)

                pcRefKey = get_pc_ref_key(prData['Product_Category_ID']) 
                pcRefKeyLang = get_pc_id_by_lang(pcRefKey)
                productCategory['Product_Category_ID'] = pcRefKeyLang
                productTemplate = 'add_product_lang.html'
                prData['RefKey'] = RefKey

            if prData['content'] == False == prData['headers']: # Product with specified RefKey does not exist
                errorMessage = True       
                                          
        else:
            errorMessage = True
    
    if errorMessage == True:
        return render_template('error.html')
    else:
        sideBar = side_bar_stuff()
        return render_template(productTemplate, prData=prData, sideBar=sideBar, productCategory=productCategory, supportedLangsData=supportedLangsData, errorMessage=errorMessage, root_url=root_url, languageID=languageID, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# edit_thumbnail client-server transaction
@app.route('/edit_thumbnail', methods=['POST'])
# @login_required
def edit_thumbnail():

    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()

    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer}) 
    

    sqlQueryID = f"""
                    SELECT `A_ID`
                    FROM `article_relatives`
                    WHERE `article_relatives`.`A_Ref_Key` = %s
                        AND `article_relatives`.`Language_ID` = %s
                  """
    
    sqlQueryValId = (RefKey, languageID)

    resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    if resultID['length'] > 0:  
        articleID = resultID['data'][0]['A_ID']
    else:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer}) 
    
    state = json.loads(state)

    sqlImage = " `Thumbnail` = %s, "
    if state['status'] == 0: # Image was not changed
        sqlImage = ""
        sqlQueryVal = (altText, articleID)
    if state['status'] == 1: # Image was chosen from another language

        # Get Image name
        if getFileName('Thumbnail', 'article', 'ID', articleID):
            imageName = getFileName('Thumbnail', 'article', 'ID', articleID)

            if checkForRedundantFiles(imageName, 'Thumbnail', 'article'):
                removeRedundantFiles(imageName, 'images/thumbnails')

        sqlQueryVal = (state['file'], altText, articleID)

    if state['status'] == 2: # New image is uploaded   
        
        # Get Image name
        if getFileName('Thumbnail', 'article', 'ID', articleID):
            imageName = getFileName('Thumbnail', 'article', 'ID', articleID)
        
            if checkForRedundantFiles(imageName, 'Thumbnail', 'article'):
                removeRedundantFiles(imageName, 'images/thumbnails')
            
        file = request.files.get('file')
        unique_filename = fileUpload(file, 'images/thumbnails')

        sqlQueryVal = (unique_filename, altText,  articleID)
    
    sqlQuery   = f"""   
                    UPDATE `article`
                    SET 
                        {sqlImage}                       
                        `DateModified` = CURDATE(),
                        `AltText` = %s
                    WHERE `ID` = %s;
                 """

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result


    # languageID = request.form.get('languageID').strip()
    # RefKey = request.form.get('RefKey').strip()
    # altText = ''
    # if request.form.get('AltText'):
    #     altText = request.form.get('AltText').strip()
    # state = request.form.get('state')

    # if len(languageID) == 0 or len(RefKey) == 0:
    #     answer = gettext('Something is wrong!')
    #     return jsonify({'status': '0', 'answer': answer}) 
    
    # state = json.loads(state)

    # if state['status'] == 0:
    #     unique_filename = state['file']     
    # else:
    #     file = request.files.get('file')

    #     unique_filename = fileUpload(file, 'images/thumbnails')

    # sqlQueryID = f"""
    #                 SELECT `article`.`ID`
    #                 FROM `article`
    #                 LEFT JOIN `article_relatives` ON `article_relatives`.`A_ID` = `article`.`ID`
    #                 WHERE `article_relatives`.`A_Ref_Key` = %s
    #                 AND `article_relatives`.`Language_ID` = %s
    #                 """
    
    # sqlQueryValId = (RefKey, languageID)

    # resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    # if resultID['length'] > 0:  
    #     articleID = resultID['data'][0]['ID']
    # else:
    #     answer = gettext('Something is wrong!')
    #     return jsonify({'status': '0', 'answer': answer}) 

    # sqlQuery   = f"""   
    #                 UPDATE `article`
    #                 SET `thumbnail` = %s, `AltText` = %s
    #                 WHERE `ID` = %s;
    #              """
    
    # sqlQueryVal = (unique_filename, altText, articleID)

    # result = sqlUpdate(sqlQuery, sqlQueryVal)
    # return result


# add_article client-server transaction
@app.route('/add_article', methods=['POST'])
@login_required
def add_pr():

    if not request.form.get('productName'):
        answer = gettext('Title is empty!')
        return jsonify({'status': '2', 'answer': answer}) 
    elif not request.form.get('productLink'): 
        answer = gettext('Link is empty!')
        return jsonify({'status': '4', 'answer': answer}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Article Category!')
        return jsonify({'status': '6', 'answer': answer}) 
    
    productName = request.form.get('productName').strip()
    productLink = request.form.get('productLink').strip()
    CategoryID = request.form.get('CategoryID').strip()

    if request.form.get('languageID'):
        languageID = request.form.get('languageID').strip()

    altText = ''
    if request.form.get('altText'):
        altText = request.form.get('altText').strip()

    shortDescription = ''
    if request.form.get('short-description'):
        shortDescription = request.form.get('short-description').strip()

    longDescription = ''  
    if request.form.get('long-description'):
        longDescription = request.form.get('long-description').strip()

    RefKey = ''  
    if request.form.get('RefKey'):
        RefKey = request.form.get('RefKey').strip()


    file = request.files.get('file')    

    return add_product(productName, productLink, languageID, CategoryID, file, altText, shortDescription, longDescription, RefKey)

# add article lang client-server transaction
@app.route('/add_article_lang', methods=['POST'])
@login_required
def add_pr_lang():

    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext('Something went wrong. Please try again!')
        return jsonify({'status': '0', 'answer': answer}) # productName is Empty
    
    RefKey = request.form.get('RefKey').strip()

    if not request.form.get('productName'):
        answer = gettext('Title is empty!')
        return jsonify({'status': '2', 'answer': answer}) 
    elif not request.form.get('productLink'): 
        answer = gettext('Link is empty!')
        return jsonify({'status': '4', 'answer': answer}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Article Category!')
        return jsonify({'status': '6', 'answer': answer}) 
    
    productName = request.form.get('productName').strip()
    productLink = request.form.get('productLink').strip()
    CategoryID = request.form.get('CategoryID').strip()

    if request.form.get('languageID'):
        languageID = request.form.get('languageID').strip()

    altText = ''
    if request.form.get('altText'):
        altText = request.form.get('altText').strip()

    shortDescription = ''
    if request.form.get('short-description'):
        shortDescription = request.form.get('short-description').strip()

    longDescription = ''  
    if request.form.get('long-description'):
        longDescription = request.form.get('long-description').strip()

    file = request.files.get('file')    
    
    return add_product_lang(productName, productLink, languageID, CategoryID, RefKey, altText, file, shortDescription, longDescription)


# edit article headers client-server transaction
@app.route('/edit_article_headers', methods=['POST'])
@login_required
def edit_pr_headers():


    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext('Something went wrong. Please try again!')
        return jsonify({'status': '0', 'answer': answer})
    elif not request.form.get('productName'):
        answer = gettext('Article name is empty!')
        return jsonify({'status': '2', 'answer': answer}) 
    elif not request.form.get('productLink'):
        answer = gettext('Article link is empty!')
        return jsonify({'status': '4', 'answer': answer}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Article Category!')
        return jsonify({'status': '6', 'answer': answer}) 
    
    productName = request.form.get('productName').strip()
    productLink = request.form.get('productLink').strip()
    languageID = request.form.get('languageID').strip()
    CategoryID = request.form.get('CategoryID').strip()
    RefKey = request.form.get('RefKey').strip()
   
    ShortDescription = ''
    if  request.form.get('short-description'):
        ShortDescription = request.form.get('short-description').strip()
    
    LongDescription = ''
    if  request.form.get('long-description'):
        LongDescription = request.form.get('long-description').strip()

    # return jsonify({'status': '0', 'answer': answer}) # Please Choose Product Category
    return edit_p_h(productName, productLink, languageID, CategoryID, RefKey, ShortDescription, LongDescription)


# Render the add_article_category.html template
@app.route('/add-article-category', methods=['GET'])
@login_required
def addPC():
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('add_product_category.html', sideBar=sideBar, languageID=languageID, current_locale=get_locale())


# add_product_category client-server transaction
@app.route('/add_article_category', methods=['POST'])
@login_required
def add_p_c():

    categoryName = request.form.get('categoryName')
    AltText = request.form.get('AltText')
    file = request.files.get('file')
    currentLanguage = request.form.get('languageID')

    if not categoryName:
        answer = gettext('Category name is empty!')
        return jsonify({'status': '2', 'answer': answer}) # categoryName is Empty
    
    
    return add_p_c_sql(categoryName, file, AltText, currentLanguage)


# Render the edit_product_category.html template
@app.route('/edit-article-category/<RefKey>', methods=['GET'])
@login_required
def edit_product_category(RefKey):
    content = edit_p_c_view(RefKey)
    pcImages = get_article_category_images(RefKey)
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('edit_product_category.html', sideBar=sideBar, content=content, pcImages=pcImages, languageID=languageID, RefKey=RefKey, current_locale=get_locale())



# edit_product_category client-server transaction
@app.route('/edit_article_category', methods=['POST'])
@login_required
def edit_p_c():
    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()
    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer}) 
    
    if request.form.get('categoryName'):
        categoryName = request.form.get('categoryName').strip()
    else:         
        answer = gettext('Category Name is empty!')
        return jsonify({'status': '0', 'answer': answer})
    
    categoryNameExists = checkCategoryName(RefKey, languageID, categoryName)
    if categoryNameExists == True:
        answer = gettext('Category Name Exists!')
        return jsonify({'status': '0', 'answer': answer})
    
    categoryStatus = request.form.get('categoryStatus')

    sqlQueryID = f"""
                    SELECT `AC_ID`
                    FROM `article_c_relatives`
                    WHERE `article_c_relatives`.`AC_Ref_Key` = %s
                    AND `article_c_relatives`.`Language_ID` = %s;
                  """
    
    sqlQueryValId = (RefKey, languageID)

    resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    if resultID['length'] > 0:  
        articleCategoryID = resultID['data'][0]['AC_ID']
    else:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer}) 
    
    state = json.loads(state)

    sqlImage = "`Article_Category_Images` = %s,"
    if state['status'] == 0:
        sqlImage = ""
        sqlQueryVal = (altText, categoryName, categoryStatus, articleCategoryID)
    if state['status'] == 1:
        # Get Image name
        if getFileName('Article_Category_Images', 'article_category', 'Article_Category_ID', articleCategoryID):
            imageName = getFileName('Article_Category_Images', 'article_category', 'Article_Category_ID', articleCategoryID)

            if checkForRedundantFiles(imageName, 'Article_Category_Images', 'article_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')

        sqlQueryVal = (state['file'], altText, categoryName, categoryStatus, articleCategoryID)
    if state['status'] == 2:    
        # Get Image name
        if getFileName('Article_Category_Images', 'article_category', 'Article_Category_ID', articleCategoryID):
            imageName = getFileName('Article_Category_Images', 'article_category', 'Article_Category_ID', articleCategoryID)
    
            if checkForRedundantFiles(imageName, 'Article_Category_Images', 'article_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')
            
        file = request.files.get('file')

        unique_filename = fileUpload(file, 'images/pc_uploads')
        sqlQueryVal = (unique_filename, altText, categoryName, categoryStatus, articleCategoryID)
    
    sqlQuery   = f"""   
                    UPDATE `article_category`
                    SET 
                        {sqlImage}                       
                        `AltText` = %s,
                        `Article_Category_Name` = %s,
                        `Article_Category_Status` = %s
                    WHERE `Article_Category_ID` = %s;
                 """

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result




# Publish/Unpublish article
@app.route('/publish', methods=['POST'])
@login_required
def publishA():

    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    ArticleStatus = request.form.get('articleStatus').strip()

    answer = gettext('Something is wrong!')

    if ArticleStatus is None or languageID is None or RefKey is None:
        return jsonify({'status': '0', 'answer': answer}) 
    
    articleID = get_pr_id_by_lang(RefKey, languageID)

    if articleID == False:
        return jsonify({'status': '0', 'answer': answer})
    
    # Published date
    sqlQueryPub = "SELECT `DatePublished` FROM `article` WHERE `ID` = %s"
    sqlQueryPubVal = (articleID,)
    resultPub = sqlSelect(sqlQueryPub, sqlQueryPubVal, True)

    if resultPub['data'][0]['DatePublished'] == None:
        sqlQuery = "UPDATE `article` SET `Article_Status` = %s, `DatePublished` = CURDATE() WHERE `ID` = %s"
    else:
        sqlQuery = "UPDATE `article` SET `Article_Status` = %s WHERE `ID` = %s"
    
    sqlValTuple = (ArticleStatus, articleID)
    result = sqlUpdate(sqlQuery, sqlValTuple)

    if result['status'] == '1':
        if ArticleStatus == '2':
            answer = gettext('Article is published')
        if ArticleStatus == '1':
            answer = gettext('Article is unpublished')
        return jsonify({'status': '1', 'answer': answer})
    else:
        return jsonify({'status': '0', 'answer': answer})


# Publish/Unpublish article
@app.route('/article-categories', methods=['GET'])
@login_required
def article_categories():
    languageID = getLangID()
    sqlQuery = """
                SELECT 
                    `Article_Category_ID`,
                    `Article_Category_Name`,
                    `Article_Category_Images`,
                    `Article_Category_Status`,
                    `AC_Ref_Key`
                FROM `article_category`
                LEFT JOIN `article_c_relatives` ON `article_c_relatives`.`AC_ID` = `article_category`.`Article_Category_ID` 
                WHERE `article_c_relatives`.`Language_ID` = %s
                ORDER BY `Article_Category_ID` DESC; 
               """
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    return render_template('article-categories.html', sideBar=sideBar, result=result, current_locale=get_locale())


@app.route('/team', methods=['GET'])
@login_required
def team():
    languageID = getLangID()
    sqlQuery = """
                SELECT 
                    `stuff`.`ID`,
                    `stuff`.`Firstname`,
                    `stuff`.`Lastname`,
                    `stuff`.`Email`,
                    `stuff`.`Status`,
                    `rol`.`Rol`
                FROM `stuff`
                LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID` 
                ; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    sideBar = side_bar_stuff()

    return render_template('team.html', result=result, sideBar=sideBar, current_locale=get_locale())

@app.route('/roles', methods=['GET'])
@login_required
def roles():
    languageID = getLangID()
    sqlQuery = """
                SELECT 
                    `rol`.`ID`,
                    `rol`.`Rol`,
                    `rol`.`Status`
                FROM `rol`
                ORDER BY `rol`.`ID` DESC 
                ; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    sideBar = side_bar_stuff()

    return render_template('roles.html', result=result, sideBar=sideBar, current_locale=get_locale())


@app.route('/add-role', methods=['GET', 'POST'])
@login_required
def add_role():
    if request.method == "POST":
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer})  
        
        languageID  = request.form.get('languageID')

        if len(request.form.get('Role')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer})  

        Role  = request.form.get('Role').strip()

        if len(request.form.get('Actions')) == 0:
            answer = gettext('Please choose at least on action')
            return jsonify({'status': '0', 'answer': answer})  

        Actions = request.form.get('Actions').strip()

        # Check whether role exists or not
        sqlQuery = "SELECT `Rol` FROM `rol` WHERE `Rol` = %s;"
        sqlValTuple = (Role,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" There is already a role called "{Role}" """
            return jsonify({'status': '0', 'answer': answer}) 
        

        sqlQuery = "INSERT INTO `rol` (`Rol`, `ActionIDs`) VALUES (%s, %s);"
        sqlValTuple = (Role, Actions)

        result = sqlInsert(sqlQuery, sqlValTuple)
        
        if result['inserted_id'] is not None:
            answer = result['answer']
            return jsonify({'status': '1', 'answer': answer}) 
        else:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': answer}) 
    else:
        languageID = getLangID()
        sqlQuery = """
                    SELECT 
                        `ID`,
                        `ActionName` AS `Name`
                    FROM `actions`
                    
                    ; 
                """
        sqlValTuple = ()
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        sideBar = side_bar_stuff()

        return render_template('add-role.html', result=result, sideBar=sideBar, languageID=languageID, current_locale=get_locale())


@app.route('/add-teammate', methods=['GET', 'POST'])
@login_required
def add_teammate():
    if request.method == "POST":
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer})  
        
        languageID  = request.form.get('languageID')


        if len(request.form.get('Email')) == 0:
            answer = gettext('Please specify email')
            return jsonify({'status': '0', 'answer': answer})  

        Email = request.form.get('Email').strip()

        # Validate email
        emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        # Check if the email matches the pattern
        if not re.match(emailPattern, Email):
            answer = gettext('Invalid email format')
            return jsonify({'status': '0', 'answer': answer})

        if len(request.form.get('RoleID')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer})  

        RoleID  = request.form.get('RoleID').strip()

        # Check whether Email exists or not in stuff and buffer tables
        sqlQuery = "SELECT `Email` FROM `stuff` WHERE `Email` = %s;"
        sqlValTuple = (Email,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists """
            return jsonify({'status': '0', 'answer': answer})
         
        sqlQuery = "SELECT `Email` FROM `buffer` WHERE `Email` = %s;"
        sqlValTuple = (Email,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists """
            return jsonify({'status': '0', 'answer': answer})
         
        # insert into buffer table
        uniqueURL = generate_random_string()

        # answer = uniqueURL
        # return jsonify({'status': '0', 'answer': answer})


        sqlQuery = "INSERT INTO `buffer` (`Email`, `RoleID`, `Url`, `Deadline`, `Status`) VALUES (%s, %s, %s, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 15 MINUTE), 0);"
        sqlValTuple = (Email, RoleID,  uniqueURL)

        result = sqlInsert(sqlQuery, sqlValTuple)
        
        if result['inserted_id'] is not None:

            sqlQuery = "SELECT * FROM `buffer` WHERE `ID` = %s;"
            sqlVal = (result['inserted_id'],)
            r = sqlSelect(sqlQuery, sqlVal, True)

            # Send email to the reciepient, do this on real server
            uniqueURL = get_full_website_name() + '/stuff-signup/' + r['data'][0]['Url']
            answer = r['data'][0]['Url']
            return jsonify({'status': '0', 'answer': uniqueURL}) 
        else:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': answer}) 
    else:
        languageID = getLangID()
        sqlQuery = """
                    SELECT 
                        `ID`,
                        `Rol`
                    FROM `rol`
                    ; 
                """
        sqlValTuple = ()
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        sideBar = side_bar_stuff()
        return render_template('add-teammate.html', result=result, sideBar=sideBar, languageID=languageID, current_locale=get_locale())


@app.route('/stuff-signup/<uniqueURL>', methods=['GET', 'POST'])
def stuff_signup(uniqueURL):
    if request.method == "POST":
        
        if len(request.form.get('Firstname')) == 0:
            answer = gettext('Please specify firstname')
            return jsonify({'status': '0', 'answer': answer})  

        Firstname = request.form.get('Firstname').strip()

        if len(request.form.get('Lastname')) == 0:
            answer = gettext('Please specify lastname')
            return jsonify({'status': '0', 'answer': answer})  

        Lastname = request.form.get('Lastname').strip()
        
        if len(request.form.get('Username')) == 0:
            answer = gettext('Please specify username')
            return jsonify({'status': '0', 'answer': answer})  

        Username = request.form.get('Username').strip()
        
        # Check if username exists in stuff tables
        sqlQuery = "SELECT `Username` FROM `stuff` WHERE `Username` = %s;"
        sqlValTuple = (Username,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = gettext('Username exists')
            return jsonify({'status': '0', 'answer': answer})
          
        
        if len(request.form.get('Password')) == 0:
            answer = gettext('Please specify Password')
            return jsonify({'status': '0', 'answer': answer})  
        
        passwordErrors = validate_password(request.form.get('Password'))

        if len(passwordErrors) > 0:
            return jsonify({'status': '2', 'answer': passwordErrors})  

        if len(request.form.get('Password2')) == 0:
            answer = gettext('Password confirmation field is empty')
            return jsonify({'status': '0', 'answer': answer})  
        
        if request.form.get('Password') != request.form.get('Password2'):
            answer = gettext('Passwords do not match!')
            return jsonify({'status': '0', 'answer': answer})  
        
        if len(request.form.get('LanguageID')) == 0:
            answer = gettext('Please specify prefared language')
            return jsonify({'status': '0', 'answer': answer})  
        
        LanguageID = request.form.get('LanguageID')

        Hash = generate_password_hash(request.form.get('Password'))
        
        # Get data from buffer
        sqlQuery = "SELECT * FROM `buffer` WHERE `Url` = %s AND `Status` = 0 AND `Deadline` > CURRENT_TIMESTAMP;"
        sqlValTuple = (uniqueURL,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        
        if result['length'] == 0:
            answer = gettext('The URL is expired')
            return jsonify({'status': '0', 'answer': answer}) 
        
        row = result['data'][0]
        Email = row['Email']
        RoleID = row['RoleID']
        BufferID = row['ID']

        sqlQuery = """INSERT INTO `stuff` (`Username`, `Password`, `Email`, `Firstname`, `Lastname`, `RolID`, `LanguageID`, `Status`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 1);"""

        sqlValTuple = (Username, Hash, Email, Firstname, Lastname, RoleID,  LanguageID)

        result = sqlInsert(sqlQuery, sqlValTuple)
        
        if result['inserted_id'] is None:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': answer})
        

        # Change status of buffer
        sqlQuery = "UPDATE `buffer` SET `Status` = 1 WHERE `ID` = %s;"
        sqlValTuple = (BufferID,)
        sqlUpdate(sqlQuery, sqlValTuple)

        return jsonify({'status': '1'}) 
        
    else:
      
        sqlQuery = "SELECT * FROM `buffer` WHERE `Url` = %s AND `Status` = 0 AND `Deadline` > CURRENT_TIMESTAMP;"
        sqlValTuple = (uniqueURL,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        # print('AAAAAAAAAAAAA')
        # print(result)
        # print(uniqueURL)
        # print('BBBBBBBBBBBBB')
        
        templateHTML = 'error.html'
        if result['length'] > 0:
            templateHTML = 'teammate-signup.html'
        
        

        languages = supported_langs()
     
        row = ''
        if result['length'] > 0:
            row = result['data'][0]

        return render_template(templateHTML,  row=row, languages=languages, current_locale=get_locale())


@app.route('/edit-role/<RoleID>', methods=['GET', 'POST'])
@login_required
def edit_role(RoleID):
    if request.method == "POST":
              
        if len(request.form.get('RoleID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer})  
        
        RoleID  = request.form.get('RoleID')
        
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrongdfd!')
            return jsonify({'status': '0', 'answer': answer})  
        
        languageID  = request.form.get('languageID')

        if len(request.form.get('Role')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer})  

        Role  = request.form.get('Role').strip()

        if len(request.form.get('Actions')) == 0:
            answer = gettext('Please choose at least on action')
            return jsonify({'status': '0', 'answer': answer})  

        Actions = request.form.get('Actions').strip()

        # Check whether role exists or not
        sqlQuery = "SELECT `Rol` FROM `rol` WHERE `Rol` = %s AND `ID` != %s;"
        sqlValTuple = (Role, RoleID)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" There is already a role called "{Role}" """
            return jsonify({'status': '0', 'answer': answer}) 
        

        sqlQuery = "UPDATE `rol` SET `Rol` = %s, `ActionIDs` = %s WHERE `ID` = %s;"
        sqlValTuple = (Role, Actions, RoleID)

        result = sqlUpdate(sqlQuery, sqlValTuple)
        
        if result['status'] == '1':
            # answer = result['answer']
            answer = 'Done'
            return jsonify({'status': '1', 'answer': answer}) 
        else:
            answer = result['answer']
            # answer = "Something is wrong!"
            return jsonify({'status': '0', 'answer': answer}) 
    else:
        languageID = getLangID()

        sqlQuery = "SELECT `ID`, `Rol`, `ActionIDs` FROM `rol` WHERE `ID` = %s;"
        sqlValTuple = (RoleID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        
        if result['length'] != 1:
            return render_template('error.html', current_locale=get_locale()) 

        sqlQueryActions = """
                    SELECT 
                        `ID`,
                        `ActionName` AS `Name`
                    FROM `actions`
                    
                    ; 
                """
        sqlValTupleActions = ()
        resultActions = sqlSelect(sqlQueryActions, sqlValTupleActions, True)
        sideBar = side_bar_stuff()

        return render_template('edit-role.html', row=result['data'][0], sideBar=sideBar, resultActions=resultActions, languageID=languageID, current_locale=get_locale())


# Publish/Unpublish article
@app.route('/stuff', methods=['GET'])
@login_required
def stuff():

    stuffID = session['user_id']
    # stuffID = 1

    sqlQuery = f"""
    SELECT 
        `stuff`.`Firstname`,
        `stuff`.`Lastname`,
        `rol`.`Rol`,
        `actions`.`ActionName`,
        `actions`.`ActionDir`,
        `actions`.`ActionGroup`,
        `actions`.`ActionType`,
        `actions`.`Img`,
        `languages`.`Language`,
        `languages`.`Prefix`
    FROM `stuff`
    LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID`
    LEFT JOIN `actions` ON find_in_set(`actions`.`ID`, `rol`.`ActionIDs`)
    LEFT JOIN `languages` ON `languages`.`Language_ID` = `stuff`.`languageID`
    WHERE `stuff`.`ID` = %s AND `stuff`.`Status` = 1 AND `ActionType` = 1;    
    """

    sqlValTuple = (stuffID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    supportedLangsData = supported_langs()
    
    return render_template('admin_panel.html', result=result, supportedLangsData=supportedLangsData, current_locale=get_locale())


@app.route('/articles', methods=['GET'])
@login_required
def articles():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    LEFT JOIN `article_category` 
                      ON `article_category`.`Article_Category_ID` = `article`.`Article_Category_ID`
                    WHERE `article_relatives`.`Language_ID` = %s                    
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    return render_template('articles.html', result=result, sideBar=sideBar, current_locale=get_locale()) 

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        # Validate email
        # email = request.form.get('email').strip()
        # email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        # # Check if the email matches the pattern
        # if not re.match(email_pattern, email):
        #     response = {'status': '0', 'message': 'Invalid email format'}
        #     return jsonify(response)
        
        # Checking username
        username = request.form.get('username') 
        if not username:
            answer = gettext('Please specify username')
            response = {'status': '0', 'answer': answer}
            return jsonify(response)
        

        # Checking passwords 
        password = request.form.get('password') 
        if not password:
            answer = gettext('Please specify password')
            response = {'status': '0', 'answer': answer}
            return jsonify(response)
        
        sqlQuery = "SELECT * FROM `stuff` WHERE `Username` = %s"
        sqlValTuple  = (username,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)    
        

        if result['length'] == 1 and check_password_hash(result['data'][0]["Password"], password): 
            session['user_id'] = result['data'][0]['ID']
            response = {'status': '1'}
            return jsonify(response)
        else:
            answer = gettext('The username or password do not match')
            response = {'status': '0', 'answer': answer}
            return jsonify(response)
        
    else:
        if 'user_id' in session:
            return redirect('/stuff')
        
        return render_template("login.html", current_locale=get_locale())


# @app.route("/superpassword", methods=['GET'])
# def superpassword1234():
#     password = generate_password_hash('1234')

#     sqlQuery = "UPDATE `stuff` SET `Password` = %s WHERE `ID` = %s"
#     sqlValTuple = (password, 2)

#     result = sqlUpdate(sqlQuery, sqlValTuple)

#     return result['answer']

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



def validate_password(password):

    # Define password validation criteria
    min_length = 8
    max_length = 64
    must_have_digit = True
    must_have_uppercase = True
    must_have_lowercase = True
    must_have_special = True

    # Check if the password meets the criteria
    errors = []

    if len(password) < min_length or len(password) > max_length:
        answer =  gettext('The password must be between ') + str(min_length) + gettext(' and ') + str(max_length) + gettext(' characters long.')
        errors.append(answer)

    if must_have_digit and not any(char.isdigit() for char in password):
        errors.append(gettext('The password must contain at least one digit.'))

    if must_have_uppercase and not any(char.isupper() for char in password):
        errors.append(gettext('The password must contain at least one uppercase letter.'))

    if must_have_lowercase and not any(char.islower() for char in password):
        errors.append(gettext('The password must contain at least one lowercase letter.'))

    if must_have_special and not any(not char.isalnum() for char in password):
        errors.append(gettext('The password must contain at least one special character.'))

    return errors




if __name__ == '__main__':
    app.run(debug=True)

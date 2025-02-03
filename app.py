from flask import Flask, render_template, request, jsonify, session, redirect, g, url_for
from flask_babel import Babel, _, lazy_gettext as _l, gettext
from products import slidesToEdit, checkCategoryName, checkProductCategoryName, get_RefKey_LangID_by_link, get_article_category_images, get_product_category_images, edit_p_h, edit_a_h, submit_reach_text, submit_product_text, add_p_c_sql, edit_p_c_view, edit_a_c_view, edit_p_c_sql, get_product_categories, get_article_categories, get_ar_thumbnail_images, get_pr_thumbnail_images, add_product, productDetails, constructPrData, add_product_lang
from sysadmin import checkSPSSDataLen, replace_spaces_in_text_nodes, totalNumRows, filter_multy_dict, getLangdatabyID, supported_langs, get_full_website_name, generate_random_string, get_meta_tags, removeRedundantFiles, checkForRedundantFiles, getFileName, fileUpload, get_ar_id_by_lang, get_pr_id_by_lang, getDefLang, getSupportedLangs, getLangID, sqlSelect, sqlInsert, sqlUpdate, sqlDelete, get_pc_id_by_lang, get_pc_ref_key, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from OpenSSL import SSL
import os
from io import BytesIO
import json
import re
import copy

current_dir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

defLang = getDefLang()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['BABEL_DEFAULT_LOCALE'] = defLang['Prefix']
app.config['BABEL_SUPPORTED_LOCALES'] = getSupportedLangs()  # Supported languages here

csrf = CSRFProtect(app)
babel = Babel(app)
PAGINATION = os.getenv('PAGINATION')
PAGINATION_BUTTONS_COUNT = os.getenv('PAGINATION_BUTTONS_COUNT')
MAIN_CURRENCY = os.getenv('MAIN_CURRENCY')

# basedir = os.path.abspath(os.path.dirname(__file__))
# SSL context creation
# context = SSL.Context(SSL.TLSv1_2_METHOD)
# context.use_privatekey_file(os.path.join(basedir, 'certs', 'private.key'))
# context.use_certificate_file(os.path.join(basedir, 'certs', 'certificate.crt'))

key_file = os.path.join(basedir, 'certs', 'private.key')
cert_file = os.path.join(basedir, 'certs', 'certificate.crt')

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400

smthWrong = 'Something went wrong. Please try again!'

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

    return render_template('side-bar-stuff-1.html', result=result['data'], supportedLangsData=supportedLangsData, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes
    # return result


@app.route('/submit_product_text', methods=['POST'])
# @login_required
def submit_product_t():
    newCSRFtoken = generate_csrf()
        
    # return jsonify({'status': 'I am here', 'newCSRFtoken': newCSRFtoken})
    # Get the content from the request data
    html_content = request.form.get('content')
    languageID = request.form.get('language-id')
    RefKey = request.form.get('RefKey')

    productID = get_pr_id_by_lang(RefKey, languageID)
    answer = submit_product_text(html_content, productID)
    return jsonify({'status': answer['status'], 'newCSRFtoken': newCSRFtoken})
    

@app.route('/submit_reach_text', methods=['POST'])
@login_required
def submit_r_t():
    newCSRFtoken = generate_csrf()
        
    # Get the content from the request data
    html_content = request.form.get('content')
    languageID = request.form.get('language-id')
    RefKey = request.form.get('RefKey')

    # html_content = replace_spaces_in_text_nodes(html_content)

    productID = get_ar_id_by_lang(RefKey, languageID)
    answer = submit_reach_text(html_content, productID)
    return jsonify({'status': answer['status'], 'newCSRFtoken': newCSRFtoken})
    

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
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    AND `Product_Status` = 2
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes

@app.route('/about')
def about():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`Language_ID` = %s
                    AND `Article_Status` = 2
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='about', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/contacts')
def contacts():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `article` 
                    LEFT JOIN `article_relatives`
                      ON  `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`Language_ID` = %s
                    AND `Article_Status` = 2
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='contacts', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# Render the index.html template
@app.route('/<myLinks>')
def index(myLinks):
    content = get_RefKey_LangID_by_link(myLinks)
    slideShow = []
    supportedLangsData = []
    metaTags = ''

    if content is not None:  
        langData = getLangdatabyID(content['LanguageID'])
        session['lang'] = langData['Prefix']
        if content['Type'] == 'product':
            productStatus = ' AND `product`.`Product_Status` = 2; '
            prData = constructPrData(content['RefKey'], productStatus)
            productStatusResult = prData.get('Status', 1)
            if prData.get('Product_ID') is not None: 
                slideShow = getSlides(prData['Product_ID'])

            if productStatusResult == 2:
                myHtml = 'product_client.html'
                            
                metaContent = prData
                metaContent['SiteName'] = request.host
                metaContent['Url'] = request.host + '/' + prData['Url']
                imageDir = 'images/pr_thumbnails/' + prData['Thumbnail']
                metaContent['ImageUrl'] = url_for('static', filename=imageDir)

                prData['test'] = metaContent['ImageUrl']
                metaTags = get_meta_tags(prData)

                # Get active languages
                RefKey = content['RefKey']
                # sqlQueryL = "SELECT `Language_ID` FROM `article_relatives` WHERE `A_Ref_Key` = %s;"
                sqlQueryL = """
                            SELECT 
                                `product_relatives`.`Language_ID`,
                                `Url`
                            FROM `product_relatives`
                                LEFT JOIN `product` ON `product`.`ID` = `product_relatives`.`P_ID`
                            WHERE `P_Ref_Key` = %s AND `product`.`Product_Status` = 2;
                            """
                sqlValL = (RefKey,)
                resultL = sqlSelect(sqlQueryL, sqlValL, False)
                supportedLangsData = []
                if resultL['length'] > 1:                    
                    langueges = supported_langs()

                    for langdata in resultL['data']:                        
                        for lang in langueges:
                            if lang['Language_ID'] == langdata[0]:
                                arr = (langdata[1], lang['Language'], lang['Prefix'])
                                supportedLangsData.append(arr)
                                    
            else:
                myHtml = 'error.html'

        if content['Type'] == 'article':            
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
                        for lang in langueges:
                            if lang['Language_ID'] == langdata[0]:
                                arr = (langdata[1], lang['Language'], lang['Prefix'])
                                supportedLangsData.append(arr)                        
            else:
                myHtml = 'error.html'            
            
    else:
        myHtml = 'error.html'
        prData = ''
    cartMessage = [ 
                    gettext("You have already added this product to the basket. You can change the quantity if You would like to."),
                    generate_csrf(),
                    gettext("In Basket")
    ]  
    return render_template(myHtml, cartMessage=cartMessage, prData=prData, slideShow=slideShow, supportedLangsData=supportedLangsData, metaTags=metaTags, current_locale=get_locale())


# Edit thumbnail image
@app.route('/pr-thumbnail/<RefKey>', methods=['GET'])
# @login_required
def pr_thumbnail(RefKey):
    languageID = getLangID()
    sqlQuery = f"""
                    SELECT `thumbnail`, `AltText` FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`P_Ref_Key` = %s
                    AND  `product_relatives`.`Language_ID` = %s
                """ 
    
    sqlValTuple = (RefKey, languageID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    result['content'] = True
    if result['length'] == 0:
        result['content'] = False   
   
    
    # Get thumbnail images from other languages of the same product
    sqlQueryIMG = f"""
                    SELECT `thumbnail`, `AltText` FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`P_Ref_Key` = %s
                    AND `product_relatives`.`Language_ID` != %s
                """ 
    
    sqlValTupIMG = (RefKey, languageID)
    resultIMG = sqlSelect(sqlQueryIMG, sqlValTupIMG, True)

    thumbnailImages = get_pr_thumbnail_images(RefKey)

    return render_template('pr_thumbnail.html', content=result, resultIMG=resultIMG, thumbnailImages=thumbnailImages, languageID=languageID, RefKey=RefKey, errorMessage=False, current_locale=get_locale() ) 
# End of edit product's thumbnail image

# Edit article's thumbnail image
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

    thumbnailImages = get_ar_thumbnail_images(RefKey)

    return render_template('thumbnail.html', content=result, resultIMG=resultIMG, thumbnailImages=thumbnailImages, languageID=languageID, RefKey=RefKey, errorMessage=False, current_locale=get_locale() ) 
# End of eidt article's thumbnail image


# View and Edit article
@app.route('/article/<RefKey>', methods=['GET'])
@login_required
def ar(RefKey):
    articleTemplate = 'articleVE.html'
    root_url = url_for('home', _external=True)
    errorMessage = False
    languageID = getLangID()
    supportedLangsData = supported_langs()

    articleCategory = get_article_categories(None, languageID)
    # productCategory = get_product_categories(None, languageID)
    prData = ''
    if RefKey is None:
         errorMessage = True
    if 'new' in RefKey.lower():      
        articleTemplate = 'add_article.html'

        if len(RefKey) > 3:
            errorMessage = True
    else: 
        if RefKey.isdigit(): # Check if the variable is numeric
            prData = constructPrData(RefKey, '')

            if prData['content'] == True == prData['headers']: 
                articleTemplate = 'articleVE.html' 
                        
            if prData['content'] == True and prData['headers'] == False:
                
                pr_id = prData['ID']
                productCategory = get_product_categories(pr_id, languageID)

                pcRefKey = get_pc_ref_key(prData['Product_Category_ID']) 
                pcRefKeyLang = get_pc_id_by_lang(pcRefKey)
                productCategory['Product_Category_ID'] = pcRefKeyLang
                articleTemplate = 'add_product_lang.html'
                prData['RefKey'] = RefKey

            if prData['content'] == False == prData['headers']: # Product with specified RefKey does not exist
                errorMessage = True       
                                          
        else:
            errorMessage = True
    
    if errorMessage == True:
        return render_template('error.html')
    else:
        sideBar = side_bar_stuff()
        return render_template(articleTemplate, prData=prData, sideBar=sideBar, productCategory=productCategory, supportedLangsData=supportedLangsData, errorMessage=errorMessage, root_url=root_url, languageID=languageID, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# View and Edit Product 
@app.route('/get_slides', methods=['POST'])
# @login_required
def get_slides():
    if not request.form.get('ProductID') or not request.form.get('languageID'):
        return []
    
    PrID = request.form.get('ProductID')
    LanguageID = request.form.get('languageID')
    result = slidesToEdit(PrID)

    return result

@app.route('/add-price/<prID>', methods=["GET"])
def add_price(prID):

    answer = gettext('Something is wrong! 0')
    # newCSRFtoken = generate_csrf()
    mainCurrency = MAIN_CURRENCY
    languageID = getLangID()
    prData = {'Product_ID': prID, 'LanguageID': languageID, 'prUpdate': gettext('Update'), 'prSaving': gettext('Saving...')}

    sqlQuery = f"""SELECT 
                        `sub_product_specification`.`ID`,
                        `sub_product_specification`.`Name`,
                        `product_relatives`.`P_Ref_Key`
                    FROM `sub_product_specification`
                        LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                        LEFT JOIN `product_relatives` ON `product_relatives`.`P_ID` = %s 
                    WHERE `sps_relatives`.`Language_ID` = %s 
                        AND `product_relatives`.`Language_ID` = %s 
                        AND `sub_product_specification`.`Status` = %s
                    ORDER BY `sub_product_specification`.`ID`;

                """
    sqlValTuple = (prID, languageID, languageID, 1)
    resultSPS = sqlSelect(sqlQuery, sqlValTuple, True)

    sqlQuery = f"""
                SELECT 
                    `sub_product_specification`.`ID`,
                    `sub_product_specification`.`Name` AS `SPS_NAME`,
                    `sub_product_specification`.`Status`,
                    `sub_product_specifications`.`ID` AS `SPSS_ID`,
                    `sub_product_specifications`.`Name` AS `Text`,
                    `sub_product_specifications`.`Order` AS `spsOrder`
                FROM `sub_product_specifications`
                LEFT JOIN `sub_product_specification` 
                    ON `sub_product_specifications`.`spsID` = `sub_product_specification`.`ID`
                WHERE `sub_product_specification`.`ID` = (
                    SELECT 
                        `product_category`.`spsID`
                    FROM `product_category`
                    LEFT JOIN `product_c_relatives` 
                        ON `product_c_relatives`.`PC_ID` = `product_category`.`Product_Category_ID`
                    LEFT JOIN `product` 
                        ON `product`.`Product_Category_ID` = `product_category`.`Product_Category_ID`
                    WHERE `product_c_relatives`.`Language_ID` = %s 
                    AND `product`.`ID` = %s 
                    LIMIT 1
                )
                ORDER BY `spsOrder`
                ;

            """
    sqlValTuple = (languageID, prID)
    resultSpecifications = sqlSelect(sqlQuery, sqlValTuple, True)
    

    return render_template('add-price.html', prData=prData, sps=resultSPS, specifications=resultSpecifications, mainCurrency=mainCurrency, current_locale=get_locale())


# Edit price view
@app.route('/edit-price/<ptID>', methods=['GET'])
# @login_required
def edit_price(ptID):
    languageID = getLangID()

    sqlQueryMain = f"""
                    SELECT `product_type`.`ID`,
                            `product_type`.`Title`,
                            `product_type`.`Price`,
                            `product_relatives`.`P_Ref_Key`,        
                            `product_type`.`spsID`,
                            `product_type`.`Order` AS `SubPrOrder`,
                            `slider`.`ID` AS `sliderID`,
                            `slider`.`Name`,
                            `slider`.`AltText`,
                            `slider`.`Order` AS `SliderOrder` 
                    FROM `product_type`
                    LEFT JOIN `slider` ON `slider`.`ProductID` = `product_type`.`ID`
                        AND `slider`.`Type` = 2
                    LEFT JOIN `product_relatives` ON `product_relatives`.`P_ID` = `product_type`.`Product_ID` 
                    WHERE `product_type`.`ID` = %s 
                    ORDER BY `SubPrOrder`  ASC, `slider`.`Order` ASC;
                    """
    sqlValTupleMain = (ptID,)
    mainResult = sqlSelect(sqlQueryMain, sqlValTupleMain, True)
    if mainResult['length'] == 0:
        return render_template('error.html')
    
    sqlQuerySpss = f"""
                        SELECT 
                            `sub_product_specifications`.`ID` AS `spssID`,
                            `sub_product_specifications`.`Name` AS `Key`,
                            `sub_product_specifications`.`spsID` AS `spsID`,
                            `sub_product_specifications`.`Order` AS `spssOrder`,
                            `product_type_details`.`ID` AS `ptdID`,
                            `product_type_details`.`Text` AS `Value`,
                            `product_type_details`.`spssID` AS `product_type_details_spssID`,
                            `product_type_details`.`productTypeID`
                        FROM 
                            `sub_product_specifications`
                        LEFT JOIN `product_type_details` ON `sub_product_specifications`.`ID` = `product_type_details`.`spssID` 
                            AND `product_type_details`.`productTypeID` = %s
                        WHERE `sub_product_specifications`.`spsID` = %s; 
                        """
    sqlValTupleSPSS = (ptID, mainResult['data'][0]['spsID'])
    resultSPSS = sqlSelect(sqlQuerySpss, sqlValTupleSPSS, True)
    

    sqlQuery = f"""SELECT 
                        `sub_product_specification`.`ID`,
                        `sub_product_specification`.`Name`
                    FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                    WHERE `sps_relatives`.`Language_ID` = %s AND `sub_product_specification`.`Status` = %s;

                """
    sqlValTuple = (languageID, 1)
    spsResult = sqlSelect(sqlQuery, sqlValTuple, True)
    
    sideBar = side_bar_stuff()
    return render_template('edit-price.html', sideBar=sideBar, mainResult=mainResult, sps=spsResult, resultSPSS=resultSPSS, languageID=languageID, current_locale=get_locale())


# Edit price action
@app.route('/editprice', methods=['POST'])
# @login_required
def editprice():
    newCSRFtoken = generate_csrf()
    ptID = request.form.get('PtID')

    if not ptID:
        answer = gettext(smthWrong)
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    if not request.form.get('title') or len(request.form.get('title').strip())  == 0:
        answer = gettext('Please specify the title!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 

    # Check weather Product Type Title exists for current product
    sqlQuery = """SELECT `Title` FROM `product_type` 
                    WHERE `Product_ID` = (SELECT `Product_ID` FROM `product_type` WHERE `ID` = %s LIMIT 1) 
                        AND `ID` != %s
                        AND `Title` = %s;
                    """
    sqlValTuple = (ptID, ptID, request.form.get('title'))
    resultCheck = sqlSelect(sqlQuery, sqlValTuple, True)

    if resultCheck['length'] > 0:
        answer = '"' + resultCheck['data'][0]['Title'] + '" ' +gettext('Product Type Title Already Exists!') 
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})    



    if not request.form.get('price') or len(request.form.get('price').strip())  == 0:
        answer = gettext('Please specify the price!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
  
    if int(request.form.get('price')) <= 0:
        answer = gettext('The price should be higher then 0!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
  
    if request.form.get('fileStatus') == '0':
        answer = gettext('At least one image should be uploaded')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    if request.form.get('spsID'):
        spsID = int(request.form.get('spsID'))
        languageID = getLangID()

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

        i = 0
        while True:
            if not request.form.get('spss_' + str(i)):
                break
            spss = request.form.get('spss_' + str(i))
            arr = spss.split(',', 1)
            Text = arr[1]
            

            if len(Text) > 255:
                longData = 1
                spssAnswer = spssAnswer + gettext('Text is too long for field ') + resultSPS['data'][i]['Text'] + '.<br/>'
            i += 1
        
        if longData == 1:
            spssAnswer += gettext('Max allowed characters are 255.')
            return jsonify({'status': '0', 'answer': spssAnswer, 'newCSRFtoken': newCSRFtoken})
    
    # Handle image upload
    sqlQueryMain = f"""
                    SELECT 
                            `slider`.`ID` AS `sliderID`,
                            `slider`.`Name`,
                            `slider`.`AltText`,
                            `slider`.`Order` AS `SliderOrder` 
                    FROM `product_type`
                    LEFT JOIN `slider` ON `slider`.`ProductID` = `product_type`.`ID`
                        AND `slider`.`Type` = 2
                    WHERE `product_type`.`ID` = %s 
                    ORDER BY `SliderOrder`;
                    """
    
    sqlValTupleMain = (ptID,)
    mainResult = sqlSelect(sqlQueryMain, sqlValTupleMain, True)
    if mainResult['length'] == 0:
        return render_template('error.html')

    # dataChecker = copy.deepcopy(mainResult['data'])  
    shortKeys = {}
    for row in mainResult['data']:
        shortKeys[row['sliderID']] = [row['Name'], row['SliderOrder'], row['AltText']]

    i = 0
    imgDir = 'images/sub_product_slider'
    sqlUpdateSlide = "UPDATE `slider` SET `AltText` = %s, `Order` = %s WHERE `ID` = %s"  
    sqlInsertSlide = "INSERT INTO `slider`  (`Name`, `AltText`, `Order`, `ProductID`, `Type`) VALUES (%s, %s, %s, %s, %s);"
    max_file_size = 5 * 1024 * 1024  # 5MB in bytes

    while True:
        if not request.form.get('upload_status_' + str(i)):
            break

        # Check image size and return an error if file is too big
        if request.files.get('file_' + str(i)):
            file = request.files.get('file_' + str(i))
            file_size = len(file.read())  # Get the file size in bytes
            file.seek(0)  # Reset the file pointer to the beginning after reading
                    
            filename = secure_filename(file.filename)

            if file_size > max_file_size:
                answer = '<<' +filename + '>>' + gettext('image size is more than 5MB')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        
        # End of checking the image size

        altText = request.form.get('alt_text_' + str(i))

        if request.form.get('upload_status_' + str(i)) == '1':
            if not request.form.get('slideID_' + str(i)):
                answer = gettext(smthWrong)
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
            
            slideID = request.form.get('slideID_' + str(i))
            if i != shortKeys[int(slideID)][1] or altText != shortKeys[int(slideID)][2]:

                sqlValTupleSlide = (request.form.get('alt_text_' + str(i)), i,  slideID)      
                resultUpdate = sqlUpdate(sqlUpdateSlide, sqlValTupleSlide)
                if resultUpdate['status'] == '-1':
                    answer = gettext(smthWrong)
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
            del shortKeys[int(slideID)]  

        # insert new image
        if request.form.get('upload_status_' + str(i)) == '0':
            file = request.files.get('file_' + str(i))
            unique_filename = fileUpload(file, imgDir)
            sqlValTuple = (unique_filename, altText, i, ptID, 2)
            result = sqlInsert(sqlInsertSlide, sqlValTuple)
            if result['status'] == 0:
                answer = gettext(smthWrong)
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

        i = i + 1
    
    sqlQueryDelete = "DELETE FROM `slider` WHERE `ID` = %s;"
    if len(shortKeys) > 0:
        for key, val in shortKeys.items():
            sqlValTuple = (key,)
            delResult = sqlDelete(sqlQueryDelete, sqlValTuple)
            if delResult['status'] == '-1':
                return jsonify({'status': '0', 'answer': delResult['answer'], 'newCSRFtoken': newCSRFtoken}) 

            # Del from folder
            removeResult = removeRedundantFiles(val[0], imgDir)
            if removeResult == False:
                answer = gettext(smthWrong)
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    # End of image upload

    # Sup product specifications
    sqlQueryPT = "SELECT `spsID` FROM `product_type` WHERE `ID` = %s;"
    sqlValTuplePT = (ptID,)
    resultPT = sqlSelect(sqlQueryPT, sqlValTuplePT, True)
    # print(resultPT['data'])
    title = request.form.get('title')
    price = request.form.get('price')
    if not request.form.get('spsID'):
        spsID = 0
    else:
        spsID = int(request.form.get('spsID'))


    sqlUpdatePriceTitle = "UPDATE `product_type` SET `title` = %s, `price` = %s, `spsID` = %s WHERE `ID` = %s;"
    sqlValTuple = (title, price, spsID, ptID)
    updateResult = sqlUpdate(sqlUpdatePriceTitle, sqlValTuple) 
    if updateResult['status'] == '-1':
        answer = gettext(smthWrong)
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    spsChecker = request.form.get('spsChecker')
    if spsChecker == '1':
        sqlQueryDel = "DELETE FROM `product_type_details` WHERE `productTypeID` = %s;"
        sqlValTuple = (ptID,)
        resultDelete = sqlDelete(sqlQueryDel, sqlValTuple)
        if resultDelete['status'] == '-1':
            answer = gettext(smthWrong)
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        

        sqlInsertPtDetails = "INSERT INTO `product_type_details` (`productTypeID`, `spssID`, `Text`) VALUES(%s, %s, %s)"
        i = 0
        while True:
            if not request.form.get('spss_' + str(i)):
                break
            spss = request.form.get('spss_' + str(i))        
            arr = spss.split(',', 1)
            if len(arr[1].strip()) > 0:
                sqlValTupleSpss = (ptID, int(arr[0]), arr[1])
                resultInsert = sqlInsert(sqlInsertPtDetails, sqlValTupleSpss)
                if resultInsert['status'] == 0:
                    answer = gettext(smthWrong)
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 

            i += 1
        

    answer = gettext('Done!')
    return jsonify({'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken})


# View and Edit Product 
@app.route('/product/<RefKey>', methods=['GET'])
@login_required
def pd(RefKey):
    productTemplate = 'product.html'
    root_url = url_for('home', _external=True)
    errorMessage = False
    languageID = getLangID()
    supportedLangsData = supported_langs()
    toBeTranslated = {'length': 0}
    productCategoriesToBeTranslated = []
    slideShow = []
    
    productCategory = get_product_categories(None, languageID)
    defLangProductCategory = {'length': 0}
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
                slideShow = getSlides(prData['Product_ID'])
                        
            if prData['content'] == True and prData['headers'] == False:
                
                pr_id = prData['ID']

                productCategory = get_product_categories(pr_id, languageID)
                defaultLangDict = getDefLang()
                if defaultLangDict['id'] != languageID:
                    defLangProductCategory = get_product_categories(None, defaultLangDict['id'])

                    if defLangProductCategory['product_category']['length'] > productCategory['product_category']['length']:
                        productCategoryRefKeys = filter_multy_dict(productCategory['product_category']['data'], 'PC_Ref_Key')
                        defLangProductCategoryRefKeys = filter_multy_dict(defLangProductCategory['product_category']['data'], 'PC_Ref_Key')
                        
                        refKeysToBeTranslated = productCategoryRefKeys ^ defLangProductCategoryRefKeys 

                        for value in defLangProductCategory['product_category']['data']:
                            for val in refKeysToBeTranslated:
                                if value['PC_Ref_Key'] == val:
                                    productCategoriesToBeTranslated.append(value) 
                                           

                pcRefKey = get_pc_ref_key(prData['Product_Category_ID']) 
                pcRefKeyLang = get_pc_id_by_lang(pcRefKey)
                productCategory['Product_Category_ID'] = pcRefKeyLang
                productTemplate = 'add_product_lang.html'
                prData['RefKey'] = RefKey

            if prData['content'] == False == prData['headers']: 
                errorMessage = True       
                                              
        else:
            errorMessage = True
    
    if errorMessage == True:
        return render_template('error.html')
    else:
        sideBar = side_bar_stuff()
        emptyCategory = gettext('To continue, please, add at least one product category.')
    
    return render_template(productTemplate, prData=prData, slideShow=slideShow, sideBar=sideBar, productCategory=productCategory, productCategoriesToBeTranslated=productCategoriesToBeTranslated, defLangProductCategory=defLangProductCategory, supportedLangsData=supportedLangsData, errorMessage=errorMessage, root_url=root_url, languageID=languageID, emptyCategory=emptyCategory, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# Edit product'd thumbnail client-server transaction
@app.route('/upload_slides', methods=['POST'])
# @login_required
def upload_slides():
    
    answer = gettext(smthWrong)
    newCSRFtoken = generate_csrf()
    languageID = getLangID()
    
    if not request.form.get('ProductID') or not request.form.get('Type'):
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    

    answer = gettext(smthWrong) # Delete after function is completed


    if not request.form.get('upload_status_0') and request.form.get('Type') == 1:
        answer = gettext('Nothing was uploaded!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    ProductID = request.form.get('ProductID')
    productType = request.form.get('Type')
     # 1 ==> product, 2 ==> subproduct e.g. product type
    if productType == '1':
        imgDir = 'images/product_slider'
    elif productType == '2':

        imgDir = 'images/sub_product_slider'

        if not request.form.get('title'):
            answer = gettext('Please specify title!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})    

        # Check weather Product Type Title exists for current product
        sqlQuery = """SELECT `Title` FROM `product_type` WHERE `Product_ID` = %s AND `Title` = %s;"""
        sqlValTuple = (ProductID, request.form.get('title'))
        resultCheck = sqlSelect(sqlQuery, sqlValTuple, True)

        if resultCheck['length'] > 0:
            answer = '"' + resultCheck['data'][0]['Title'] + '" ' +gettext('Product Type Title Already Exists!') 
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})    
    
        if not request.form.get('price'):
            answer = gettext('Please specify price!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
        
        if request.form.get('fileStatus') == '0':
            answer = gettext('At least one image should be uploaded')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

        if int(request.form.get('price')) <= 0:
            answer = gettext('The price should be higher then 0!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        
        title = request.form.get('title')
        price = request.form.get('price')
        spsID = 0
        if request.form.get('spsID'):
            spsID = int(request.form.get('spsID'))

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
            
            if longData == 1:
                spssAnswer += gettext('Max allowed characters are 255.')
                return jsonify({'status': '0', 'answer': spssAnswer, 'newCSRFtoken': newCSRFtoken})

        sqlQuery = "SELECT `Order` FROM `product_type` WHERE `Product_ID` = %s AND `Status` = 1 ORDER BY `Order` DESC"
        sqlValueTuple = (ProductID,)
        result = sqlSelect(sqlQuery, sqlValueTuple, True)

        if result['length'] > 0:
            order = result['data'][0]['Order'] + 1
        else:
            order = 0

        sqlInsertQuery = "INSERT INTO `product_type` (`Price`, `Title`, `Order`, `Product_ID`, `User_Id`, `spsID`, `Status`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        sqlInsertVals = (int(price), title, order, int(ProductID), session['user_id'], spsID, 1)
        insertedResult = sqlInsert(sqlInsertQuery, sqlInsertVals)

        if insertedResult['inserted_id']:
            ProductID = insertedResult['inserted_id']
            if request.form.get('spsID'):
                sqlP_T_DetailsInsert = "INSERT INTO `product_type_details` (`productTypeID`, `spssID`, `Text`) VALUES (%s, %s, %s)"
                for row in resultSPS['data']:
                    if request.form.get(str(row['spssID'])):
                        Text = request.form.get(str(row['spssID']))
                        sqlValTuplePTD = (ProductID, row['spssID'], Text)
                        resultInsertPTD = sqlInsert(sqlP_T_DetailsInsert, sqlValTuplePTD)
                        if resultInsertPTD['status'] == 0:
                            answer = gettext(smthWrong)
                            return jsonify({'status': '0', 'answer': resultInsertPTD['answer'], 'newCSRFtoken': newCSRFtoken})


        else: 
            answer = gettext(smthWrong)
            return jsonify({'status': '0', 'answer': insertedResult['answer'], 'newCSRFtoken': newCSRFtoken})
            

    else:
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    sqlQuery = "SELECT `ID`, `Name`, `Order`, `AltText` FROM `slider` WHERE `ProductID` = %s AND `Type` = %s;" # Ba type@?
    sqlValTuple = (ProductID, int(productType))
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    shortKeys = {}
    if result['length'] > 0:
        for row in result['data']:
            # shortKeys[row['Name']] = [row['ID'], row['Order']]
            shortKeys[row['ID']] = [row['Name'], row['Order'], row['AltText']]

    dataList = []
    if request.form.get('fileStatus') is not None:
        i = 0
        fileName = 'file_' + str(i)
        max_file_size = 5 * 1024 * 1024  # 5MB in bytes
        sqlUpdateSlide = "UPDATE `slider` SET `AltText` = %s, `Order` = %s WHERE `ID` = %s"  
        sqlInsertSlide = "INSERT INTO `slider`  (`Name`, `AltText`, `Order`, `ProductID`, `Type`) VALUES (%s, %s, %s, %s, %s);"

        while request.files.get(fileName):
            file = request.files.get(fileName)

            # Check image size and return an error if file is too big
            file_size = len(file.read())  # Get the file size in bytes
            file.seek(0)  # Reset the file pointer to the beginning after reading
                    
            filename = secure_filename(file.filename)

            if file_size > max_file_size:
                answer = '<<' +filename + '>>' + gettext('image size is more than 5MB')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
            
            # End of checking the image size


            uStatus = 'upload_status_' + str(i)
            uploadStatus = request.form.get(uStatus)
            
            alt_text = 'alt_text_' + str(i)
            altText = request.form.get(alt_text)

            # Checking the order for not edited (cropped) files
            if uploadStatus == '1':
                
                slideID = request.form.get('slideID_' + str(i))
                if i != shortKeys[int(slideID)][1] or altText != shortKeys[int(slideID)][2]:

                    sqlValTupleSlide = (request.form.get('alt_text_' + str(i)), i,  slideID)      
                    resultUpdate = sqlUpdate(sqlUpdateSlide, sqlValTupleSlide)
                    if resultUpdate['status'] == '-1':
                        answer = gettext(smthWrong)
                        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
                del shortKeys[int(slideID)]  
                # sliderID = shortKeys[filename][0]
                # order = shortKeys[filename][1]
                # if order != i:
                   
                #     sqlQuery = "UPDATE `slider` SET `Order` = %s WHERE `ID` = %s;"
                #     sqlValTuple = (i, sliderID)
                #     sqlUpdate(sqlQuery, sqlValTuple) 

                # del shortKeys[filename]
            #  End

            if uploadStatus == '0':
                unique_filename = fileUpload(file, imgDir)
                sqlValTuple = (unique_filename, altText, i, ProductID, productType)
                result = sqlInsert(sqlInsertSlide, sqlValTuple)
                if result['inserted_id']:
                    # Stegh es grum file uploader
                    dataList.append(result['answer'])
                else:
                    answer = gettext(smthWrong)
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
         

            
            
            i = i + 1    
            fileName = 'file_' + str(i)

        # print('SSSSSSSSSSSSSSSSSSSSS', shortKeys)
        lenShortkeys = len(shortKeys)
        if lenShortkeys > 0 and productType == '1':
            sqlValList = []
            for key, val in shortKeys.items():
                sqlValList.append(key)
                
                # Del from folder
                removeResult = removeRedundantFiles(val[0], imgDir)
                if removeResult == False:
                    answer = gettext(smthWrong)
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
            
            idCount = lenShortkeys * "%s, "
            idCount = idCount[:-2]
            sqlDeleteQuery = f"DELETE FROM `slider` WHERE `ID` IN ({idCount});" 
            sqlValTuple = tuple(sqlValList)
            # print(f"Query {sqlDeleteQuery} AND sqlValTuple {sqlValTuple}")
            delResult = sqlDelete(sqlDeleteQuery, sqlValTuple)
            if delResult['status'] == '-1':
                return jsonify({'status': '0', 'answer': delResult['answer'], 'newCSRFtoken': newCSRFtoken}) 
   
    answer = gettext('Done!')
    return jsonify({'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 


# Edit product'd thumbnail client-server transaction
@app.route('/edit_pr_thumbnail', methods=['POST'])
# @login_required
def edit_pr_thumbnail():
    newCSRFtoken = generate_csrf()
        
    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()

    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    

    sqlQueryID = f"""
                    SELECT `P_ID`
                    FROM `product_relatives`
                    WHERE `product_relatives`.`P_Ref_Key` = %s
                        AND `product_relatives`.`Language_ID` = %s
                  """
    
    sqlQueryValId = (RefKey, languageID)

    resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    if resultID['length'] > 0:  
        productID = resultID['data'][0]['P_ID']
    else:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    state = json.loads(state)

    sqlImage = " `Thumbnail` = %s, "
    if state['status'] == 0: # Image was not changed
        sqlImage = ""
        sqlQueryVal = (altText, productID)
    if state['status'] == 1: # Image was chosen from another language

        # Get Image name
        if getFileName('Thumbnail', 'product', 'ID', productID):
            imageName = getFileName('Thumbnail', 'product', 'ID', productID)

            if checkForRedundantFiles(imageName, 'Thumbnail', 'product'):
                removeRedundantFiles(imageName, 'images/pr_thumbnails')

        sqlQueryVal = (state['file'], altText, productID)

    if state['status'] == 2: # New image is uploaded   
        
        # Get Image name
        if getFileName('Thumbnail', 'product', 'ID', productID):
            imageName = getFileName('Thumbnail', 'product', 'ID', productID)
        
            if checkForRedundantFiles(imageName, 'Thumbnail', 'product'):
                removeRedundantFiles(imageName, 'images/pr_thumbnails')
            
        file = request.files.get('file')
        unique_filename = fileUpload(file, 'images/pr_thumbnails')

        sqlQueryVal = (unique_filename, altText,  productID)
    
    sqlQuery   = f"""   
                    UPDATE `product`
                    SET 
                        {sqlImage}                       
                        `DateModified` = CURDATE(),
                        `AltText` = %s
                    WHERE `ID` = %s;
                 """

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result


# edit_thumbnail client-server transaction
@app.route('/edit_thumbnail', methods=['POST'])
# @login_required
def edit_thumbnail():
    newCSRFtoken = generate_csrf()
        
    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()

    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    

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
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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


# add_product client-server transaction
@app.route('/add_product', methods=['POST'])
@login_required
def add_pr():
    newCSRFtoken = generate_csrf()
        
    if not request.form.get('productName'):
        answer = gettext('Title is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('productLink'): 
        answer = gettext('Link is empty!')
        return jsonify({'status': '4', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Product Category!')
        return jsonify({'status': '6', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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


# add_article client-server transaction
@app.route('/add_article', methods=['POST'])
@login_required
def add_ar():
    newCSRFtoken = generate_csrf()
        
    if not request.form.get('productName'):
        answer = gettext('Title is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('productLink'): 
        answer = gettext('Link is empty!')
        return jsonify({'status': '4', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Article Category!')
        return jsonify({'status': '6', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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

    return add_article(productName, productLink, languageID, CategoryID, file, altText, shortDescription, longDescription, RefKey)

# add article lang client-server transaction
@app.route('/add_article_lang', methods=['POST'])
@login_required
def add_pr_lang():

    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext(smthWrong)
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


# edit product headers client-server transaction
@app.route('/edit_product_headers', methods=['POST'])
# @login_required
def edit_pr_headers():
    newCSRFtoken = generate_csrf()
        
    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext(smthWrong)
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    elif not request.form.get('productName'):
        answer = gettext('Product name is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('productLink'):
        answer = gettext('Product link is empty!')
        return jsonify({'status': '4', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Product Category!')
        return jsonify({'status': '6', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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


# edit article headers client-server transaction
@app.route('/edit_article_headers', methods=['POST'])
@login_required
def edit_ar_headers():
    newCSRFtoken = generate_csrf()
        
    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext(smthWrong)
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    elif not request.form.get('productName'):
        answer = gettext('Article name is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('productLink'):
        answer = gettext('Article link is empty!')
        return jsonify({'status': '4', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    elif not request.form.get('CategoryID'):
        answer = gettext('Please Choose Article Category!')
        return jsonify({'status': '6', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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
    return edit_a_h(productName, productLink, languageID, CategoryID, RefKey, ShortDescription, LongDescription)


# Render the add_product_category.html template
@app.route('/add-product-category', methods=['GET'])
@login_required
def addPC():
    # Vortegh em Stegh em
    # sps - ov dropdown es steghcum!
    languageID = getLangID()
    sqlQuery = f"""SELECT 
                        `sub_product_specification`.`ID`,
                        `sub_product_specification`.`Name`
                    FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                    WHERE `sps_relatives`.`Language_ID` = %s AND `sub_product_specification`.`Status` = %s;

                """
    sqlValTuple = (languageID, 1)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    
    sideBar = side_bar_stuff()
    return render_template('add_product_category.html', sideBar=sideBar, sps=result, languageID=languageID, current_locale=get_locale())


# add_product_category client-server transaction
@app.route('/add_product_category', methods=['POST'])
@login_required
def add_p_c():
    newCSRFtoken = generate_csrf()
    categoryName = request.form.get('categoryName')
    spsID = request.form.get('spsID')
    AltText = request.form.get('AltText')
    file = request.files.get('file')
    currentLanguage = request.form.get('languageID')

    if not categoryName:
        answer = gettext('Category name is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    if spsID:
        spsID = int(spsID)
    else:
        spsID = None
    
    return add_p_c_sql(categoryName, file, AltText, currentLanguage, spsID, newCSRFtoken)

# Render the add_article_category.html template
@app.route('/add-article-category', methods=['GET'])
@login_required
def addAC():
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('add_article_category.html', sideBar=sideBar, languageID=languageID, current_locale=get_locale())


# add_product_category client-server transaction
@app.route('/add_article_category', methods=['POST'])
@login_required
def add_a_c():
    newCSRFtoken = generate_csrf()
    categoryName = request.form.get('categoryName')
    AltText = request.form.get('AltText')
    file = request.files.get('file')
    currentLanguage = request.form.get('languageID')

    if not categoryName:
        answer = gettext('Category name is empty!')
        return jsonify({'status': '2', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) # categoryName is Empty
    
    
    return add_a_c_sql(categoryName, file, AltText, currentLanguage, newCSRFtoken)


# Render the edit_product_category.html template
@app.route('/edit-product-category/<RefKey>', methods=['GET'])
# @login_required
def edit_product_category(RefKey):
    content = edit_p_c_view(RefKey)
    pcImages = get_product_category_images(RefKey) 
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('edit_product_category.html', sideBar=sideBar, content=content, pcImages=pcImages, languageID=languageID, RefKey=RefKey, current_locale=get_locale())



# edit_product_category client-server transaction
@app.route('/edit_product_category', methods=['POST'])
# @login_required
def edit_p_c():
    newCSRFtoken = generate_csrf()
        
    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()
    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    if request.form.get('categoryName'):
        categoryName = request.form.get('categoryName').strip()
    else:         
        answer = gettext('Category Name is empty!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    categoryNameExists = checkProductCategoryName(RefKey, languageID, categoryName)
    if categoryNameExists == True:
        answer = gettext('Category Name Exists!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    categoryStatus = request.form.get('categoryStatus')

    sqlQueryID = f"""
                    SELECT `PC_ID`
                    FROM `product_c_relatives`
                    WHERE `product_c_relatives`.`PC_Ref_Key` = %s
                    AND `product_c_relatives`.`Language_ID` = %s;
                  """
    
    sqlQueryValId = (RefKey, languageID)

    resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    if resultID['length'] > 0:  
        productCategoryID = resultID['data'][0]['PC_ID']
    else:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    state = json.loads(state)

    sqlImage = "`Product_Category_Images` = %s,"
    if state['status'] == 0:
        sqlImage = ""
        sqlQueryVal = (altText, categoryName, categoryStatus, productCategoryID)
    if state['status'] == 1:
        # Get Image name
        if getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID):
            imageName = getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID)

            if checkForRedundantFiles(imageName, 'Product_Category_Images', 'product_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')

        sqlQueryVal = (state['file'], altText, categoryName, categoryStatus, productCategoryID)
    if state['status'] == 2:    
        # Get Image name
        if getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID):
            imageName = getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID)
    
            if checkForRedundantFiles(imageName, 'Product_Category_Images', 'product_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')
            
        file = request.files.get('file')

        unique_filename = fileUpload(file, 'images/pc_uploads')
        sqlQueryVal = (unique_filename, altText, categoryName, categoryStatus, productCategoryID)
    
    # Stegh es !!!
    sqlQuery   = f"""   
                    UPDATE `product_category`
                    SET 
                        {sqlImage}                       
                        `AltText` = %s,
                        `Product_Category_Name` = %s,
                        `Product_Category_Status` = %s
                    WHERE `Product_Category_ID` = %s;
                 """

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result


# Render the edit_product_category.html template
@app.route('/edit-article-category/<RefKey>', methods=['GET'])
@login_required
def edit_article_category(RefKey):
    content = edit_a_c_view(RefKey)
    pcImages = get_article_category_images(RefKey)
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('edit_product_category.html', sideBar=sideBar, content=content, pcImages=pcImages, languageID=languageID, RefKey=RefKey, current_locale=get_locale())



# edit_product_category client-server transaction
@app.route('/edit_article_category', methods=['POST'])
@login_required
def edit_a_c():
    newCSRFtoken = generate_csrf()
        
    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    altText = ''
    if request.form.get('AltText'):
        altText = request.form.get('AltText').strip()
    state = request.form.get('state')

    if len(languageID) == 0 or len(RefKey) == 0:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    if request.form.get('categoryName'):
        categoryName = request.form.get('categoryName').strip()
    else:         
        answer = gettext('Category Name is empty!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    categoryNameExists = checkCategoryName(RefKey, languageID, categoryName)
    if categoryNameExists == True:
        answer = gettext('Category Name Exists!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
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
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
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




# Publish/Unpublish product
@app.route('/publish-product', methods=['POST'])
# @login_required
def publishP():

    languageID = request.form.get('languageID').strip()
    RefKey = request.form.get('RefKey').strip()
    productStatus = request.form.get('productStatus').strip()

    answer = gettext('Something is wrong!')

    if productStatus is None or languageID is None or RefKey is None:
        return jsonify({'status': '0', 'answer': answer}) 
    
    productID = get_pr_id_by_lang(RefKey, languageID)

    if productID == False:
        return jsonify({'status': '0', 'answer': answer})
    
    # Published date
    sqlQueryPub = "SELECT `DatePublished` FROM `product` WHERE `ID` = %s"
    sqlQueryPubVal = (productID,)
    resultPub = sqlSelect(sqlQueryPub, sqlQueryPubVal, True)

    if resultPub['data'][0]['DatePublished'] == None:
        sqlQuery = "UPDATE `product` SET `Product_Status` = %s, `DatePublished` = CURDATE() WHERE `ID` = %s"
    else:
        sqlQuery = "UPDATE `product` SET `Product_Status` = %s WHERE `ID` = %s"
    
    sqlValTuple = (productStatus, productID)
    result = sqlUpdate(sqlQuery, sqlValTuple)

    if result['status'] == '1':
        if productStatus == '2':
            answer = gettext('Product is published')
        if productStatus == '1':
            answer = gettext('Product is unpublished')
        return jsonify({'status': '1', 'answer': answer})
    else:
        return jsonify({'status': '0', 'answer': answer})

# End of Publish/Unpublish product


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

# End of Publish/Unpublish article

# Product categories view
@app.route('/product-categories', methods=['GET'])
# @login_required
def product_categories():
    languageID = getLangID()
    sqlQuery = """
                SELECT 
                    `Product_Category_ID`,
                    `Product_Category_Name`,
                    `Product_Category_Images`,
                    `Product_Category_Status`,
                    `PC_Ref_Key`
                FROM `product_category`
                LEFT JOIN `product_c_relatives` ON `product_c_relatives`.`PC_ID` = `product_category`.`Product_Category_ID` 
                WHERE `product_c_relatives`.`Language_ID` = %s
                ORDER BY `Product_Category_ID` DESC; 
               """
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    return render_template('product-categories.html', sideBar=sideBar, result=result, current_locale=get_locale())

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
    sqlQuery = f"""
                SELECT 
                    `stuff`.`ID`,
                    `stuff`.`Firstname`,
                    `stuff`.`Lastname`,
                    `stuff`.`Email`,
                    `stuff`.`Status`,
                    `stuff`.`Avatar`,
                    `stuff`.`AltText`,
                    `rol`.`Rol`
                FROM `stuff`
                LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID` 
                LIMIT 0, {PAGINATION}
                ; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    numRows = totalNumRows('stuff')
    sideBar = side_bar_stuff()

    return render_template('team.html', result=result, sideBar=sideBar, numRows=numRows, page=1,  pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), current_locale=get_locale())



@app.route('/team/<page>', methods=['Get'])
# @login_required
def teampage(page): 
    languageID = getLangID()
    newCSRFtoken = generate_csrf()
    rowsToSelect = (int(page) - 1) * int(PAGINATION)
    sqlQuery = f"""
                SELECT 
                    `stuff`.`ID`,
                    `stuff`.`Firstname`,
                    `stuff`.`Lastname`,
                    `stuff`.`Email`,
                    `stuff`.`Status`,
                    `stuff`.`Avatar`,
                    `stuff`.`AltText`,
                    `rol`.`Rol`
                FROM `stuff`
                LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID` 
                LIMIT {rowsToSelect}, {PAGINATION}; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()
    numRows = totalNumRows('stuff')


    return render_template('team.html', result=result, sqlQuery=sqlQuery, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), sideBar=sideBar, current_locale=get_locale())
    # return jsonify({'status': '1', 'answer': result['data'], 'newCSRFtoken': newCSRFtoken})




@app.route('/edit-teammate/<teammateID>', methods=['GET', 'POST'])
# @login_required
def edit_teammate(teammateID):
    languageID = getLangID()
    if request.method == 'POST':
        newCSRFtoken = generate_csrf()
               
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        languageID  = request.form.get('languageID')

        # Check if firstname exists
        if len(request.form.get('Firstname')) == 0:
            answer = gettext('Please specify the first name')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Firstname = request.form.get('Firstname').strip()
       
        # Check if lastname exists
        if len(request.form.get('Lastname')) == 0:
            answer = gettext('Please specify the last name')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Lastname = request.form.get('Lastname').strip()
        
        # Check if email exists
        if len(request.form.get('Email')) == 0:
            answer = gettext('Please specify email')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Email = request.form.get('Email').strip()

        # Validate email
        emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        # Check if the email matches the pattern
        if not re.match(emailPattern, Email):
            answer = gettext('Invalid email format')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
     
        # Check whether Email exists or not in stuff and buffer tables
        sqlQuery = "SELECT `Email` FROM `stuff` WHERE `Email` = %s AND `ID` != %s;"
        sqlValTuple = (Email, teammateID)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists. """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
         
        sqlQuery = "SELECT `Email` FROM `buffer` WHERE `Email` = %s AND `Status` = 0;"
        sqlValTuple = (Email,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
        
        # Check if Role exists
        if len(request.form.get('RoleID')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
       
        RoleID  = request.form.get('RoleID').strip()
        
        # Check if Status exists
        if len(request.form.get('Status')) == 0:
            answer = gettext('Something is wrong, please try again!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Status  = request.form.get('Status')

        AltText = ''
        avatar = ''
        sqlValTuple = (Firstname, Lastname, Email, RoleID, AltText, Status, teammateID)
        
        if request.form.get('imageState') == '0': # No image uploaded
            avatar = " Avatar = '', "
            sqlQ = "SELECT `Avatar` FROM `stuff` WHERE `ID` = %s;"
            sqlVT = (teammateID,)
            res = sqlSelect(sqlQ, sqlVT, True)
            if res['data'][0]['Avatar']:
                oldAvatar = res['data'][0]['Avatar']
                removeRedundantFiles(oldAvatar, 'images/stuff')  


        if request.form.get('imageState') == '1': # Same image (it was not changed)
            
            AltText  = request.form.get('AltText')
            sqlValTuple = (Firstname, Lastname, Email, RoleID, AltText, Status, teammateID)

        if request.form.get('imageState') == '2': # New image is uploaded
            sqlQ = "SELECT `Avatar` FROM `stuff` WHERE `ID` = %s;"
            sqlVT = (teammateID,)
            res = sqlSelect(sqlQ, sqlVT, True)
            if res['data'][0]['Avatar']:
                oldAvatar = res['data'][0]['Avatar']
                removeRedundantFiles(oldAvatar, 'images/stuff')  

            AltText  = request.form.get('AltText')     
            file = request.files.get('file')
            Avatar = fileUpload(file, 'images/stuff')
            avatar = "Avatar = %s,"
            sqlValTuple = (Firstname, Lastname, Email, RoleID, Avatar, AltText, Status, teammateID)

        sqlQuery = f"""
            UPDATE `stuff` SET
                `Firstname` = %s,
                `Lastname` = %s,
                `Email` = %s,
                `RolID` = %s,
                {avatar}
                `AltText` = %s,
                `Status` = %s
            WHERE `ID` = %s;
        """

        result = sqlUpdate(sqlQuery, sqlValTuple)

        if result['status'] == '1':
            return jsonify({'status': '1'})
        else:  
            return jsonify({'status': '0', 'answer': result['answer'], 'newCSRFtoken': newCSRFtoken})  

    # GET action
    else:
        sqlQuery = """
                    SELECT 
                        `stuff`.`ID`,
                        `stuff`.`Firstname`,
                        `stuff`.`Lastname`,
                        `stuff`.`Email`,
                        `stuff`.`Avatar`,
                        `stuff`.`AltText`,
                        `stuff`.`Status`,
                        `rol`.`ID` AS `RoleID`,
                        `rol`.`Rol`
                    FROM `stuff`
                    LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`RolID` 
                    WHERE `stuff`.`ID` = %s
                    ; 
                """
        sqlValTuple = (teammateID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        sqlQueryR = """
                        SELECT 
                            `ID`,
                            `Rol`
                        FROM `rol`
                        ; 
                    """
        sqlValTupleR = ()
        resultR = sqlSelect(sqlQueryR, sqlValTupleR, True)

        sideBar = side_bar_stuff()

        return render_template('edit-teammate.html', row=result['data'][0], resultR=resultR, sideBar=sideBar, languageID=languageID, current_locale=get_locale())

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
        newCSRFtoken = generate_csrf()
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        languageID  = request.form.get('languageID')

        if len(request.form.get('Role')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Role  = request.form.get('Role').strip()

        if len(request.form.get('Actions')) == 0:
            answer = gettext('Please choose at least on action')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Actions = request.form.get('Actions').strip()

        # Check whether role exists or not
        sqlQuery = "SELECT `Rol` FROM `rol` WHERE `Rol` = %s;"
        sqlValTuple = (Role,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" There is already a role called "{Role}" """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        

        sqlQuery = "INSERT INTO `rol` (`Rol`, `ActionIDs`) VALUES (%s, %s);"
        sqlValTuple = (Role, Actions)

        result = sqlInsert(sqlQuery, sqlValTuple)
        
        if result['inserted_id'] is not None:
            answer = result['answer']
            return jsonify({'status': '1', 'answer': answer}) 
        else:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
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
        newCSRFtoken = generate_csrf()
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer})  
        
        languageID  = request.form.get('languageID')

        # Check if email exists
        if len(request.form.get('Email')) == 0:
            answer = gettext('Please specify email')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Email = request.form.get('Email').strip()

        # Validate email
        emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        # Check if the email matches the pattern
        if not re.match(emailPattern, Email):
            answer = gettext('Invalid email format')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

        if len(request.form.get('RoleID')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        RoleID  = request.form.get('RoleID').strip()

        # Check whether Email exists or not in stuff and buffer tables
        sqlQuery = "SELECT `Email` FROM `stuff` WHERE `Email` = %s;"
        sqlValTuple = (Email,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
         
        sqlQuery = "SELECT `Email` FROM `buffer` WHERE `Email` = %s;"
        sqlValTuple = (Email,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" Specified email  "{Email}" already exists """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
         
        # insert into buffer table
        uniqueURL = generate_random_string()

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
            return jsonify({'status': '0', 'answer': uniqueURL, 'newCSRFtoken': newCSRFtoken}) 
        else:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
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
        newCSRFtoken = generate_csrf()        
        
        if len(request.form.get('Firstname')) == 0:
            answer = gettext('Please specify firstname')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Firstname = request.form.get('Firstname').strip()

        if len(request.form.get('Lastname')) == 0:
            answer = gettext('Please specify lastname')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Lastname = request.form.get('Lastname').strip()
        
        if len(request.form.get('Username')) == 0:
            answer = gettext('Please specify username')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Username = request.form.get('Username').strip()
        
        # Check if username exists in stuff tables
        sqlQuery = "SELECT `Username` FROM `stuff` WHERE `Username` = %s;"
        sqlValTuple = (Username,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = gettext('Username exists')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
          
        
        if len(request.form.get('Password')) == 0:
            answer = gettext('Please specify Password')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        passwordErrors = validate_password(request.form.get('Password'))

        if len(passwordErrors) > 0:
            return jsonify({'status': '2', 'answer': passwordErrors, 'newCSRFtoken': newCSRFtoken})  

        if len(request.form.get('Password2')) == 0:
            answer = gettext('Password confirmation field is empty')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        if request.form.get('Password') != request.form.get('Password2'):
            answer = gettext('Passwords do not match!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        if len(request.form.get('LanguageID')) == 0:
            answer = gettext('Please specify prefared language')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        AltText = request.form.get('altText')
        
        unique_filename = ''
        if request.files.get('file'):
            file = request.files.get('file')

            # Check file type
            valid_types = {'image/jpeg', 'image/png'}
            if file.mimetype not in valid_types:
                answer = gettext('File should be in PNG or JPG/JPEG format')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
            
            # # Check file size (1 MB = 1048576 bytes)
            file_size = file.tell()
            if file_size > 1048576:
                answer = gettext('File size should not exceed 1MB.')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
            
            file.seek(0)  # Reset the file pointer to the beginning after reading
            unique_filename = fileUpload(file, 'images/stuff')
    
        LanguageID = request.form.get('LanguageID')

        Hash = generate_password_hash(request.form.get('Password'))
        
        # Get data from buffer
        sqlQuery = "SELECT * FROM `buffer` WHERE `Url` = %s AND `Status` = 0 AND `Deadline` > CURRENT_TIMESTAMP;"
        sqlValTuple = (uniqueURL,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        
        if result['length'] == 0:
            answer = gettext('The URL is expired')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        
        row = result['data'][0]
        Email = row['Email']
        RoleID = row['RoleID']
        BufferID = row['ID']

        sqlQuery = """INSERT INTO `stuff` (`Username`, `Password`, `Email`, `Firstname`, `Lastname`, `RolID`, `LanguageID`, `Avatar`, `AltText`, `Status`)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1);"""

        sqlValTuple = (Username, Hash, Email, Firstname, Lastname, RoleID,  LanguageID, unique_filename, AltText)

        result = sqlInsert(sqlQuery, sqlValTuple)
        
        if result['inserted_id'] is None:
            answer = " Something is wrong!"
            return jsonify({'status': '0', 'answer': result['answer'], 'newCSRFtoken': newCSRFtoken})
        

        # Change status of buffer
        sqlQuery = "UPDATE `buffer` SET `Status` = 1 WHERE `ID` = %s;"
        sqlValTuple = (BufferID,)
        sqlUpdate(sqlQuery, sqlValTuple)

        return jsonify({'status': '1'}) 
        
    else:
      
        sqlQuery = "SELECT * FROM `buffer` WHERE `Url` = %s AND `Status` = 0 AND `Deadline` > CURRENT_TIMESTAMP;"
        sqlValTuple = (uniqueURL,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
               
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
        newCSRFtoken = generate_csrf()
              
        if len(request.form.get('RoleID')) == 0:
            answer = gettext('Something wrong!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        RoleID  = request.form.get('RoleID')
        
        if len(request.form.get('languageID')) == 0:
            answer = gettext('Something wrongdfd!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
        
        languageID  = request.form.get('languageID')

        if len(request.form.get('Role')) == 0:
            answer = gettext('Please specify the role')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Role  = request.form.get('Role').strip()

        if len(request.form.get('Actions')) == 0:
            answer = gettext('Please choose at least on action')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  

        Actions = request.form.get('Actions').strip()

        # Check whether role exists or not
        sqlQuery = "SELECT `Rol` FROM `rol` WHERE `Rol` = %s AND `ID` != %s;"
        sqlValTuple = (Role, RoleID)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        if result['length'] > 0:
            answer = f""" There is already a role called "{Role}" """
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        

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
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
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


@app.route('/products', methods=['GET'])
# @login_required
def products():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    LEFT JOIN `product_category` 
                      ON `product_category`.`Product_Category_ID` = `product`.`Product_Category_ID`
                    WHERE `product_relatives`.`Language_ID` = %s                    
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    return render_template('products.html', result=result, mainCurrency=MAIN_CURRENCY,  sideBar=sideBar, current_locale=get_locale()) 


@app.route('/store', methods=['GET', 'POST'])
# @login_required
def store():    
    if request.method == 'GET':
        languageID = getLangID()
        # Main query that gets all active products in all stores [ WHERE `quantity`.`Status` = 1]
        sqlQuery =  f"""
                        SELECT 
                            `product`.`ID`,
                            `product`.`Title` AS `prTitle`,
                            `product`.`Thumbnail`,
                            SUM(`quantity`.`Quantity`) AS `TotalQuantity`
                        FROM `quantity`
                            LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                        WHERE `quantity`.`Status` = 1
                        GROUP BY `product`.`ID`, `product`.`Title`, `product`.`Thumbnail`
                    ;               
                    """
        
        sqlValTuple = ()
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        sqlQueryStore = "SELECT `ID`, `Name` FROM `store` WHERE `Status` = 1;"
        resultStore = sqlSelect(sqlQueryStore, (), False)
        storeData = json.dumps(resultStore['data'])

        sqlQueryProducts = "SELECT `ID`, `Title` FROM `product` WHERE `Language_ID` = %s;"
        resultStore = sqlSelect(sqlQueryProducts, (languageID,), False)
        productsData = json.dumps(resultStore['data'])

        sideBar = side_bar_stuff()
        return render_template('store.html', result=result, storeData=storeData, productsData=productsData, mainCurrency=MAIN_CURRENCY,  sideBar=sideBar, current_locale=get_locale()) 
    else:
        newCSRFtoken = generate_csrf()
        filters = ''
        sqlValList = []

        if request.form.get('productionDate'):
            filters = filters + ' AND productionDate = %s ' 
            sqlValList.append(request.form.get('productionDate'))

        if request.form.get('expDate'):
            filters = filters + ' AND expDate = %s ' 
            sqlValList.append(request.form.get('expDate'))

        if request.form.get('addDate'):
            filters = filters + ' AND addDate = %s ' 
            sqlValList.append(request.form.get('addDate'))

        if request.form.get('storeID'):
            filters = filters + ' AND storeID = %s ' 
            sqlValList.append(request.form.get('storeID'))

        if request.form.get('productID'):
            filters = filters + ' AND `product`.`ID` = %s ' 
            sqlValList.append(request.form.get('productID'))

        if request.form.get('ptID'):
            filters = filters + ' AND `productTypeID` = %s ' 
            sqlValList.append(request.form.get('ptID'))

        
        if len(sqlValList) > 0:
            sqlValTuple = tuple(sqlValList)
        else: 
            sqlValTuple = ()

        sqlQuery = f"""
                        SELECT 
                            `product`.`ID`,
                            `product`.`Title` AS `prTitle`,
                            `product`.`Thumbnail`,
                            SUM(`quantity`.`Quantity`) AS `TotalQuantity`
                        FROM `quantity`
                            LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                        WHERE `quantity`.`Status` = 1 {filters}
                        GROUP BY `product`.`ID`, `product`.`Title`, `product`.`Thumbnail`
                    ;               
                    """
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        response = {'status': '1', 'answer': result['data'], 'length': result['length'], 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)


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


@app.route("/pt-specifications", methods=['GET'])
# @login_required
def pt_specifications():
    languageID = getLangID()
    sqlQuery = """
                SELECT 
                    `sub_product_specification`.`ID`,
                    `sub_product_specification`.`Name`,
                    `sub_product_specification`.`Status`
                FROM `sub_product_specification`
                LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                WHERE `sps_relatives`.`Language_ID` = %s;
                """
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    numRows = totalNumRows('sub_product_specification')
    sideBar = side_bar_stuff()

    return render_template('product-type-specifications.html', result=result, sideBar=sideBar, numRows=numRows, page=1,  pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), current_locale=get_locale())


@app.route("/edit-pts/<ptsID>", methods=['GET'])
# @login_required
def edit_pts_view(ptsID):
    languageID = getLangID()
    sqlQuery = """
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
    sqlValTuple = (languageID, ptsID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()
    if result['length'] == 0:
        return render_template('error.html', current_locale=get_locale())

    return render_template('edit-pts.html', result=result['data'], num=result['length'], sideBar=sideBar, current_locale=get_locale())


# Change order of product types of a product
@app.route("/change-type-order", methods=['POST'])
# @login_required
def change_type_order():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    prID = request.form.get('prID')
    sqlQuery = """
                    SELECT `product_type`.`ID`,
                            `product_type`.`Order`
                    FROM `product_type`
                    WHERE `product_type`.`Product_ID` = %s 
                    ORDER BY `product_type`.`Order` 
                    ;"""
    sqlValTuple = (prID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)

    i = 0
    sqlQuery = "UPDATE `product_type` SET `Order` = %s WHERE `ID` = %s;"
    while True:
        if not request.form.get(str(i)):
            break
        print(f"result['data'][i]['ID'] Type is {type(result['data'][i]['ID'])} Value is {result['data'][i]['ID']}  ===== request.form.get(i) Type is {type(request.form.get(str(i)))} Value is {request.form.get(str(i))}")    
        if result['data'][i]['ID'] != int(request.form.get(str(i))):
            sqlValTuple = (i, request.form.get(str(i)))
            updateResult = sqlUpdate(sqlQuery, sqlValTuple)
            if updateResult['status'] == '-1':
                answer = gettext(smthWrong)
                response = {'status': '0', 'answer': updateResult['answer'], 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)   
             
        i += 1


    answer = gettext('Order Changed Successfully!')
    response = {'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)
    

@app.route("/chaneg-pt-status", methods=['POST'])
# @login_required
def chaneg_pt_status():
    newCSRFtoken = generate_csrf()
    ptID = request.form.get('ptID') 
    status = request.form.get('status') 
    if not ptID or not status:
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    sqlQuery = "UPDATE `product_type` SET `status` = %s WHERE `ID` = %s;"
    sqlValTuple = (status, ptID)
    result = sqlUpdate(sqlQuery, sqlValTuple)

    if result['status'] == '-1':
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    answer = gettext('Status changed successfully!')
    response = {'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/edit-pts", methods=['POST'])
# @login_required
def edit_pts():
    newCSRFtoken = generate_csrf()
    spsName = request.form.get('spsName') 
    if not spsName:
        answer = gettext('Please specify subproduct situation name!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    spsID = request.form.get('spsID') 
    if not spsID:
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)

    languageID = getLangID()
    # Check if the spsName already exists 
    sqlQuery = f"""SELECT `sub_product_specification`.`ID`
                    FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID`
                    WHERE `sub_product_specification`.`Name` = %s AND `sps_relatives`.`Language_ID` = %s AND `sub_product_specification`.`ID` != %;"""
    
    sqlValTuple = (spsName, languageID, spsID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    if result['length'] > 0:
        answer = gettext('Subproduct situation name exists!') + ' "' + spsName + '"'
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    userID = session['user_id']

    sqlQueryPtss = """
                SELECT 
                    `sub_product_specification`.`ID`,
                    `sub_product_specification`.`Name`,
                    `sub_product_specifications`.`Name` AS `Text`,
                    `sub_product_specifications`.`ID` AS `spssID`,
                    `sub_product_specifications`.`Status` AS `spssStatus`,
                    `spss_relatives`.`Ref_Key` AS `spssRefKey`
                FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                    LEFT JOIN `sub_product_specifications` ON `sub_product_specifications`.`spsID` = `sub_product_specification`.`ID`
                    LEFT JOIN `spss_relatives` ON `spss_relatives`.`SPSS_ID` = `sub_product_specifications`.`ID` 
                WHERE `sps_relatives`.`Language_ID` = %s AND `sub_product_specification`.`ID` = %s
                ORDER BY `sub_product_specifications`.`Order`;
                """
    sqlValTuple = (languageID, spsID)
    result = sqlSelect(sqlQueryPtss, sqlValTuple, True)

    if spsName != result['data'][0]['Name']:
        sqlQueryUpdate = "UPDATE `sub_product_specification` SET `Name` = %s WHERE `ID` = %s;"
        sqlValTupleUpdate = (spsName, spsID)
        updateResult = sqlUpdate(sqlQueryUpdate, sqlValTupleUpdate)
        if updateResult['status'] == '-1':
            answer = gettext(smthWrong)
            response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
            return jsonify(response)
        

    sqlQuerySpssUpdate = "UPDATE `sub_product_specifications` SET `Name` = %s WHERE `ID` = %s "    
    sqlQuerySpssInsert = "INSERT INTO `sub_product_specifications` (`Name`, `Order`, `spsID`, `Status`) VALUES (%s, %s, %s, %s)" 
    sqlQuerySPSSRelativeInsert = "INSERT INTO `spss_relatives` (`SPSS_ID`, `Ref_Key`, `Language_ID`, `User_ID`, `Status`) VALUES (%s, %s, %s, %s, %s)"
    
    RefKey = result['data'][-1:][0]['spssRefKey']
    dataChecker = copy.deepcopy(result['data'])  
    i = 0
    
    while True:
        spsText = request.form.get('text_' + str(i))
        if not spsText: 
            break
        # print('AAAAAAAAAAAAAAAAAAAAAAa')
        # print(i)
        # print(f"result['data'] Length {len(result['data'])}")
        # print('BBBBBBBBBBBBBBBBBBBBBBB')
        
        if len(result['data']) > i:
            if spsText != result['data'][i]['Text']:
                # print(f"{spsText} -- {result['data'][i]['Text']} ")
                sqlValTuple = (spsText, result['data'][i]['spssID'])
                updateResult = sqlUpdate(sqlQuerySpssUpdate, sqlValTuple)
                if updateResult['status'] == '-1':
                    answer = gettext(smthWrong)
                    response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                    return jsonify(response)
        else:
            sqlValTuple = (spsText, i, spsID, 1)
            resultInsert = sqlInsert(sqlQuerySpssInsert, sqlValTuple)
            if resultInsert['status'] == 0:
                answer = gettext(smthWrong)
                response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)

            spssID = resultInsert['inserted_id']

            sqlValTupleSPSRel = (spssID, RefKey, languageID, userID, 1)
            insertResult = sqlInsert(sqlQuerySPSSRelativeInsert, sqlValTupleSPSRel)
            if insertResult['status'] == 0:
                answer = gettext(smthWrong)
                response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)
            
            RefKey = RefKey + 1
    
        if len(dataChecker):
            dataChecker.pop(0)

        i = i + 1

    if len(dataChecker) > 0:
        for row in dataChecker:
            sqlQueryDel = "DELETE FROM `sub_product_specifications` WHERE `ID` = %s;"
            sqlValTuple = (row['spssID'],)
            resultDel = sqlDelete(sqlQueryDel, sqlValTuple)
            if resultDel['status'] == '-1':
                answer = gettext(smthWrong)
                response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)
            
    response = {'status': '1', 'answer': gettext('Done!'), 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


    


@app.route("/add-sps", methods=['GET'])
# @login_required
def add_sps_view():
    return render_template('sp-specifications.html', current_locale=get_locale())

# Subproduct situation and situations adding function
@app.route("/add_sps", methods=['POST'])
# @login_required
def add_sps():
    newCSRFtoken = generate_csrf()
    # Checking spsName
    spsName = request.form.get('spsName') 
    if not spsName:
        answer = gettext('Please specify subproduct situation name!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    languageID = getLangID()
    # Check if the spsName already exists 
    sqlQuery = f"""SELECT `sub_product_specification`.`ID`
                    FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID`
                    WHERE `sub_product_specification`.`Name` = %s AND `sps_relatives`.`Language_ID` = %s;"""
    sqlValTuple = (spsName, languageID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    if result['length'] > 0:
        answer = gettext('Subproduct situation name exists!') + ' "' + spsName + '"'
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    userID = session['user_id']

    sqlQuery = "INSERT INTO `sub_product_specification` (`Name`, `User_ID`, `Status`) VALUES (%s, %s, %s)"
    sqlValTuple = (spsName, userID, 1)
    result = sqlInsert(sqlQuery, sqlValTuple)

    if not result['inserted_id']:
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response) 

    # Get refkey
    sqlQueryRefKey = "SELECT `Ref_Key` FROM `sps_relatives` WHERE `Language_ID` = %s AND `Status` = %s ORDER BY `Ref_Key` DESC LIMIT 1;"
    sqlValTupleRK = (languageID, 1)
    resultRK = sqlSelect(sqlQueryRefKey, sqlValTupleRK, True)
    if resultRK['length'] > 0:
        spsRefKey = resultRK['data'][0]['Ref_Key'] + 1
    else:
        spsRefKey = 1

    spsID = result['inserted_id']
    sqlQuerySPSRel = "INSERT INTO `sps_relatives` (`SPS_ID`, `Ref_Key`, `Language_ID`, `User_ID`, `Status`) VALUES (%s, %s, %s, %s, %s)"
    sqlValTupleSPSRel = (spsID, spsRefKey, languageID, userID, 1)
    sqlInsert(sqlQuerySPSRel, sqlValTupleSPSRel)
    
    i = 0
    sqlValues = []
    sqlSyntax = ''
    sqlQuerySPSS = "INSERT INTO `sub_product_specifications` (`Name`, `Order`, `spsID`, `Status`) VALUES (%s, %s, %s, %s)" 
    sqlQuerySPSSRel = "INSERT INTO `spss_relatives` (`SPSS_ID`, `Ref_Key`, `Language_ID`, `User_ID`, `Status`) VALUES (%s, %s, %s, %s, %s)"
    
    # Get refkey
    sqlQueryRefKey = "SELECT `Ref_Key` FROM `spss_relatives` WHERE `Language_ID` = %s AND `Status` = %s ORDER BY `Ref_Key` DESC LIMIT 1;"
    sqlValTupleRK = (languageID, 1)
    resultRK = sqlSelect(sqlQueryRefKey, sqlValTupleRK, True)
    if resultRK['length'] > 0:
        spssRefKey = resultRK['data'][0]['Ref_Key'] + 1
    else:
        spssRefKey = 1


    while True:
        spsText = request.form.get('text_' + str(i))
        if not spsText: 
            break

        sqlValTuple = (spsText, i, spsID, 1)
        result = sqlInsert(sqlQuerySPSS, sqlValTuple)

        spssID = result['inserted_id']
        spssRefKey = int(spssRefKey) + i

        sqlValTupleSPSRel = (spssID, spssRefKey, languageID, userID, 1)
        sqlInsert(sqlQuerySPSSRel, sqlValTupleSPSRel)
        
        i = i + 1

    # return result['status']
    response = {'status': '1', 'answer': result['answer'], 'newCSRFtoken': newCSRFtoken}
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        newCSRFtoken = generate_csrf()
        # Checking username
        username = request.form.get('username') 
        if not username:
            answer = gettext('Please specify username')
            response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
            return jsonify(response)
        

        # Checking passwords 
        password = request.form.get('password') 
        if not password:
            answer = gettext('Please specify password')
            response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
            return jsonify(response)
        
        sqlQuery = "SELECT * FROM `stuff` WHERE `Username` = %s AND `Status` = 1"
        sqlValTuple  = (username,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)    
        

        if result['length'] == 1 and check_password_hash(result['data'][0]["Password"], password): 
            session['user_id'] = result['data'][0]['ID']
            response = {'status': '1'}
            return jsonify(response)
        else:
            answer = gettext('The username or password do not match')
            response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
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


def table(structure):

    structure = {
        'rows': [], # [{}, {}, {}, ... ]
        'header': [], # ['ID', 'Name', 'Status', ... ]
        'buttons': [], # ['url', 'name']
        'pagination': [] # True, False
    }
    
    return render_template('table.html', structure=structure, current_locale=get_locale())


def getSlides(PrID):
    sqlQueryTitle = "SELECT `Title` FROM `product` WHERE `ID` = %s;"
    sqlValTuple = (PrID,)
    resultTitle = sqlSelect(sqlQueryTitle, sqlValTuple, True)

    sqlQuery = f"""SELECT `slider`.`ID` AS `sliderID`,
                          `slider`.`Name`,
                          `slider`.`Order`, 
                          `slider`.`Type`                          
                    FROM `slider`
                    -- LEFT JOIN `product` ON `product`.`ID` = `slider`.`ProductID`
                    WHERE `ProductID` = %s AND `slider`.`Type` = 1
                    ORDER BY `ORDER` ASC
                """
    sqlValTuple = (PrID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    sqlQuerySubProduct = f"""SELECT `product_type`.`ID`,
                                    -- `product_type`.`Price`,
                                    -- `product_type`.`Title`,
                                    `product_type`.`Order` AS `SubPrOrder`,
                                    `slider`.`ID` AS `sliderID`,
                                    `slider`.`AltText`,
                                    `slider`.`Name`,
                                    `slider`.`Order` AS `SliderOrder` 
                            FROM `product_type`
                            LEFT JOIN `slider` ON `slider`.`ProductID` = `product_type`.`ID`
                            WHERE `product_type`.`Product_ID` = %s AND `product_type`.`Status` = 1
                            AND `slider`.`Type` = 2
                            ORDER BY `SubPrOrder` ASC, `slider`.`Order` ASC;
                          """
    sqlSubPRValTuple = (PrID,)
    resultSubPr = sqlSelect(sqlQuerySubProduct, sqlSubPRValTuple, True)
    
    subProducts = []
    
    if resultSubPr['length'] > 0:
        subProducts = [{
                    'ID': resultSubPr['data'][0]['ID'],
                    # 'Price': resultSubPr['data'][0]['Price'],
                    # 'Title': resultSubPr['data'][0]['Title'],
                    'Name': resultSubPr['data'][0]['Name'],
                    'AltText': resultSubPr['data'][0]['AltText'],
                    'i': result['length']
                    }]
        
        if resultSubPr['length'] > 1:
            checker = resultSubPr['data'][0]['ID']
            myDict = {}
            i = result['length']
            for row in resultSubPr['data']:

                if checker != row['ID']:
                    myDict = {
                        'ID': row['ID'],
                        # 'Price': row['Price'],
                        # 'Title': row['Title'],
                        'Name': row['Name'],
                        'AltText': row['AltText'],
                        'i': i
                    }
                    subProducts.append(myDict)
                    checker = row['ID']
                
                i = i + 1
    sqlQuerySpss = f"""
                    SELECT 
                        `sub_product_specifications`.`ID` AS `spssID`,
                        `sub_product_specifications`.`Name` AS `Title`,
                        `product_type_details`.`Text`,
                        `product_type`.`Title` AS `ptTitle`,
                        `product_type`.`Price`,
                        `product_type`.`ID` AS `ptID`,
                        `product`.`Title` AS `prTitle`,
                        (SELECT COUNT(`ID`) FROM `product_type` WHERE `product_type`.`Product_ID` = %s) AS `ptCount`,
                        (SELECT SUM(`Quantity`) FROM `quantity` WHERE `productTypeID` = `ptID` AND `expDate` >= CURDATE()) AS `Quantity`
                    FROM `product_type`
                        LEFT JOIN `product_type_details` ON `Product_Type`.`ID` = `product_type_details`.`ProductTypeID`
                        LEFT JOIN `sub_product_specifications` ON `product_type_details`.`spssID` = `sub_product_specifications`.`ID`
                        LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                    WHERE `product_type`.`Product_ID` = %s
                        AND `product_type`.`Status` = 1
                    ORDER BY `product_type`.`Order`, `sub_product_specifications`.`Order`
                    ;
                    """
    sqlValTupleSpss = (PrID, PrID)
    resultSpss = sqlSelect(sqlQuerySpss, sqlValTupleSpss, True)

    # print('aaaaaaaaaaaaaaaaaa', resultSpss)
    return render_template('slideshow.html', result=result, resultSubPr=resultSubPr, resultSpss=resultSpss, subProducts=subProducts, Title = resultTitle['data'][0]['Title'], mainCurrency=MAIN_CURRENCY, current_locale=get_locale())


@app.route("/get-spacifications", methods=["POST"])
# @login_required
def get_specifications():
    newCSRFtoken = generate_csrf()
    if not request.form.get('LanguageID') or not request.form.get('spsID'):
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    languageID = request.form.get('LanguageID')
    spsID = request.form.get('spsID')

    sqlQuery = f"""
                    SELECT 
                        `sub_product_specifications`.`ID`,
                        `sub_product_specifications`.`Name` AS `Text`
                    FROM `sub_product_specification`
                    LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                    LEFT JOIN `sub_product_specifications` ON `sub_product_specifications`.`spsID` = `sub_product_specification`.`ID`
                    WHERE `sps_relatives`.`Language_ID` = %s 
                        AND `sub_product_specification`.`ID` = %s 
                        AND `sub_product_specifications`.`Status` = %s
                    ORDER BY `sub_product_specifications`.`Order`;
                    ;

                """
    sqlValTuple = (languageID, spsID, 1)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    
    return jsonify({'data': result['data'], 'status': '1'})


@app.route("/get-product-types", methods=["POST"])
# @login_required
def get_product_types():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    prID = request.form.get('prID')
    dataType = True
    if request.form.get('type'):
        dataType = False

    sqlQuery = """
                    SELECT  `product_type`.`ID`,
                            `product_type`.`Title`,
                            `product_type`.`Price`,
                            `product_type`.`Order` AS `SubPrOrder`,
                            (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                            (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                            `product_type`.`Status`
                    FROM `product_type`
                    WHERE `product_type`.`Product_ID` = %s
                    ORDER BY `SubPrOrder` 
                    ;"""
    sqlValTuple = (prID,)
    result = sqlSelect(sqlQuery, sqlValTuple, dataType)

    productTypeData = result['data']
    if dataType == False:
        productTypeData = json.dumps(result['data'])

    response = {'status': '1', 'data': productTypeData, 'length': result['length'], 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/get-product-types-quantity", methods=["POST"])
# @login_required
def get_product_types_quantity():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    prID = request.form.get('prID')
    dataType = True
    if request.form.get('type'):
        dataType = False

    filters = ''
    sqlValList = []
    sqlValList.append(prID)

    if request.form.get('productionDate'):
        filters = filters + ' AND `quantity`.`productionDate` = %s ' 
        sqlValList.append(request.form.get('productionDate'))

    if request.form.get('expDate'):
        filters = filters + ' AND `quantity`.`expDate` = %s ' 
        sqlValList.append(request.form.get('expDate'))

    if request.form.get('addDate'):
        filters = filters + ' AND `quantity`.`addDate` = %s ' 
        sqlValList.append(request.form.get('addDate'))

    if request.form.get('storeID'):
        filters = filters + ' AND `quantity`.`storeID` = %s ' 
        sqlValList.append(request.form.get('storeID'))

    if request.form.get('ptID'):
        filters = filters + ' AND `productTypeID` = %s ' 
        sqlValList.append(request.form.get('ptID'))

    
    if len(sqlValList) > 0:
        sqlValTuple = tuple(sqlValList)
    else: 
        sqlValTuple = (prID,)

    sqlQuery = f"""
                    SELECT  `product_type`.`ID`,
                            `product_type`.`Title`,
                            `product_type`.`Price`,
                            `product_type`.`Order` AS `SubPrOrder`,
                            (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                            (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                            SUM(`quantity`.`Quantity`) AS `Quantity`,
                            `product_type`.`Status`
                    FROM `quantity`
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                    WHERE `product_type`.`Product_ID` = %s {filters}
                    GROUP BY `product_type`.`ID`, `product_type`.`Title`, `product_type`.`Price`, `imgName`, `AltText`
                    ORDER BY `SubPrOrder` 
                    ;"""
    
    result = sqlSelect(sqlQuery, sqlValTuple, dataType)

    productTypeData = result['data']
    if dataType == False:
        productTypeData = json.dumps(result['data'])

    response = {'status': '1', 'data': productTypeData, 'length': result['length'], 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.template_filter('typeof')
def typeof(var):
    return str(type(var).__name__)



@app.route("/cart/<productTypesQuantity>", methods=["GET", "POST"])
@app.route("/cart", methods=["GET", "POST"])
def cart(productTypesQuantity=None): 
    if request.method == "GET":
        result = {'length': 0}
        if productTypesQuantity is not None and '&' in productTypesQuantity:
            arr = productTypesQuantity.split('&')
            print(arr)

        return render_template('cart.html', result=result, current_locale=get_locale())
    else:
        pass


@app.route("/get-pt-quantities", methods=["POST"])
def get_pt_quantities():     
    if not request.form.get('ptID'):
        answer = gettext(smthWrong)
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    newCSRFtoken = generate_csrf()
    ptID = request.form.get('ptID')

    filters = ''
    sqlValList = []
    sqlValList.append(ptID)

    if request.form.get('productionDate'):
        filters = filters + ' AND `quantity`.`productionDate` = %s ' 
        sqlValList.append(request.form.get('productionDate'))

    if request.form.get('expDate'):
        filters = filters + ' AND `quantity`.`expDate` = %s ' 
        sqlValList.append(request.form.get('expDate'))

    if request.form.get('addDate'):
        filters = filters + ' AND `quantity`.`addDate` = %s ' 
        sqlValList.append(request.form.get('addDate'))

    if request.form.get('storeID'):
        filters = filters + ' AND `quantity`.`storeID` = %s ' 
        sqlValList.append(request.form.get('storeID'))


    sqlValTuple = tuple(sqlValList)
        

    sqlQuary = f"""
                SELECT 
                    `quantity`.`ID`,
                     `product_type`.`ID` AS `ptID`,
                    `store`.`Name`,
                    CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `Initials`,
                    `quantity`.`Quantity`,
                    `quantity`.`maxQuantity`,
                    DATE_FORMAT(`productionDate`, '%d-%m-%Y') AS `productionDate`,
                    DATE_FORMAT(`expDate`, '%d-%m-%Y') AS `expDate`,
                    DATE_FORMAT(`addDate`, '%d-%m-%Y') AS `addDate`,
                    CONCAT(`product`.`Title`, ': ', `product_type`.`Title`) AS `Title`,
                    CASE 
                        WHEN `expDate` > CURDATE() THEN 0 
                        ELSE 1 
                    END AS `expStatus`
                FROM `quantity` 
                    LEFT JOIN `store` ON `store`.`ID` = `quantity`.`storeID`
                    LEFT JOIN `stuff` ON `stuff`.`ID` = `quantity`.`userID`
                    LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                    LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
                WHERE `quantity`.`productTypeID` = %s AND `quantity`.`Status` = '1' {filters}
                ;
            """
    
    result = sqlSelect(sqlQuary, sqlValTuple, True)
    # ptQuantityData = json.dumps(result['data'])
    ptQuantityData = result['data']

    response = {'status': '1', 'data': ptQuantityData, 'length': result['length'], 'answer': result['error'], 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/edit-store/<quantity_pt_IDs>", methods=["GET"])
@app.route("/edit-store", methods=["POST"])
# @login_required
def edit_store(quantity_pt_IDs=None):
    newCSRFtoken = generate_csrf()
    if request.method == "POST":
        if not request.form.get('quantityID') or request.form.get('quantityID') == 'null':
            answer = gettext(smthWrong)
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
    
        if not request.form.get('ptID') or request.form.get('ptID') == 'null':
            answer = gettext('Please Specify Product Type')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
    
        if not request.form.get('storeID'):
            answer = gettext('Please Specify Store')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('quantity') or request.form.get('quantity') == 'null':
            answer = gettext('Please Specify Quantity')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('quantity').isdigit():
            return jsonify({'status': '0', 'answer': smthWrong,  'newCSRFtoken': newCSRFtoken})

        if int(request.form.get('quantity')) < 1:
            answer = gettext('Quantity should be greater than Zero')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('productionDate'):
            answer = gettext('Please Specify Production Date')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('expDate'):
            answer = gettext('Please Specify Expiration Date')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})

        maxQuantity = None       
        if request.form.get('maxQuantity') != 'false':
            if not request.form.get('maxQuantity'):
                answer = gettext('Please Specify Max Allowed Quantity')
                return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
            
            if not request.form.get('maxQuantity').isdigit():
                return jsonify({'status': '0', 'answer': smthWrong + 'sSSSDASDF',  'newCSRFtoken': newCSRFtoken})

            if int(request.form.get('maxQuantity')) < 1:
                answer = gettext('Max Allowed Quantity should be greater than Zero')
                return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})    

            maxQuantity = request.form.get('maxQuantity')

        ptID = request.form.get('ptID')
        storeID = request.form.get('storeID')
        quantity = request.form.get('quantity')
        quantityID = request.form.get('quantityID')
        productionDate = request.form.get('productionDate').replace("-", "/")
        expDate = request.form.get('expDate').replace("-", "/")
        userID = session['user_id']

        sqlQuery =  """
                    UPDATE `quantity` SET
                        `productTypeID` = %s,  
                        `storeID` = %s,  
                        `Quantity` = %s,  
                        `maxQuantity` = %s,  
                        `userID` = %s,  
                        `productionDate` = STR_TO_DATE(%s, '%m/%d/%Y'),  
                        `expDate` = STR_TO_DATE(%s, '%m/%d/%Y'),  
                        `addDate` = CURRENT_DATE()
                    WHERE `ID` = %s
                    ;
                    """
        sqlValTuple = (ptID, storeID, quantity, maxQuantity, userID, productionDate, expDate, quantityID)
        result = sqlUpdate(sqlQuery, sqlValTuple)
        print('AAAAAAAAAAAAAAAAAAAAAA')
        print(result['answer'])
        if result['status'] == '-1':
            # response = {'status': '0', 'answer': gettext(smthWrong), 'newCSRFtoken': newCSRFtoken}
            response = {'status': '0', 'answer': result['answer'], 'newCSRFtoken': newCSRFtoken}
            return jsonify(response)        

        response = {'status': '1', 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)

    else:
        quantityID, ptID = quantity_pt_IDs.split('qptid')
        languageID = getLangID()

        sqlQuaryQuantity = """SELECT 
                                `ID`,
                                `productTypeID`,
                                `storeID`,
                                `Quantity`,
                                `maxQuantity`,
                                DATE_FORMAT(`productionDate`, '%d/%m/%Y') AS `productionDate`,
                                DATE_FORMAT(`expDate`, '%d/%m/%Y') AS `expDate`
                            FROM `quantity` 
                            WHERE `ID` = %s
                            ;
                            """
        sqlValTupQuantity = (quantityID,)
        resultQuantity = sqlSelect(sqlQuaryQuantity, sqlValTupQuantity, True)

        sqlQuery = """SELECT 
                        `product`.`ID`,
                        `product`.`Title`,
                        `product_type`.`ID` AS `ptID`,
                        `product_type`.`Title` AS `ptTitle`
                    FROM `product` 
                        LEFT JOIN `product_type` ON `product_type`.`Product_ID` = `product`.`ID`
                    WHERE `product`.`Language_ID` = %s 
                    ORDER BY `product`.`ID`, `product_type`.`Order` 
                    -- LIMIT 2
                    ;
                    """
        sqlValTuple = (languageID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        prData = json.dumps(result['data']) 

        sqlQueryStore = "SELECT `ID`, `Name` FROM `store` WHERE `Status` = 1;"
        resultStore = sqlSelect(sqlQueryStore, (), True)

        storeData = json.dumps(resultStore['data'])

        sideBar = side_bar_stuff()

        return render_template('edit_store.html', resultQuantity=resultQuantity['data'],  storeData=storeData, storeID = resultQuantity['data'][0]['storeID'], dataLength=result['length'], prData=prData, ptID=ptID, sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale()) 



@app.route("/add-to-store", methods=["GET", "POST"])
@app.route("/add-to-store/<ptID>", methods=["GET", "POST"])
# @login_required
def add_to_store(ptID=None):
    newCSRFtoken = generate_csrf()
    if request.method == "GET":
        languageID = getLangID()
        sqlQuery = """SELECT 
                        `product`.`ID`,
                        `product`.`Title`,
                        `product_type`.`ID` AS `ptID`,
                        `product_type`.`Title` AS `ptTitle`
                    FROM `product` 
                        LEFT JOIN `product_type` ON `product_type`.`Product_ID` = `product`.`ID`
                    WHERE `product`.`Language_ID` = %s 
                    ORDER BY `product`.`ID`, `product_type`.`Order` 
                    -- LIMIT 2
                    ;
                    """
        sqlValTuple = (languageID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        prData = json.dumps(result['data']) 

        sqlQueryStore = "SELECT `ID`, `Name` FROM `store` WHERE `Status` = 1;"
        resultStore = sqlSelect(sqlQueryStore, (), True)

        storeData = json.dumps(resultStore['data'])

        sideBar = side_bar_stuff()

        return render_template('add_to_store.html', storeData=storeData, dataLength=result['length'], prData=prData, ptID=ptID, sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    else:

        if not request.form.get('ptID') or request.form.get('ptID') == 'null':
            answer = gettext('Please Specify Product Type')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('storeID'):
            answer = gettext('Please Specify Store')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('quantity') or request.form.get('quantity') == 'null':
            answer = gettext('Please Specify Quantity')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('quantity').isdigit():
            return jsonify({'status': '0', 'answer': smthWrong,  'newCSRFtoken': newCSRFtoken})

        if int(request.form.get('quantity')) < 1:
            answer = gettext('Quantity should be greater than Zero')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('productionDate'):
            answer = gettext('Please Specify Production Date')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
        
        if not request.form.get('expDate'):
            answer = gettext('Please Specify Expiration Date')
            return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})

        maxQuantity = None       
        if request.form.get('maxQuantity') != 'false':
            if not request.form.get('maxQuantity'):
                answer = gettext('Please Specify Max Allowed Quantity')
                return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
            
            if not request.form.get('maxQuantity').isdigit():
                return jsonify({'status': '0', 'answer': smthWrong + 'sSSSDASDF',  'newCSRFtoken': newCSRFtoken})

            if int(request.form.get('maxQuantity')) < 1:
                answer = gettext('Max Allowed Quantity should be greater than Zero')
                return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})    

            maxQuantity = request.form.get('maxQuantity')

        ptID = request.form.get('ptID')
        storeID = request.form.get('storeID')
        quantity = request.form.get('quantity')
        productionDate = request.form.get('productionDate').replace("-", "/")
        expDate = request.form.get('expDate').replace("-", "/")
        userID = session['user_id']

        sqlQuery = f"""INSERT INTO `quantity` 
                        (`productTypeID`, `storeID`, `Quantity`, `maxQuantity`, `userID`, `productionDate`, `expDate`, `addDate`, `Status`) 
                        VALUES (%s, %s, %s, %s, %s, STR_TO_DATE(%s, '%m/%d/%Y'), STR_TO_DATE(%s, '%m/%d/%Y'), CURRENT_DATE(), '1');
                        """
        sqlValTuple = (ptID, storeID, quantity, maxQuantity, userID, productionDate, expDate)

        result= sqlInsert(sqlQuery, sqlValTuple)
        if result['status'] == 0:
            return jsonify({'status': '0', 'answer': smthWrong,  'newCSRFtoken': newCSRFtoken})

        answer = 'Done!'
        return jsonify({'status': '1', 'answer': answer,  'newCSRFtoken': newCSRFtoken})


# Check if product type exists in specified quantity
@app.route('/check-pt-quantity', methods=['POST'])
def check_pt_quantity():
    newCSRFtoken = generate_csrf()
    if not request.form.get('num') or not request.form.get('ptID') :
        answer = gettext(smthWrong)
        return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
    
    ptID = request.form.get('ptID') 
    num = request.form.get('num') 

    sqlQuery = "SELECT SUM(`Quantity`) AS `Quantity` FROM `quantity` WHERE `productTypeID` = %s AND `expDate` >= CURDATE() AND `Status` = 1;"
    sqlValTuple = (ptID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    print(result['data'])
    print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')

    if result['data'][0]['Quantity'] == None:
        answer = gettext("Out of stock")
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    # Check if there is a maximum quantity to buy
    sqlQueryMax = "SELECT `maxQuantity` FROM `quantity` WHERE `productTypeID` = %s AND `maxQuantity` IS NOT NULL AND `expDate` >= CURDATE()  AND `Status` = 1 ORDER BY `maxQuantity` DESC LIMIT 1;"
    sqlValTupleMax = (ptID,)
    resultMax = sqlSelect(sqlQueryMax, sqlValTupleMax, True)
    if resultMax['length'] > 0:
        maxQuantity = resultMax['data'][0]['maxQuantity']
        if maxQuantity < int(num):
            answer = gettext("Maximum available quantity for single purchase is ") + str(maxQuantity)
            return jsonify({'status': '2', 'max': maxQuantity, 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    if int(result['data'][0]['Quantity']) < int(num):
        maxQuantity = result['data'][0]['Quantity']

        answer = gettext("Maximum available quantity is ") + str(maxQuantity)
        return jsonify({'status': '2', 'max': maxQuantity, 'answer': answer, 'newCSRFtoken': newCSRFtoken})
   
    return jsonify({'status': '1', 'newCSRFtoken': newCSRFtoken})


@app.route("/timer", methods=["GET"])
def random_reminder():
    return render_template('random-reminder.html')


if __name__ == '__main__':
    app.run(ssl_context=(cert_file, key_file), debug=True)

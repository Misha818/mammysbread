from flask import Flask, render_template, request, jsonify, session, redirect, g, url_for
from flask_babel import Babel, _, lazy_gettext as _l, gettext
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from products import submit_notes_text, get_pr_order, slidesToEdit, checkCategoryName, checkProductCategoryName, get_RefKey_LangID_by_link, get_article_category_images, get_product_category_images, edit_p_h, edit_a_h, submit_reach_text, submit_product_text, add_p_c_sql, edit_p_c_view, edit_a_c_view, edit_p_c_sql, get_product_categories, get_ar_thumbnail_images, get_pr_thumbnail_images, add_product, productDetails, constructPrData, add_product_lang
from sysadmin import getLangdata, check_alias, get_order_status_list, get_affiliates, get_affiliate_reward_progress, get_promo_code_id_affiliateID, deletePUpdateP, insertPUpdateP, insertIntoBuffer, calculate_price_promo, clientID_contactID, checkSPSSDataLen, replace_spaces_in_text_nodes, totalNumRows, filter_multy_dict, getLangdatabyID, supported_langs, get_full_website_name, generate_random_string, get_meta_tags, removeRedundantFiles, checkForRedundantFiles, getFileName, fileUpload, get_ar_id_by_lang, get_pr_id_by_lang, getDefLang, getSupportedLangs, getLangID, sqlSelect, sqlInsert, sqlUpdate, sqlDelete, get_pc_id_by_lang, get_pc_ref_key, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError, generate_csrf
from OpenSSL import SSL
from flask_recaptcha import ReCaptcha
from io import BytesIO
from datetime import datetime, date, UTC
from bs4 import BeautifulSoup
import os
import json
import re
import copy

current_dir = os.path.dirname(os.path.abspath(__file__))
basedir = os.path.abspath(os.path.dirname(__file__))

# app = Flask(__name__)
# limiter = Limiter(get_remote_address, app=app)


app = Flask(__name__)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now(UTC).year}


# app.config['RECAPTCHA_SITE_KEY'] = os.getenv('SECRET_KEY')
# app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('SECRET_KEY')
# recaptcha = ReCaptcha(app)


# Initialize limiter with in-memory storage explicitly.
# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"],
#     storage_uri="memory://",  # explicitly using in-memory storage
#     strategy="fixed-window"
# )





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


# return = {
#             '0': gettext('Cancelled'),
#             '1': gettext('Panding'),
#             '2': gettext('Purchased'),
#             '3': gettext('Preparing'),
#             '4': gettext('Ready'),
#             '5': gettext('Delivered')
#         }


orderStatusList = get_order_status_list()

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('csrf_error.html', reason=e.description), 400


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


@app.route("/login", methods=["GET", "POST"])
# @limiter.limit("3 per minute")
def login():
    if request.method == "POST":
        # if recaptcha.verify():
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
        # else:
        #     return jsonify({'status': "0", 'answer': gettext("CAPTCHA verification failed.")})
    else:
        if 'user_id' in session:
            return redirect('/stuff')
        
        return render_template("login.html", current_locale=get_locale())


@app.errorhandler(429)
def ratelimit_handler(e):

    return jsonify({'status': '0', 'answer': gettext('Rate limit exceeded'), 'newCSRFtoken': generate_csrf()}), 429


@app.route('/submit_product_text', methods=['POST'])
@login_required
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
    refKey = request.args.get('RefKey', '')
    session['lang'] = lang
    if refKey != '':
        langData = getLangdata(lang)
        translated_path_segment = check_alias(refKey, langData['ID'])
        if translated_path_segment == False:
            return redirect(request.referrer)
        else:
            newUrl = url_for('home', _external=True) + translated_path_segment
            return redirect(newUrl)
    
    if 'langID' in request.referrer:
        newUrl = request.referrer.split('&langID=')[0]
        return redirect(newUrl)

    return redirect(request.referrer)

# @app.route('/setlang')
# def setlang():
#     defLang = getDefLang()
#     lang = request.args.get('lang', defLang['Prefix'])
#     session['lang'] = lang
#     print('request.referrer request.referrer request.referrer request.referrer request.referrer')
#     print(request.referrer)
#     print('request.referrer request.referrer request.referrer request.referrer request.referrer')
#     return
#     return redirect(request.referrer)

@app.route('/changeprorder', methods=['POST'])
@login_required
def change_pr_order():
    status = '0'
    if not request.form.get('order') or not request.form.get('order'):
        return jsonify({'status': status, 'answer': gettext('Something went wrong. Please try again!')})
    
    newOrder = int(request.form.get('order'))
    prID = int(request.form.get('prID'))
    langID = getLangID()

    sqlQueryOldOrder = "SELECT `Order` FROM `product` WHERE `ID` = %s;"
    resultOldOrder = sqlSelect(sqlQueryOldOrder, (prID,), True)
    oldOrder = resultOldOrder['data'][0]['Order']

    
    if oldOrder < newOrder:
        condition = "`Order` - 1"    
        sqlValTuple = (oldOrder+1, newOrder, langID)
    elif oldOrder > newOrder:
        condition = "`Order` + 1"    
        sqlValTuple = (newOrder, oldOrder-1, langID)
    
    sqlQuery =  f"""
                    UPDATE `product`
                    SET `Order` = {condition}
                    WHERE `Order` BETWEEN %s AND %s
                    AND `Language_ID` = %s
                """
    result = sqlUpdate(sqlQuery, sqlValTuple)
    if result['status'] == '-1':
        return jsonify({'status': status, 'answer': gettext('Something went wrong. Please try again!')})

    sqlQueryOdd = "UPDATE `product` SET `Order` = %s WHERE `ID` = %s;"
    sqlVT = (newOrder, prID)
    resultOdd = sqlUpdate(sqlQueryOdd, sqlVT)
    if resultOdd['status'] == '-1':
        return jsonify({'status': status, 'answer': gettext('Something went wrong. Please try again!')})

    status = '1'
    return jsonify({'status': status})


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
                    ORDER BY `product`.`Order` ASC
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
  
    return render_template('index.html', result=result, MAIN_CURRENCY=MAIN_CURRENCY, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes

@app.route('/about')
def about():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    AND `Product_Status` = 2
                    ORDER BY `product`.`Order` ASC
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='about', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/contacts')
def contacts():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    AND `Product_Status` = 2
                    ORDER BY `product`.`Order` ASC
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='contacts', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/favorites')
def favorites():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    AND `Product_Status` = 2
                    ORDER BY `product`.`Order` ASC
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='favorites', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/products-client')
def products_client():
    languageID = getLangID()
    sqlQuery =  f"""SELECT * FROM `product` 
                    LEFT JOIN `product_relatives`
                      ON  `product_relatives`.`P_ID` = `product`.`ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    AND `Product_Status` = 2
                    ORDER BY `product`.`Order` ASC
                """
    
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    return render_template('index.html', result=result, scrollTo='card-container-user', current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/order-tracker/<pdID>')
def order_tracker(pdID):
    languageID = getLangID()
    sqlQuery =  f"""SELECT `ID`, `Status` FROM `payment_details` 
                    WHERE `ID` = %s
                """
    
    sqlValTuple = (pdID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        return render_template('error.html', current_locale=get_locale())
    
    orderStatusList = get_order_status_list()

    return render_template('order-tracker.html', row=result['data'][0], orderStatusList=json.dumps(orderStatusList),  current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


@app.route('/other-products', methods=['POST'])
def other_products():
    if request.form.get('prID'):
        prID = request.form.get('prID')
        languageID = getLangID()
        sqlQuery =  f"""SELECT * FROM `product` 
                        LEFT JOIN `product_relatives`
                        ON  `product_relatives`.`P_ID` = `product`.`ID`
                        WHERE `product_relatives`.`Language_ID` = %s
                            AND `Product`.`ID` != %s
                            AND `Product_Status` = 2
                        ORDER BY `product`.`Order` ASC
                    """
        
        sqlValTuple = (languageID, prID)
        result = sqlSelect(sqlQuery, sqlValTuple, True)

        return jsonify({'status': "1", 'data': result})
    else:
        return jsonify({'status': "0"})
    

# Edit thumbnail image
@app.route('/pr-thumbnail/<RefKey>', methods=['GET'])
@login_required
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



@app.route('/buy-now/<surl>', methods=['GET'])
def buy_now(surl):
    newCSRFtoken = generate_csrf()
    mainCurrency = MAIN_CURRENCY
    key, val = surl.split('-')
    prDataGlobal = {'ptID': int(key), 'quantity': int(val) }
    return render_template('buy-now.html', prDataGlobal=prDataGlobal, mainCurrency=mainCurrency, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    newCSRFtoken = generate_csrf()
    if request.method == 'GET':
        mainCurrency = MAIN_CURRENCY
        return render_template('checkout.html', mainCurrency=mainCurrency, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    
    # 1. Lock some tables, unlock at the end
    # 2. check data validity
    # 3. client detection by phone number or registration 
    # 4. Calculate Total price to be purchased
    # 5. insert additional data into  payment_details table and get inserted id
    # 6. insert data into table buffer_store
    # 7. Send data to bank api
    # 8. recive answer from api 
    # 9. if answer == 1
        # insert data into purchase_history
    # else -- update table quantity 
    # 10. delete data from buffer_store
    # 11. unlock locked tables
    if request.method == 'POST':
        # Lock some tables, unlock at the end
        if not request.form.get('data'):
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})    

        json_str = request.form.get('data')

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

        # check data validity 

        if data['confirm-phone'] != data['phone']:
            answer = gettext('The phone numbers do not match')
            return jsonify({'status': "0", 'answer': answer, 'newCSRFtoken': newCSRFtoken})
        
        if data.get('email') != '' and data.get('email') is not None:
            emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            # Check if the email matches the pattern
            if not re.match(emailPattern, data['email']):
                answer = gettext('Invalid email format')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})

        paymentMethod = False
        for key, value in data.items():
            if key in ['credit', 'debit', 'paypal']:
                if value == True:
                    paymentMethod = key
            if key != 'email' and key != 'promo' and key != 'ptData' and list != type(value) != bool and value.strip() == '':
                answer = gettext('Invalid value for ') + key
                return jsonify({'status': "0", 'answer': answer, 'newCSRFtoken': newCSRFtoken})    

        if len(data['ptData']) == 0:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})   
        
        if paymentMethod == False:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})   
        # End of Validation


        # client detection || registration by phone number
        # returns {'clientID': clientID, 'contactID': contactID}
        ccIDs = clientID_contactID(data)
        clientID = ccIDs['clientID']
        contactID = ccIDs['contactID']
        note = data.get('note')
        notesID = None
        if note is not None:
            sqlQuery = "INSERT INTO `notes` (`note`, `type`, `addressee_type`, `add_user_id`) VALUES (%s, %s, %s, %s);"
            sqlValTuple = (note, 3, 2, clientID)
            result = sqlInsert(sqlQuery, sqlValTuple)
            notesID = result['inserted_id']
        # END of client detection || registration by phone number

        # Calculate Total price to be purchased. This also checks promo code's validity 
        # And 
        # priceARR = calculate_price_promo(data['ptData'], data['promo'])
        # if priceARR['status'] == "0":
        #     answer = gettext(priceARR['answer'])
        #     return jsonify({'status': "0", 'answer': answer, 'newCSRFtoken': newCSRFtoken})
        # if priceARR['status'] == "2":
        #     return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})            
        # if priceARR['status'] == "1":
        #     amount = priceARR['answer']
        # END of Calculate Total price to be purchased
        
        # Get Promo Code ID
        promoID, affiliateID = [None, None]
        print('AAAAAAAAAAAAAAAAAAAA')
        print(data['promo'])
        print(type(data['promo']))
        print('AAAAAAAAAAAAAAAAAAAA')
        if data['promo'] != '':
            promodict = get_promo_code_id_affiliateID(data['promo'])
            if len(promodict) > 0:
                promoID = promodict['ID']
                affiliateID = promodict['affiliateID']
            


        # insert additional data into  payment_details table and get inserted id
        sqlQueryPD = "INSERT INTO `payment_details` (`promo_code_id`, `promo_code`, `affiliateID`, `notesID`, `clientID`, `contactID`, `Status`) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        sqlValTuplePD = (promoID, data['promo'], affiliateID, notesID, clientID, contactID, 1)
        resultPD = sqlInsert(sqlQueryPD, sqlValTuplePD)
        if resultPD['status'] == 0:
            return jsonify({'status': "0", 'answer': resultPD['answer'], 'newCSRFtoken': newCSRFtoken})

    
        pdID = resultPD['inserted_id'] 
        # pdID = 1 

        # insert data into table buffer
        # This also checks if specified amount of product exists
        buffer = insertIntoBuffer(data, pdID, gettext('Something went wrong. Please try again!'))
        # print('AAAAAAAAAAAAAAAAAAAAAAA')
        # print(buffer)
        # print('AAAAAAAAAAAAAAAAAAAAAAA')
        if buffer['status'] == "0":
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!') + 'sdsds', 'newCSRFtoken': newCSRFtoken})
        
        if buffer['status'] == "2":
            return jsonify({'status': "0", 'answer': gettext("Invalid Promo Code"), 'newCSRFtoken': newCSRFtoken})
        
        # print(buffer['answer'])
        # print('totalPrice is ', buffer['totalPrice'])

        amount = buffer['totalPrice']
        
        # Send data to bank api
        # recive answer from api 
        bank_answer_status = 1
        # insert data to purchace_history

        if bank_answer_status == 1:
            paymentData = {
                'finalPrice': amount,
                'paymentMethod': 'Visa',
                'CMD': 4242,
                'paymentStatus': 1
            }
            purchseData = insertPUpdateP(pdID, paymentData)
            if purchseData['status'] == 0:
                return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
        

            # answer = gettext('Payment passed successfully') + ' ' + str(amount) + ' ' + MAIN_CURRENCY
            purchseData = json.dumps(purchseData['answer'])
            return jsonify({'status': "1", 'pdID': pdID, 'purchseData': purchseData, 'newCSRFtoken': newCSRFtoken})    
                

        # delete from bufer and update table quantity
        # update payment_details with id pdID
        deletePUpdateP(pdID)        
        answer = gettext('Payment failed')
        return jsonify({'status': "0", 'answer': answer, 'newCSRFtoken': newCSRFtoken})    
        

@app.route('/confirmation-page/<pdID>', methods=['GET'])
def confirmation_page(pdID):
    newCSRFtoken = generate_csrf()
    
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
            LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
    WHERE `payment_details`.`ID` = %s
    ORDER BY `product`.`Order`, `product_type`.`Order`;
"""
    result = sqlSelect(sqlQuery, (pdID,), True)
    if result['length'] == 0:
        return render_template('error.html')
    
    return render_template('confirmation-page.html', result=result['data'], mainCurrency = MAIN_CURRENCY, newCSRFtoken=newCSRFtoken,  current_locale=get_locale())


@app.route('/orders/<filter>', methods=['Get'])
# @login_required
def orders(filter): 
    newCSRFtoken = generate_csrf()
    filters = {}
    
    protoTuple = []
    where = ''

    if '&' in filter:
        array = filter.split('&')
        for linkStr in array:
            key, val = linkStr.split('=')
            filters[key] = val
            if key != 'page' and key != 'status':
                if key == 'Firstname' or key == 'Lastname':
                    protoTuple.append(f"%{val}%")
                else:    
                    protoTuple.append(val)


    else:
        key, val = filter.split('=')
        filters[key] = val
        filters['status'] = '1'
        protoTuple.append(1)

    where = ''    
    
    if filters.get('Firstname') is not None:
        where += f"""AND `clients`.`FirstName` LIKE '%' %s """

    if filters.get('Lastname') is not None:
        where += f"""AND `clients`.`LastName` LIKE '%' %s """
    
    if filters.get('phone') is not None:
        where += f"""AND `phones`.`phone` = %s """
    
    if filters.get('email') is not None:
        where += f"""AND `emails`.`email` = %s """

    if filters.get('promoCode') is not None:
        where += f"""AND `payment_details`.`promo_code` = %s """

    if filters.get('status') != 'all':
        where = where + 'AND `payment_details`.`Status` = %s '
        protoTuple.append(filters.get('status'))
    
    if len(where) > 0:
        where = 'WHERE ' + where[3:]

    page = filters['page']
    rowsToSelect = (int(page) - 1) * int(PAGINATION)

    sqlValTuple = tuple(protoTuple)

    sqlQuery = f"""
            SELECT 
                `payment_details`.`ID`,
                `payment_details`.`promo_code`,   
                `payment_details`.`final_price`,   
                `payment_details`.`Status`,   
                `clients`.`FirstName`,
                `clients`.`LastName`,
                `phones`.`phone`,
                `emails`.`email`
            FROM `payment_details` 
                LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
                LEFT JOIN `phones` ON `client_contacts`.`phoneID` = `phones`.`ID`
                LEFT JOIN `emails` ON `client_contacts`.`emailID` = `emails`.`ID`
                LEFT JOIN `addresses` ON `client_contacts`.`addressID` = `addresses`.`ID`
                LEFT JOIN `notes` ON `payment_details`.`notesID` = `notes`.`ID`
                LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
            {where}
                GROUP BY `payment_details`.`ID`
                ORDER BY `payment_details`.`ID` DESC
                LIMIT {rowsToSelect}, {int(PAGINATION)}; 
               """
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    numRows = totalNumRows('payment_details', where, sqlValTuple)
    
    orderStatusList = get_order_status_list()

    return render_template('orders.html', result=result, filters=filters, orderStatusList=orderStatusList, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    

@app.route('/affiliate-orders/<filter>', methods=['Get'])
# @login_required
def affiliate_orders(filter): 
    newCSRFtoken = generate_csrf()
    filters = {}
    
    protoTuple = [session['user_id']] * 3

    if '&' in filter:
        array = filter.split('&')
        for linkStr in array:
            key, val = linkStr.split('=')
            filters[key] = val
            if key != 'page' and key != 'status':
                if key == 'Firstname' or key == 'Lastname':
                    protoTuple.append(f"%{val}%")
                else:    
                    protoTuple.append(val)


    else:
        key, val = filter.split('=')
        filters[key] = val
        filters['status'] = '1'
        protoTuple.append(1)

    where = 'WHERE `payment_details`.`affiliateID` = %s '
    
    if filters.get('Firstname') is not None:
        where += f"""AND `clients`.`FirstName` LIKE '%' %s """

    if filters.get('Lastname') is not None:
        where += f"""AND `clients`.`LastName` LIKE '%' %s """
    
    if filters.get('phone') is not None:
        where += f"""AND `phones`.`phone` = %s """
    
    if filters.get('email') is not None:
        where += f"""AND `emails`.`email` = %s """

    if filters.get('promoCode') is not None:
        where += f"""AND `payment_details`.`promo_code` = %s """

    if filters.get('status') != 'all' and filters.get('status') != 'pending':
        where = where + 'AND `payment_details`.`Status` = %s '
        protoTuple.append(filters.get('status'))


    if filters.get('status') == 'pending':
        where = where + 'AND `payment_details`.`Status` in (2,3,4) '
    

    page = filters['page']
    rowsToSelect = (int(page) - 1) * int(PAGINATION)

    sqlValTuple = tuple(protoTuple)

    sqlQuery = f"""
             SELECT
                `payment_details`.`ID`,
                `payment_details`.`ID` AS `pdID`,
                `payment_details`.`promo_code`,
                `payment_details`.`final_price`,
                `payment_details`.`Status`,
                `clients`.`FirstName`,
                `clients`.`LastName`,

                -- count affiliate revard
                (SELECT 
                    SUM(CASE 
                        WHEN `discount`.`revard_type` =  1 
                            THEN `discount`.`revard_value` * `purchase_history`.`quantity` 
                        ELSE  `purchase_history`.`quantity` * `purchase_history`.`price` * `discount`.`revard_value` / 100
                    END) 
                FROM `purchase_history` 
                    LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                    LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                    LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
                    LEFT JOIN `discount` ON `discount`.`ptID` = `product_type`.`ID` 
                        AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                WHERE `payment_details`.`ID` = `pdID`     
                    AND `payment_details`.`affiliateID` = %s
                    AND `purchase_history`.`discount` is not null
                GROUP BY `payment_details`.`ID`) AS `RV`,
                -- COUNT NET
                (SELECT 
                    SUM(`purchase_history`.`quantity` * `purchase_history`.`price` - `purchase_history`.`quantity` * `purchase_history`.`price` * `purchase_history`.`discount` / 100) AS `net`
                FROM `purchase_history` 
                    LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                    LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                    LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
                    LEFT JOIN `discount` ON `discount`.`ptID` = `product_type`.`ID` 
                        AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                WHERE `payment_details`.`ID` = `pdID`  
                    AND `payment_details`.`affiliateID` = %s
                    AND `purchase_history`.`discount` is not null
                GROUP BY `payment_details`.`ID`) AS `Discounted_Price`
            FROM `payment_details`
                LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
                LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`            
                {where}
            GROUP BY `payment_details`.`ID`
            ORDER BY `payment_details`.`ID` DESC
            LIMIT {rowsToSelect}, {int(PAGINATION)}; 
               """
    
    # sqlQuery = f"""
    #         SELECT 
    #             `payment_details`.`ID`,
    #             `payment_details`.`promo_code`,   
    #             `payment_details`.`final_price`,   
    #             `payment_details`.`Status`,   
    #             `clients`.`FirstName`,
    #             `clients`.`LastName`
    #         FROM `payment_details` 
    #             LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
    #             LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
    #             LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
    #         {where}
    #             GROUP BY `payment_details`.`ID`
    #             ORDER BY `payment_details`.`ID` DESC
    #             LIMIT {rowsToSelect}, {int(PAGINATION)}; 
    #            """
    
    orderStatusList = get_order_status_list()

    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    numRows = totalNumRows('payment_details', where, sqlValTuple)
    # numRows = totalNumRows('payment_details')

    return render_template('affiliate-orders.html', result=result, filters=filters, orderStatusList=orderStatusList, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())


@app.route('/stuff-affiliate-orders/<filter>', methods=['Get'])
# @login_required
def stuff_affiliate_orders(filter): 
    newCSRFtoken = generate_csrf()
    filters = {}
    
    protoTuple = []

    if '&' in filter:
        array = filter.split('&')
        for linkStr in array:
            key, val = linkStr.split('=')
            filters[key] = val
            if key != 'page' and key != 'status' and key != 'affiliate':
                if key == 'Firstname' or key == 'Lastname':
                    protoTuple.append(f"%{val}%")
                else:    
                    protoTuple.append(val)


    else:
        key, val = filter.split('=')
        filters[key] = val
        filters['status'] = '1'
        protoTuple.append(1)

    where = 'WHERE `payment_details`.`affiliateID` = %s '
    
    if filters.get('Firstname') is not None:
        where += f"""AND `clients`.`FirstName` LIKE '%' %s """

    if filters.get('Lastname') is not None:
        where += f"""AND `clients`.`LastName` LIKE '%' %s """
    
    if filters.get('phone') is not None:
        where += f"""AND `phones`.`phone` = %s """
    
    if filters.get('email') is not None:
        where += f"""AND `emails`.`email` = %s """

    if filters.get('promoCode') is not None:
        where += f"""AND `payment_details`.`promo_code` = %s """

    if filters.get('status') != 'all' and filters.get('status') != 'pending':
        where = where + 'AND `payment_details`.`Status` = %s '
        protoTuple.append(filters.get('status'))


    if filters.get('status') == 'pending':
        where = where + 'AND `payment_details`.`Status` in (2,3,4) '
    
    if filters.get('affiliate') is None or filters.get('affiliate') == '':
        return render_template('error.html', current_locale=get_locale())

    page = filters['page']
    rowsToSelect = (int(page) - 1) * int(PAGINATION)

    protoTuple = [filters['affiliate']] * 3 + protoTuple
    sqlValTuple = tuple(protoTuple)

    sqlQuery = f"""
             SELECT
                `payment_details`.`ID`,
                `payment_details`.`ID` AS `pdID`,
                `payment_details`.`promo_code`,
                `payment_details`.`final_price`,
                `payment_details`.`Status`,
                `clients`.`FirstName`,
                `clients`.`LastName`,
                CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `affiliate`,

                -- count affiliate revard
                (SELECT 
                    SUM(CASE 
                        WHEN `discount`.`revard_type` =  1 
                            THEN `discount`.`revard_value` * `purchase_history`.`quantity` 
                        ELSE  `purchase_history`.`quantity` * `purchase_history`.`price` * `discount`.`revard_value` / 100
                    END) 
                FROM `purchase_history` 
                    LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                    LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                    LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
                    LEFT JOIN `discount` ON `discount`.`ptID` = `product_type`.`ID` 
                        AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                WHERE `payment_details`.`ID` = `pdID`     
                    AND `payment_details`.`affiliateID` = %s
                    AND `purchase_history`.`discount` is not null
                GROUP BY `payment_details`.`ID`) AS `RV`,
                -- COUNT NET
                (SELECT 
                    SUM(`purchase_history`.`quantity` * `purchase_history`.`price` - `purchase_history`.`quantity` * `purchase_history`.`price` * `purchase_history`.`discount` / 100) AS `net`
                FROM `purchase_history` 
                    LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                    LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                    LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
                    LEFT JOIN `discount` ON `discount`.`ptID` = `product_type`.`ID` 
                        AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                WHERE `payment_details`.`ID` = `pdID`  
                    AND `payment_details`.`affiliateID` = %s
                    AND `purchase_history`.`discount` is not null
                GROUP BY `payment_details`.`ID`) AS `Discounted_Price`
            FROM `payment_details`
                LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
                LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                LEFT JOIN `stuff` ON `stuff`.`ID` = `payment_details`.`affiliateID`            
                {where}
            GROUP BY `payment_details`.`ID`
            ORDER BY `payment_details`.`ID` DESC
            LIMIT {rowsToSelect}, {int(PAGINATION)}; 
               """
    
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    sideBar = side_bar_stuff()

    numRows = totalNumRows('payment_details', where, sqlValTuple)

    orderStatusList = get_order_status_list()

    return render_template('affiliate-orders.html', result=result, filters=filters, affID=filters['affiliate'], orderStatusList=orderStatusList, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    

@app.route('/send-email/<email>', methods=['GET'])
# @login_required
def send_email(email):
    newCSRFtoken = generate_csrf()
    return 1

@app.route('/order-details/<pdID>', methods=['GET'])
# @login_required
def order_details(pdID):
    newCSRFtoken = generate_csrf()
    
    sqlQuery = f"""
    SELECT 
        `payment_details`.`ID`,
        `payment_details`.`payment_method`,
        `payment_details`.`CMD`,
        `payment_details`.`promo_code`,   
        `payment_details`.`promo_code_id`,   
        `payment_details`.`final_price`,   
        `payment_details`.`timestamp`,   
        `payment_details`.`Status`,   
        `delivered`.`timestamp` AS `deliveryDate`,
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
            LEFT JOIN `delivered` ON `delivered`.`pdID` = `payment_details`.`ID`
            LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
            LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
            LEFT JOIN `phones` ON `client_contacts`.`phoneID` = `phones`.`ID`
            LEFT JOIN `emails` ON `client_contacts`.`emailID` = `emails`.`ID`
            LEFT JOIN `addresses` ON `client_contacts`.`addressID` = `addresses`.`ID`
            LEFT JOIN `notes` ON `payment_details`.`notesID` = `notes`.`ID`
            LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
            LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
    WHERE `payment_details`.`ID` = %s
    ORDER BY `product`.`Order`, `product_type`.`Order`
    ;
"""
    result = sqlSelect(sqlQuery, (pdID,), True)
    if result['length'] == 0:
        return render_template('error.html')
    
    sideBar = side_bar_stuff()
    return render_template('order-details.html', sideBar=sideBar, result=result['data'], mainCurrency = MAIN_CURRENCY, newCSRFtoken=newCSRFtoken,  current_locale=get_locale())
    

@app.route('/affiliate-order-details/<pdID>', methods=['GET'])
# @login_required
def affiliate_order_details(pdID):
    newCSRFtoken = generate_csrf()
    
#     sqlQuery = f"""
#     SELECT 
#         `payment_details`.`ID`,
#         `payment_details`.`payment_method`,
#         `payment_details`.`CMD`,
#         `payment_details`.`promo_code`,   
#         `payment_details`.`promo_code_id`,   
#         `payment_details`.`final_price`,   
#         `payment_details`.`timestamp`,   
#         `payment_details`.`Status`,   
#         `delivered`.`timestamp` AS `deliveryDate`,
#         `clients`.`FirstName`,
#         `clients`.`LastName`,
#         `product`.`Title` AS `prTitle`,
#         `product_type`.`Title` AS `ptTitle`,
#         `purchase_history`.`quantity`,
#         `purchase_history`.`price`,
#         `purchase_history`.`discount`
#     FROM `payment_details` 
#             LEFT JOIN `delivered` ON `delivered`.`pdID` = `payment_details`.`ID`
#             LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
#             LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
#             LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
#             LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
#             LEFT JOIN `promo_code` ON `promo_code`.`ID` = `payment_details`.`promo_code_id`
#     WHERE `payment_details`.`ID` = %s AND `promo_code`.`affiliateID` = %s;
# """

    sqlQuery = f"""
                    SELECT 
                        `payment_details`.`ID`,
                        `payment_details`.`promo_code_id`,
                        `payment_details`.`timestamp`, 
                        `payment_details`.`Status`,
                        `delivered`.`timestamp` AS `deliveryDate`,
                        -- `purchase_history`.`ID`,	
                        `purchase_history`.`ptID`,	
                        `purchase_history`.`quantity`,		
                        `purchase_history`.`price`,	
                        `purchase_history`.`discount`,
                        `product`.`Title` AS `prTitle`,
                        `product_type`.`Title` AS `ptTitle`,
                        `discount`.`promo_code_id`,
                        `promo_code`.`Promo` AS `promo_code`,
                        `discount`.`revard_value`,
                        `discount`.`revard_type`,
                        `clients`.`FirstName`,
                        `clients`.`LastName`
                    FROM `purchase_history` 
                       LEFT JOIN `payment_details` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                        LEFT JOIN `delivered` ON `delivered`.`pdID` = `payment_details`.`ID`
                        LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                        LEFT JOIN `promo_code` ON `payment_details`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type` ON `purchase_history`.`ptID` = `product_type`.`ID`
                        LEFT JOIN `product` ON `product`.`ID` = `product_type`.`product_ID`
                        LEFT JOIN `discount` ON `discount`.`ptID` = `product_type`.`ID` 
                            AND `discount`.`promo_code_id` = `payment_details`.`promo_code_id`
                    WHERE `purchase_history`.`payment_details_id` = %s
                        AND `promo_code`.`affiliateID` = %s
                        AND `purchase_history`.`discount` is not null;
                """

    result = sqlSelect(sqlQuery, (pdID, session.get('user_id')), True)
    if result['length'] == 0:
        return render_template('error.html')
    
    sideBar = side_bar_stuff()
    return render_template('affiliate-order-details.html', sideBar=sideBar, result=result['data'], mainCurrency = MAIN_CURRENCY, newCSRFtoken=newCSRFtoken,  current_locale=get_locale())
    
    

@app.route('/get-affiliate-transfer-details', methods=['POST'])
# @login_required
def get_affiliate_transfer_details():
    newCSRFtoken = generate_csrf()
    if not request.form.get('notesID'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    notesID = request.form.get('notesID')
    sqlQuery = """SELECT 
                    `notes`.`ID`, 
                    `notes`.`note` 
                FROM `notes` 
                LEFT JOIN `partner_payments` ON `partner_payments`.`ID` = `notes`.`refID`
                WHERE  `notes`.`ID` = %s AND `partner_payments`.`affiliateID` = %s;"""

    result = sqlSelect(sqlQuery, (notesID, session['user_id']), True)
    if result['length'] == 0:
        return jsonify({'status': "0", 'answer': result['error'], 'newCSRFtoken': newCSRFtoken})

    return jsonify({'status': "1", 'row': result['data'][0], 'newCSRFtoken': newCSRFtoken})
        

@app.route('/get-transfer-details', methods=['POST'])
# @login_required
def get_transfer_details():
    newCSRFtoken = generate_csrf()
    if not request.form.get('notesID'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    notesID = request.form.get('notesID')
    sqlQuery = "SELECT  `notes`.`ID`, `notes`.`note` FROM `notes` WHERE  `notes`.`ID` = %s"

    result = sqlSelect(sqlQuery, (notesID,), True)
    if result['length'] == 0:
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    return jsonify({'status': "1", 'row': result['data'][0], 'newCSRFtoken': newCSRFtoken})
    
    
@app.route('/get-order-details', methods=['POST'])
# @login_required
def get_order_details():
    if not request.form.get('orderID'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!')})
    
    pdID = request.form.get('orderID')

    sqlQuery = f"""
                    SELECT 
                        `payment_details`.`ID`,
                        `payment_details`.`promo_code`,   
                        `payment_details`.`final_price`,   
                        `payment_details`.`Status`,   
                        `clients`.`FirstName`,
                        `clients`.`LastName`,
                        `phones`.`phone`,
                        `addresses`.`address`,
                        `emails`.`email`
                    FROM `payment_details` 
                        LEFT JOIN `clients` ON `payment_details`.`clientID` = `clients`.`ID`
                        LEFT JOIN `client_contacts` ON `payment_details`.`contactID` = `client_contacts`.`ID`
                        LEFT JOIN `phones` ON `client_contacts`.`phoneID` = `phones`.`ID`
                        LEFT JOIN `emails` ON `client_contacts`.`emailID` = `emails`.`ID`
                        LEFT JOIN `addresses` ON `client_contacts`.`addressID` = `addresses`.`ID`
                        LEFT JOIN `purchase_history` ON `payment_details`.`ID` = `purchase_history`.`payment_details_id`
                    WHERE `payment_details`.`ID` = %s
                        GROUP BY `payment_details`.`ID`
                        ORDER BY `payment_details`.`ID` DESC
                    ;
                """
    result = sqlSelect(sqlQuery, (pdID,), True)
    orderStatusList = get_order_status_list()

    return jsonify({'status': "1", 'data': result['data'], "statusList": orderStatusList, "newCSRFtoken": generate_csrf()})

@app.route('/edit-order-details', methods=['POST'])
# @login_required
def edit_order_details():
    newCSRFtoken = generate_csrf()
    if not request.form.get('orderID') or not request.form.get('firstname') or not request.form.get('lastname') or not request.form.get('phone') or not request.form.get('address') or not request.form.get('status'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    phone = request.form.get('phone')
    phone = ''.join(filter(str.isdigit, phone))

    Email = ''
    if request.form.get('email'):
        Email = request.form.get('email').strip()
        # Validate email
        emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        # Check if the email matches the pattern
        if not re.match(emailPattern, Email):
            answer = gettext('Invalid email format')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    


    pdID = request.form.get('orderID')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    address = request.form.get('address')
    status = request.form.get('status')    

    sqlQuery = "SELECT * FROM `emails` WHERE `email` = %s;"
    sqlValTuple = (Email,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        langID = getLangdata(session['lang'])['ID']
        sqlQuery = "INSERT INTO `emails` (`email`, `langID`) VALUES (%s, %s);"
        sqlValTuple = (Email, langID)
        result = sqlInsert(sqlQuery, sqlValTuple)
        emailID = result['inserted_id']
    else:
        emailID = result['data'][0]['ID']

    sqlQuery = "SELECT * FROM `clients` WHERE `FirstName` = %s AND `LastName` = %s;"
    sqlValTuple = (firstname, lastname)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        sqlQuery = "INSERT INTO `clients` (`FirstName`, `LastName`) VALUES (%s, %s);"
        sqlValTuple = (firstname, lastname)
        result = sqlInsert(sqlQuery, sqlValTuple)
        clientID = result['inserted_id']
    else:
        clientID = result['data'][0]['ID']

    sqlQuery = "SELECT * FROM `phones` WHERE `phone` = %s;"
    sqlValTuple = (phone,)  
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        sqlQuery = "INSERT INTO `phones` (`phone`) VALUES (%s);"
        sqlValTuple = (phone,)
        result = sqlInsert(sqlQuery, sqlValTuple)
        phoneID = result['inserted_id']
    else:
        phoneID = result['data'][0]['ID']
    
    sqlQuery = "SELECT * FROM `addresses` WHERE `address` = %s;"
    sqlValTuple = (address,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        sqlQuery = "INSERT INTO `addresses` (`address`) VALUES (%s);"
        sqlValTuple = (address,)
        result = sqlInsert(sqlQuery, sqlValTuple)
        addressID = result['inserted_id']
    else:
        addressID = result['data'][0]['ID']

    sqlQuery = "SELECT `clientID`, `contactID`, `Status` FROM `payment_details` WHERE `ID` = %s;"
    result = sqlSelect(sqlQuery, (pdID,), True)
    if result['length'] == 0:
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    clientID = result['data'][0]['clientID']
    contactID = result['data'][0]['contactID']
    Status = result['data'][0]['Status']

    sqlQuery = "UPDATE `clients` SET `FirstName` = %s, `LastName` = %s WHERE `ID` = %s;"
    sqlValTuple = (firstname, lastname, clientID)
    result = sqlUpdate(sqlQuery, sqlValTuple)
    if result['status'] == '-1':
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    sqlQuery = "UPDATE `client_contacts` SET `phoneID` = %s, `emailID` = %s, `addressID` = %s WHERE `ID` = %s;"
    sqlValTuple = (phoneID, emailID, addressID, contactID)
    result = sqlUpdate(sqlQuery, sqlValTuple)
    if result['status'] == '-1':
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    if Status != int(status):
        sqlQuery = "UPDATE `payment_details` SET `Status` = %s WHERE `ID` = %s;"
        sqlValTuple = (status, pdID)
        result = sqlUpdate(sqlQuery, sqlValTuple)
        if result['status'] == '-1':
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

        if status == '5':
            sqlQuery = "SELECT * FROM `delivered` WHERE `pdID` = %s;"
            result = sqlSelect(sqlQuery, (pdID,), True)
            if result['length'] == 0:
                sqlQurty = "INSERT INTO `delivered` (`pdID`, `timestamp`) VALUES (%s, NOW());"
                result = sqlInsert(sqlQurty, (pdID,))
                if result['status'] == '-1':
                    return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
            else:
                sqlQuery = "UPDATE `delivered` SET `timestamp` = NOW() WHERE `pdID` = %s;"
                result = sqlUpdate(sqlQuery, (pdID,))
                if result['status'] == '-1':
                    return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    return jsonify({'status': "1", "newCSRFtoken": generate_csrf()})


@app.route('/get_slides', methods=['POST'])
@login_required
def get_slides():
    if not request.form.get('ProductID') or not request.form.get('languageID'):
        return []
    
    PrID = request.form.get('ProductID')
    LanguageID = request.form.get('languageID')
    result = slidesToEdit(PrID)

    return result


@app.route('/add-price/<prID_RefKey>', methods=["GET"])
@login_required
def add_price(prID_RefKey):
    languageID = getLangID()
    if 'langID' in prID_RefKey:
        languageID = prID_RefKey.split('&langID=')[1]
        prID_RefKey = prID_RefKey.split('&langID=')[0]

        if len(getLangdatabyID(languageID)) == 0:
            return render_template('error.html')
        
        session['lang'] = getLangdatabyID(languageID)['Prefix']
    

    prID = prID_RefKey
    PT_Ref_Key = ''
    if '&' in prID_RefKey:
        prID = prID_RefKey.split('&')[0]
        PT_Ref_Key = prID_RefKey.split('&')[1]    


    answer = gettext('Something is wrong!')
    # newCSRFtoken = generate_csrf()
    mainCurrency = MAIN_CURRENCY
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
    
    sideBar = side_bar_stuff()
    return render_template('add-price.html', prData=prData, sps=resultSPS, specifications=resultSpecifications, PT_Ref_Key=PT_Ref_Key, sideBar=sideBar, mainCurrency=mainCurrency, current_locale=get_locale())


# Edit price view
@app.route('/edit-price/<ptID>', methods=['GET'])
@login_required
def edit_price(ptID):    
    languageID = getLangID()
    oldLangID = languageID
    
    newCSRFtoken = generate_csrf()
    if 'langID' in ptID:
        languageID = ptID.split('&langID=')[1]
        ptID = ptID.split('&langID=')[0]

        if len(getLangdatabyID(languageID)) == 0:
            return render_template('error.html')
        
        session['lang'] = getLangdatabyID(languageID)['Prefix']

    sideBar = side_bar_stuff()
    sqlQueryMain = f"""
                    SELECT  
                            `product_type_relatives`.`PT_Ref_Key`,
                            `product_type`.`ID`,
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
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_ID` = `product_type`.`ID` 
                    WHERE `product_type_relatives`.`PT_Ref_Key`= %s 
                        AND `product_type_relatives`.`Language_ID` = %s
                    ORDER BY `SubPrOrder`  ASC, `slider`.`Order` ASC;
                    """
    sqlValTupleMain = (ptID, languageID)
    mainResult = sqlSelect(sqlQueryMain, sqlValTupleMain, True)
    if mainResult['length'] == 0:
        if session['lang'] == getDefLang()['Prefix']:
            return render_template('error.html')
        else:
            # I have
            # PT_Ref_Key, languageID, oldLangID
            # PT_Ref_Key, oldLangID, languageID

            # Get product ref key
            sqlQueryPRK = """SELECT `product_relatives`.`P_Ref_Key` FROM `product_type_relatives`
                                LEFT JOIN `product_type` ON `product_type`.`ID` = `product_type_relatives`.`PT_ID`
                                LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                                LEFT JOIN `product_relatives` ON `product`.`ID` = `product_relatives`.`P_ID`
                            WHERE `product_type_relatives`.`PT_Ref_Key` = %s
                            LIMIT 1"""
            resultPRK = sqlSelect(sqlQueryPRK, (ptID,), True)
            if resultPRK['length'] == 0:
                return render_template('error.html', current_loacale=get_locale())
            
            P_Ref_Key = resultPRK['data'][0]['P_Ref_Key']

            sqlQueryPrIDRefKey = f"""
                                        SELECT 
                                            `product_relatives`.`P_Ref_Key`,
                                            `product_relatives`.`Language_ID`,
                                            `product_relatives`.`P_ID`,
                                            (SELECT `product_type_relatives`.`PT_ID`  FROM `product_type_relatives`
                                                WHERE `product_type_relatives`.`PT_Ref_Key` = %s
                                                    AND `product_type_relatives`.`Language_ID` = %s) AS `PT_ID`   
                                        FROM `product_relatives`     
                                        WHERE `product_relatives`.`P_Ref_Key` = %s
                                            AND `product_relatives`.`Language_ID` =%s    
                                    ;"""

            # Though the var is called ptID actuelly it is PT_Ref_Key
            sqlValTuplePrIDRefKey = (ptID, languageID, P_Ref_Key, languageID)
            resultPrIDRefKey = sqlSelect(sqlQueryPrIDRefKey, sqlValTuplePrIDRefKey, True)
            if resultPrIDRefKey['length'] == 0:
                content = {
                    'message': gettext('To continue translate the product first'),
                    'forwardUrl': url_for('pd', RefKey=str(P_Ref_Key)), 
                    'backUrl': url_for('edit_price', ptID=str(ptID)+'&langID='+str(getDefLang()['id']))
                }
                return render_template('choose.html', content=content, sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())

            if resultPrIDRefKey['data'][0]['PT_ID'] == None:
                prID_RefKey = str(resultPrIDRefKey['data'][0]['P_ID'])+'&' + ptID + '&langID=' + str(languageID)
                redirectUrl = url_for('add_price', prID_RefKey=prID_RefKey)
                return redirect(redirectUrl) 

    # sqlQuerySpss es queryin el a penq relativesov anel    
    ptID = mainResult['data'][0]['ID']
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
    
    return render_template('edit-price.html', sideBar=sideBar, mainResult=mainResult, sps=spsResult, resultSPSS=resultSPSS, languageID=languageID, newCSRFtoken=newCSRFtoken, current_locale=get_locale())


# Edit price action
@app.route('/editprice', methods=['POST'])
@login_required
def editprice():
    newCSRFtoken = generate_csrf()
    ptID = request.form.get('PtID')

    if not ptID:
        answer = gettext('Something went wrong. Please try again!')
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
  
    if float(request.form.get('price')) <= 0:
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
                answer = gettext('Something went wrong. Please try again!')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
            
            slideID = request.form.get('slideID_' + str(i))
            if i != shortKeys[int(slideID)][1] or altText != shortKeys[int(slideID)][2]:

                sqlValTupleSlide = (request.form.get('alt_text_' + str(i)), i,  slideID)      
                resultUpdate = sqlUpdate(sqlUpdateSlide, sqlValTupleSlide)
                if resultUpdate['status'] == '-1':
                    answer = gettext('Something went wrong. Please try again!')
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
            del shortKeys[int(slideID)]  

        # insert new image
        if request.form.get('upload_status_' + str(i)) == '0':
            file = request.files.get('file_' + str(i))
            unique_filename = fileUpload(file, imgDir)
            sqlValTuple = (unique_filename, altText, i, ptID, 2)
            result = sqlInsert(sqlInsertSlide, sqlValTuple)
            if result['status'] == 0:
                answer = gettext('Something went wrong. Please try again!')
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
                answer = gettext('Something went wrong. Please try again!')
                return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    # End of image upload

    # Sup product specifications
    sqlQueryPT = "SELECT `spsID` FROM `product_type` WHERE `ID` = %s;"
    sqlValTuplePT = (ptID,)
    resultPT = sqlSelect(sqlQueryPT, sqlValTuplePT, True)
    title = request.form.get('title')
    price = float(request.form.get('price'))
    if not request.form.get('spsID'):
        spsID = 0
    else:
        spsID = int(request.form.get('spsID'))


    sqlUpdatePriceTitle = "UPDATE `product_type` SET `title` = %s, `price` = %s, `spsID` = %s WHERE `ID` = %s;"
    sqlValTuple = (title, price, spsID, ptID)
    updateResult = sqlUpdate(sqlUpdatePriceTitle, sqlValTuple) 
    if updateResult['status'] == '-1':
        answer = gettext('Something went wrong. Please try again!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    
    spsChecker = request.form.get('spsChecker')
    if spsChecker == '1':
        sqlQueryDel = "DELETE FROM `product_type_details` WHERE `productTypeID` = %s;"
        sqlValTuple = (ptID,)
        resultDelete = sqlDelete(sqlQueryDel, sqlValTuple)
        if resultDelete['status'] == '-1':
            answer = gettext('Something went wrong. Please try again!')
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
                    answer = gettext('Something went wrong. Please try again!')
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
    supportedLangsData = supported_langs()
    toBeTranslated = {'length': 0}
    productCategoriesToBeTranslated = []
    slideShow = []

    if RefKey is None:
         errorMessage = True

    languageID = getLangID()
    if 'langID' in RefKey:
        languageID = RefKey.split('&langID=')[1]
        RefKey = RefKey.split('&langID=')[0]

    if len(getLangdatabyID(languageID)) == 0:
        return render_template('error.html')
    
    productCategory = get_product_categories(None, languageID)
    defLangProductCategory = {'length': 0}
    prData = ''
   
   
    if 'new' in RefKey.lower():      
        productTemplate = 'add_product.html'

        if len(RefKey) > 3:
            errorMessage = True
    else: 
        if RefKey.isdigit(): # Check if the variable is numeric
            prData = constructPrData(RefKey, '', languageID)

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
    
    return render_template(productTemplate, prData=prData, ordering=get_pr_order(), slideShow=slideShow, sideBar=sideBar, productCategory=productCategory, productCategoriesToBeTranslated=productCategoriesToBeTranslated, defLangProductCategory=defLangProductCategory, supportedLangsData=supportedLangsData, errorMessage=errorMessage, root_url=root_url, languageID=languageID, emptyCategory=emptyCategory, current_locale=get_locale()) # current_locale is babel variable for multilingual purposes


# Edit product'd thumbnail client-server transaction
@app.route('/upload_slides', methods=['POST'])
@login_required
def upload_slides():
    
    answer = gettext('Something went wrong. Please try again!')
    newCSRFtoken = generate_csrf()
    languageID = getLangID()
    
    if not request.form.get('ProductID') or not request.form.get('Type'):
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
    

    answer = gettext('Something went wrong. Please try again!') # Delete after function is completed


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

        if float(request.form.get('price')) <= 0:
            answer = gettext('The price should be higher then 0!')
            return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
        
        title = request.form.get('title')
        price = float(request.form.get('price'))
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
        sqlInsertVals = (price, title, order, int(ProductID), session['user_id'], spsID, 1)
        insertedResult = sqlInsert(sqlInsertQuery, sqlInsertVals)

        PT_Ref_Key = request.form.get('PT_Ref_Key', '')
        if PT_Ref_Key == '':
            sqlQueryHighestRK = "SELECT `PT_Ref_Key` FROM `product_type_relatives` ORDER BY `PT_Ref_Key` DESC LIMIT 1;"
            resultHighestRK = sqlSelect(sqlQueryHighestRK, (), True)    
            if resultHighestRK['length'] > 0:
                PT_Ref_Key = resultHighestRK['data'][0]['PT_Ref_Key'] + 1
            else:
                PT_Ref_Key = 0


        sqlQueryRefQey = "INSERT INTO `product_type_relatives` (`Language_ID`, `PT_ID`, `PT_REF_KEY`, `User_ID`) VALUES (%s, %s, %s, %s)"
        sqlValTupleRefKey = (languageID, insertedResult['inserted_id'], PT_Ref_Key, session['user_id'])
        resultRefKey = sqlInsert(sqlQueryRefQey, sqlValTupleRefKey)

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
                            answer = gettext('Something went wrong. Please try again!')
                            return jsonify({'status': '0', 'answer': resultInsertPTD['answer'], 'newCSRFtoken': newCSRFtoken})


        else: 
            answer = gettext('Something went wrong. Please try again!')
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
                        answer = gettext('Something went wrong. Please try again!')
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
                    answer = gettext('Something went wrong. Please try again!')
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
         

            
            
            i = i + 1    
            fileName = 'file_' + str(i)

        lenShortkeys = len(shortKeys)
        if lenShortkeys > 0 and productType == '1':
            sqlValList = []
            for key, val in shortKeys.items():
                sqlValList.append(key)
                
                # Del from folder
                removeResult = removeRedundantFiles(val[0], imgDir)
                if removeResult == False:
                    answer = gettext('Something went wrong. Please try again!')
                    return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 
            
            idCount = lenShortkeys * "%s, "
            idCount = idCount[:-2]
            sqlDeleteQuery = f"DELETE FROM `slider` WHERE `ID` IN ({idCount});" 
            sqlValTuple = tuple(sqlValList)
            delResult = sqlDelete(sqlDeleteQuery, sqlValTuple)
            if delResult['status'] == '-1':
                return jsonify({'status': '0', 'answer': delResult['answer'], 'newCSRFtoken': newCSRFtoken}) 
   
    answer = gettext('Done!')
    return jsonify({'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}) 


# Edit product'd thumbnail client-server transaction
@app.route('/edit_pr_thumbnail', methods=['POST'])
@login_required
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


# edit product headers client-server transaction
@app.route('/edit_product_headers', methods=['POST'])
@login_required
def edit_pr_headers():
    if not request.form.get('RefKey') or request.form.get('RefKey').isdigit() is not True or request.form.get('RefKey') == '0':
        answer = gettext('Something went wrong. Please try again!')
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


# Render the add_product_category.html template
@app.route('/add-product-category', methods=['GET'])
@login_required
def addPC():
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


# Render the edit_product_category.html template
@app.route('/edit-product-category/<RefKey>', methods=['GET'])
@login_required
def edit_product_category(RefKey):

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
    

    content = edit_p_c_view(RefKey)
    pcImages = get_product_category_images(RefKey) 
    languageID = getLangID()
    sideBar = side_bar_stuff()
    return render_template('edit_product_category.html', sideBar=sideBar, sps=result, content=content, pcImages=pcImages, languageID=languageID, RefKey=RefKey, current_locale=get_locale())


# edit_product_category client-server transaction
@app.route('/edit_product_category', methods=['POST'])
@login_required
def edit_p_c():
    newCSRFtoken = generate_csrf()
        
    spsID = 0
    if request.form.get('spsID'):
        spsID = int(request.form.get('spsID'))

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
        sqlQueryVal = (altText, categoryName, categoryStatus, spsID, productCategoryID)
    if state['status'] == 1:
        # Get Image name
        if getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID):
            imageName = getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID)

            if checkForRedundantFiles(imageName, 'Product_Category_Images', 'product_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')

        sqlQueryVal = (state['file'], altText, categoryName, categoryStatus, spsID, productCategoryID)
    if state['status'] == 2:    
        # Get Image name
        if getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID):
            imageName = getFileName('Product_Category_Images', 'product_category', 'Product_Category_ID', productCategoryID)
    
            if checkForRedundantFiles(imageName, 'Product_Category_Images', 'product_category'):
                removeRedundantFiles(imageName, 'images/pc_uploads')
            
        file = request.files.get('file')

        unique_filename = fileUpload(file, 'images/pc_uploads')
        sqlQueryVal = (unique_filename, altText, categoryName, categoryStatus, spsID, productCategoryID)
    
    # Stegh es !!!
    sqlQuery   = f"""   
                    UPDATE `product_category`
                    SET 
                        {sqlImage}                       
                        `AltText` = %s,
                        `Product_Category_Name` = %s,
                        `Product_Category_Status` = %s,
                        `spsID` = %s
                    WHERE `Product_Category_ID` = %s;
                 """

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result


# Publish/Unpublish product
@app.route('/publish-product', methods=['POST'])
@login_required
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


# Product categories view
@app.route('/product-categories', methods=['GET'])
@login_required
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
                LIMIT 0, {int(PAGINATION)}
                ; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    numRows = totalNumRows('stuff')
    sideBar = side_bar_stuff()

    return render_template('team.html', result=result, sideBar=sideBar, numRows=numRows, page=1,  pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), current_locale=get_locale())


@app.route('/affiliates', methods=['GET'])
# @login_required
def affiliates():
    
    where = "WHERE `rol`.`Rol` = 'Affiliate'"
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
                {where} 
                LIMIT 0, {int(PAGINATION)}
                ; 
               """
    sqlValTuple = ()
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    numRows = totalNumRows('payment_details', where, sqlValTuple)
    # numRows = totalNumRows('stuff')
    sideBar = side_bar_stuff()

    return render_template('affiliates.html', result=result, sideBar=sideBar, numRows=numRows, page=1,  pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), current_locale=get_locale())



@app.route('/team/<page>', methods=['Get'])
@login_required
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
@login_required
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
            answer = gettext('Please specify the last name')
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


@app.route('/stuff', methods=['GET'])
@login_required
def stuff():

    stuffID = session['user_id']
    

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
    
    if result['length'] == 0:
        return render_template('error.html', current_locale=get_locale())

        
    supportedLangsData = supported_langs()
    view = 'admin_panel.html'
    resultP, resultRevardsList = ['', '']
    if result['data'][0]['Rol'] == 'Affiliate':
        sqlQueryPromo = f"""
                    SELECT 
                        `promo_code`.`Promo`,
                        `promo_code`.`expDate`,
                        `promo_code`.`Status`
                    FROM `promo_code`
                        
                    WHERE `promo_code`.`affiliateID` = %s;    
                    """

        sqlValTuplePromo = (stuffID,)
        resultP = sqlSelect(sqlQueryPromo, sqlValTuplePromo, True)
        
        view = 'affiliate.html'
        resultRevards = get_affiliate_reward_progress(stuffID)

        row = {}
        if resultRevards['length'] > 0:
            row = resultRevards['data'][0]
    
        resultRevardsList = {
            '0': [gettext('Voided'),    row.get('Voided') or 0, 'Voided', 'affiliate-orders/page=1&status=0'],
            '1': [gettext('Pending'),   row.get('Pending') or 0, 'Pending', 'affiliate-orders/page=1&status=pending'],
            '2': [gettext('Approved'),  row.get('Approved') or 0, 'Approved', 'affiliate-orders/page=1&status=5'],
            '3': [gettext('Settled'),   row.get('Settled') or 0, 'Settled', 'affiliate-transfers/page=1']
        }

    return render_template(view, result=result, resultP=resultP, resultRevardsList=json.dumps(resultRevardsList), supportedLangsData=supportedLangsData, currentDate=date.today(), current_locale=get_locale())


@app.route('/affiliate/<affID>', methods=['GET'])
# @login_required
def affiliate(affID):
    supportedLangsData = supported_langs()
    
    sqlQuery = f"""
                SELECT
                    `stuff`.`Firstname`,
                    `stuff`.`Lastname`,
                    `promo_code`.`Promo`,
                    `promo_code`.`expDate`,
                    `promo_code`.`Status`
                FROM `promo_code`
                    LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`                    
                WHERE `promo_code`.`affiliateID` = %s;    
                """

    sqlValTuple = (affID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    print(result['data'])
    print(result['error'])

    if result['length'] == 0:
        return render_template('error.html')
    
    resultRevards = get_affiliate_reward_progress(affID)

    row = {}
    if resultRevards['length'] > 0:
        row = resultRevards['data'][0]

    resultRevardsList = {
        '0': [gettext('Voided'), row.get('Voided') or 0, 'Voided', 'stuff-affiliate-orders/page=1&status=0&affiliate='+affID],
        '1': [gettext('Pending'), row.get('Pending') or 0, 'Pending', 'stuff-affiliate-orders/page=1&status=pending&affiliate='+affID],
        '2': [gettext('Approved'), row.get('Approved') or 0, 'Approved', 'stuff-affiliate-orders/page=1&status=5&affiliate='+affID],
        '3': [gettext('Settled'), row.get('Settled') or 0, 'Settled', 'transfers/page=1&affiliate=' + affID]
    }

    sideBar = side_bar_stuff()
    return render_template('affiliate.html', resultP=result, result=result, stuff=True, affID=affID, resultRevardsList=json.dumps(resultRevardsList), sideBar=sideBar, supportedLangsData=supportedLangsData, currentDate=date.today(), current_locale=get_locale())


@app.route('/promo-code-details/<promo>', methods=['GET'])
# @login_required
def promo_code_details(promo):
    sqlQuery = """
        SELECT 
            `promo_code`.`Promo`,
            `promo_code`.`affiliateID`,
            DATE_FORMAT(`promo_code`.`expDate`, '%m-%d-%Y') AS `expDate`, 
            `promo_code`.`Status`,
            `product`.`ID` AS `prID`,
            `product_type`.`ID` AS `ptID`,
            `product`.`Title` AS `prTitle`,
            `product_type`.`Title` AS `ptTitle`,
            `discount`.`ID` AS `discountID`,
            `discount`.`discount`,
            `discount`.`discount_status`,
            `discount`.`revard_value`,
            `discount`.`revard_type`,
            CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `affiliate` 
        FROM `promo_code` 
            LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID`
            LEFT JOIN `product_type` ON `product_type`.`ID` = `discount`.`ptID`
            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
            LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`
        WHERE `promo_code`.`Promo` = %s AND `promo_code`.`affiliateID` = %s
        ORDER BY `product`.`Order` ASC, `product_type`.`Order` ASC;
    """

    userID = session.get('user_id')
    result = sqlSelect(sqlQuery, (promo, userID), True)

    if result['length'] == 0:
        return render_template('error.html', current_locale=get_locale())
    
    discounts = json.dumps(result['data']) 
    headings = [result['data'][0]['affiliate'], result['data'][0]['Promo']]

    sideBar = side_bar_stuff()

    return render_template('promo-code-details.html', discounts=discounts, headings=headings, mainCurrency=MAIN_CURRENCY,  sideBar=sideBar, current_locale=get_locale()) 


@app.route('/stuff-promo-code-details/<filters>', methods=['GET'])
# @login_required
def stuff_promo_code_details(filters):

    promo, affID = (item.split('=')[1] for item in filters.split('&'))

    sqlQuery = """
        SELECT 
            `promo_code`.`Promo`,
            `promo_code`.`affiliateID`,
            DATE_FORMAT(`promo_code`.`expDate`, '%m-%d-%Y') AS `expDate`, 
            `promo_code`.`Status`,
            `product`.`ID` AS `prID`,
            `product_type`.`ID` AS `ptID`,
            `product`.`Title` AS `prTitle`,
            `product_type`.`Title` AS `ptTitle`,
            `discount`.`ID` AS `discountID`,
            `discount`.`discount`,
            `discount`.`discount_status`,
            `discount`.`revard_value`,
            `discount`.`revard_type`,
            CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `affiliate`
        FROM `promo_code` 
            LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID`
            LEFT JOIN `product_type` ON `product_type`.`ID` = `discount`.`ptID`
            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
            LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`
        WHERE `promo_code`.`Promo` = %s AND `promo_code`.`affiliateID` = %s
        ORDER BY `product`.`Order` ASC, `product_type`.`Order` ASC;
    """
    result = sqlSelect(sqlQuery, (promo, affID), True)

    if result['length'] == 0:
        return render_template('error.html', current_locale=get_locale())
    
    discounts = json.dumps(result['data']) 
    headings = [result['data'][0]['affiliate'], result['data'][0]['Promo'], str(result['data'][0]['affiliateID'])]


    sideBar = side_bar_stuff()

    return render_template('promo-code-details.html', discounts=discounts, headings=headings, mainCurrency=MAIN_CURRENCY,  sideBar=sideBar, current_locale=get_locale()) 


@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    languageID = getLangID()
    DefLangID = getDefLang()['id']
    newCSRFtoken = generate_csrf()
    
    if request.method == 'POST':
        if request.form.get('shTP') == '1':
            sqlQuery =  """SELECT 
                        `product`.`ID`,
                        `product`.`Thumbnail`,
                        `product`.`DatePublished`,
                        `product`.`Product_Status`,
                        `product_relatives`.`P_Ref_Key`,
                        `product`.`Title`,
                        `product`.`DateModified`,
                        `product_category`.`Product_Category_Name`,
                        `product`.`Url`
                    FROM `product` 
                        LEFT JOIN `product_relatives` ON  `product_relatives`.`P_ID` = `product`.`ID`
                        LEFT JOIN `product_category` ON `product_category`.`Product_Category_ID` = `product`.`Product_Category_ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                        AND not find_in_set(`product_relatives`.`P_Ref_Key`, (SELECT GROUP_CONCAT(`product_relatives`.`P_Ref_Key`) FROM `product_relatives` WHERE `product_relatives`.`Language_ID` = %s))
                    ORDER BY `product`.`Order` ASC                 
                    """
             
            sqlValTuple = (DefLangID, languageID)
            resultFilters = sqlSelect(sqlQuery, sqlValTuple, True)
            return jsonify({'status': '1', 'prData': resultFilters, 'newCSRFtoken': newCSRFtoken})

    else:        
        sqlQuery =  """SELECT 
                        `product`.`ID`,
                        `product`.`Thumbnail`,
                        `product`.`DatePublished`,
                        `product`.`Product_Status`,
                        `product_relatives`.`P_Ref_Key`,
                        `product`.`Title`,
                        `product`.`DateModified`,
                        `product_category`.`Product_Category_Name`,
                        `product`.`Url`
                    FROM `product` 
                        LEFT JOIN `product_relatives` ON  `product_relatives`.`P_ID` = `product`.`ID`
                        LEFT JOIN `product_category` ON `product_category`.`Product_Category_ID` = `product`.`Product_Category_ID`
                    WHERE `product_relatives`.`Language_ID` = %s
                    ORDER BY `product`.`Order` ASC                 
                    """
        sqlValTuple = (languageID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        sideBar = side_bar_stuff()
        
        if DefLangID == languageID:
            translated = False
        else:
            translated = True

        return render_template('products.html', result=result, mainCurrency=MAIN_CURRENCY, translated=translated, languageID=languageID, DefLangID=DefLangID, sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale()) 


@app.route('/store', methods=['GET', 'POST'])
@login_required
def store():    
    newCSRFtoken = generate_csrf()
    if request.method == 'GET':
        languageID = getLangID()
        # Main query that gets all active products in all stores [ WHERE `quantity`.`Status` = 1]
        sqlQuery =  f"""
                        SELECT 
                            `product`.`ID`,
                            `product`.`Title` AS `prTitle`,
                            `product`.`Thumbnail`,
                            SUM(`quantity`.`Quantity`) AS `TotalQuantity`,
                            (SELECT 
                                SUM(`quantity`.`Quantity`)
                                FROM `Quantity`
                                    LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                                    LEFT JOIN `product` p ON `product_type`.`Product_ID` = `p`.`ID`
                                WHERE `Quantity`.`expDate` < CURRENT_DATE() AND `p`.`ID` = `product`.`ID`) 
                            AS `expired`
                        FROM `quantity`
                            LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                        WHERE `quantity`.`Status` = 1
                        GROUP BY `product`.`ID`, `product`.`Title`, `product`.`Thumbnail`
                        ORDER BY `product`.`Order` ASC  
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
        return render_template('store.html', result=result, storeData=storeData, productsData=productsData, mainCurrency=MAIN_CURRENCY,  sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale()) 
    else:
        
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
                            SUM(`quantity`.`Quantity`) AS `TotalQuantity`,
                            (SELECT 
                                SUM(`quantity`.`Quantity`)
                                FROM `Quantity`
                                    LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                                    LEFT JOIN `product` p ON `product_type`.`Product_ID` = `p`.`ID`
                                WHERE `Quantity`.`expDate` < CURRENT_DATE() AND `p`.`ID` = `product`.`ID`) 
                            AS `expired`
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


@app.route("/pt-specifications", methods=['GET', 'POST'])
@login_required
def pt_specifications():
    newCSRFtoken = generate_csrf()
    languageID = getLangID()
    if request.method == 'GET':
        sqlQuery = """
                    SELECT 
                        `sub_product_specification`.`ID`,
                        `sps_relatives`.`Ref_Key`,
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
        translated = False
        if getDefLang()['id'] != languageID:
            translated = True
        return render_template('product-type-specifications.html', result=result, sideBar=sideBar, translated=translated, numRows=numRows, page=1,  pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    else:
        if request.form.get('shTP') == '1':
            sqlQuery = """
                        SELECT 
                            `sub_product_specification`.`ID`,
                            `sps_relatives`.`Ref_Key`,
                            `sub_product_specification`.`Name`,
                            `sub_product_specification`.`Status`
                        FROM `sub_product_specification`
                        LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID` 
                        WHERE `sps_relatives`.`Language_ID` = %s
                            AND not find_in_set(`sps_relatives`.`Ref_Key`, (SELECT GROUP_CONCAT(`sps_relatives`.`Ref_Key`) FROM `sps_relatives` WHERE `sps_relatives`.`Language_ID` = %s));

                        """
            sqlValTuple = (getDefLang()['id'], languageID)
            result = sqlSelect(sqlQuery, sqlValTuple, True)

            return jsonify({'status': '1', 'data': result, 'newCSRFtoken': newCSRFtoken})
        else:
            return jsonify({'status': '0', 'newCSRFtoken': newCSRFtoken})

# Edit product type specification (subproduct)
@app.route("/edit-pts/<ptsRefKey>", methods=['GET'])
@login_required
def edit_pts_view(ptsRefKey):
    languageID = getLangID()

    # Get ptsID
    sqlQueryPTS = "SELECT `SPS_ID` FROM `sps_relatives` WHERE `Ref_Key` = %s AND `Language_ID` = %s;"
    resultPTS = sqlSelect(sqlQueryPTS, (ptsRefKey, languageID), True)
    if resultPTS['length'] == 0:
        if getDefLang()['id'] == getLangdata(session['lang'])['ID']:
            return render_template('error.html', current_locale=get_locale())
        else:    
            redirectUrl = url_for('add_sps_view', spsRefKey=ptsRefKey)
            return redirect(redirectUrl)

    
    ptsID = resultPTS['data'][0]['SPS_ID']
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
@login_required
def change_type_order():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext('Something went wrong. Please try again!')
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
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)

    i = 0
    sqlQuery = "UPDATE `product_type` SET `Order` = %s WHERE `ID` = %s;"
    while True:
        if not request.form.get(str(i)):
            break
        if result['data'][i]['ID'] != int(request.form.get(str(i))):
            sqlValTuple = (i, request.form.get(str(i)))
            updateResult = sqlUpdate(sqlQuery, sqlValTuple)
            if updateResult['status'] == '-1':
                answer = gettext('Something went wrong. Please try again!')
                response = {'status': '0', 'answer': updateResult['answer'], 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)   
             
        i += 1


    answer = gettext('Order Changed Successfully!')
    response = {'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)
    

@app.route("/chaneg-pt-status", methods=['POST'])
@login_required
def chaneg_pt_status():
    newCSRFtoken = generate_csrf()
    ptID = request.form.get('ptID') 
    status = request.form.get('status') 
    if not ptID or not status:
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    sqlQuery = "UPDATE `product_type` SET `status` = %s WHERE `ID` = %s;"
    sqlValTuple = (status, ptID)
    result = sqlUpdate(sqlQuery, sqlValTuple)

    if result['status'] == '-1':
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    answer = gettext('Status changed successfully!')
    response = {'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/edit-pts", methods=['POST'])
@login_required
def edit_pts():
    newCSRFtoken = generate_csrf()
    spsName = request.form.get('spsName') 
    if not spsName:
        answer = gettext('Please specify subproduct situation name!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    spsID = request.form.get('spsID') 
    if not spsID:
        answer = gettext('Something went wrong. Please try again!')
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
            answer = gettext('Something went wrong. Please try again!')
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
        
        if len(result['data']) > i:
            if spsText != result['data'][i]['Text']:
                sqlValTuple = (spsText, result['data'][i]['spssID'])
                updateResult = sqlUpdate(sqlQuerySpssUpdate, sqlValTuple)
                if updateResult['status'] == '-1':
                    answer = gettext('Something went wrong. Please try again!')
                    response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                    return jsonify(response)
        else:
            sqlValTuple = (spsText, i, spsID, 1)
            resultInsert = sqlInsert(sqlQuerySpssInsert, sqlValTuple)
            if resultInsert['status'] == 0:
                answer = gettext('Something went wrong. Please try again!')
                response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)

            spssID = resultInsert['inserted_id']

            sqlValTupleSPSRel = (spssID, RefKey, languageID, userID, 1)
            insertResult = sqlInsert(sqlQuerySPSSRelativeInsert, sqlValTupleSPSRel)
            if insertResult['status'] == 0:
                answer = gettext('Something went wrong. Please try again!')
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
                answer = gettext('Something went wrong. Please try again!')
                response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
                return jsonify(response)
            
    response = {'status': '1', 'answer': gettext('Done!'), 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


    


@app.route("/add-sps/<spsRefKey>", methods=['GET'])
@app.route("/add-sps", methods=['GET'])
@login_required
def add_sps_view(spsRefKey=None):
    data = []
    num=1
    if spsRefKey is not None and getDefLang()['id'] != getLangdata(session['lang'])['ID']:
        if not spsRefKey.isdigit():
            return render_template('error.html')
        
        sqlQuery =  """
                    SELECT 
                        `sub_product_specification`.`ID` AS `spsID`,
                        `sub_product_specification`.`Name` AS `spsName`,
                        `sub_product_specifications`.`ID` AS `spssID`,
                        `sub_product_specifications`.`Name` AS `spssName`
                    FROM `sub_product_specification`
                        LEFT JOIN `sps_relatives` ON `sps_relatives`.`SPS_ID` = `sub_product_specification`.`ID`
                        LEFT JOIN `sub_product_specifications` ON `sub_product_specifications`.`spsID` = `sub_product_specification`.`ID`
                    WHERE `sps_relatives`.`Ref_Key` = %s
                        AND `sps_relatives`.`Language_ID` = %s
                    ORDER BY `sub_product_specifications`.`Order`;
                    """
        sqlValTuple = (spsRefKey, getDefLang()['id'])
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        if result['length'] == 0:
            return render_template('error.html')
        
        data = result['data']
        num = result['length']

    sideBar = side_bar_stuff()
    return render_template('sp-specifications.html', spsRefKey=spsRefKey, data=data, num=num, sideBar=sideBar, current_locale=get_locale())


@app.route("/transfers/<filters>", methods=['GET'])
# @login_required
def transfers(filters):
    if request.method == "GET":
        newCSRFtoken = generate_csrf()

        page = filters
        affiliateID, where = ['', '']
        sqlValTuple = ()

        if '&' in filters:
            page = filters.split('&')[0]
            affStr = filters.split('&')[1]
            affiliateID = affStr.split('=')[1]

            if not affiliateID.isdigit():
                return render_template('error.html', current_locale=get_locale())
            
            affiliateID = int(affiliateID)
            where = "WHERE `partner_payments`.`affiliateID` = %s"
            sqlValTuple = (affiliateID,)


        if not page or not '=' in page:
            return render_template('error.html', current_locale=get_locale())
        page = page.split('=')[1]

        if not page.isdigit():
            return render_template('error.html', current_locale=get_locale())

        rowsToSelect = (int(page) - 1) * int(PAGINATION)

             
        sqlQuery =  f"""SELECT 
                        `partner_payments`.`ID` AS `transactionID`,    
                        `partner_payments`.`amount`,
                        `partner_payments`.`type`,
                        `partner_payments`.`timestamp`,
                        `notes`.`ID` AS `notesID`,
                        `notes`.`note`,
                        CONCAT(`stuff`.`Firstname`, ' ', `stuff`.`Lastname`) AS `Initials`,
                        `rol`.`Rol`
                    FROM `partner_payments`
                        LEFT JOIN `notes` ON `notes`.`refID` = `partner_payments`.`ID`
                        LEFT JOIN `stuff` ON `stuff`.`ID` = `partner_payments`.`affiliateID`
                        LEFT JOIN `rol` ON `rol`.`ID` = `stuff`.`rolID`
                    {where}
                    ORDER BY `partner_payments`.`ID` DESC
                    LIMIT {rowsToSelect}, {int(PAGINATION)};
                    """
        
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        # if result['length'] == 0:
        #     return render_template('error.html', current_locale=get_locale())
        
        # resultAff = get_affiliates('AND `rol`.`ID` = 2')
        resultAff = get_affiliates()
        
        numRows = totalNumRows('partner_payments', where, sqlValTuple)
        

        sideBar = side_bar_stuff()
        return render_template('transfers.html', result=result, resultAff=resultAff, affID=affiliateID, sideBar=sideBar, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), newCSRFtoken=newCSRFtoken, current_locale=get_locale())


@app.route("/affiliate-transfers/<page>", methods=['GET'])
# @login_required
def affiliate_transfers(page):
    if request.method == "GET":
        newCSRFtoken = generate_csrf()

        if not page or not '=' in page:
            return render_template('error.html', current_locale=get_locale())
        page = page.split('=')[1]

        if not page.isdigit():
            return render_template('error.html', current_locale=get_locale())

        rowsToSelect = (int(page) - 1) * int(PAGINATION)
        where = "WHERE `partner_payments`.`affiliateID` = %s"

             
        sqlQuery =  f"""SELECT 
                        `partner_payments`.`ID` AS `transactionID`,    
                        `partner_payments`.`amount`,
                        `partner_payments`.`type`,
                        `partner_payments`.`timestamp`,
                        `notes`.`ID` AS `notesID`,
                        `notes`.`note`
                    FROM `partner_payments`
                        LEFT JOIN `notes` ON `notes`.`refID` = `partner_payments`.`ID`
                    {where}
                    LIMIT {rowsToSelect}, {int(PAGINATION)};
                    """
        
        sqlValTuple = (session['user_id'],)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        if result['length'] == 0:
            return render_template('error.html', current_locale=get_locale())
        
        numRows = totalNumRows('partner_payments', where, sqlValTuple)
        

        sideBar = side_bar_stuff()
        return render_template('affiliate-transfers.html', result=result, sideBar=sideBar, numRows=numRows, page=int(page), pagination=int(PAGINATION), pbc=int(PAGINATION_BUTTONS_COUNT), newCSRFtoken=newCSRFtoken, current_locale=get_locale())



@app.route("/transfer-funds/<stuffID>", methods=['GET', 'POST'])
@app.route("/transfer-funds", methods=['GET', 'POST'])
# @login_required
def transfer_funds(stuffID=0):
    newCSRFtoken = generate_csrf()
    if request.method == "GET":

        result = get_affiliates()
        sideBar = side_bar_stuff()
        return render_template('transfer-funds.html', result=result, stuffID=int(stuffID), sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    else:
        invalid = False
        if not request.form.get('recipient') or not request.form.get('amount') or not request.form.get('type'):
            invalid = True

        amount = request.form.get('amount')
        num = amount.count(',') + amount.count('.')

        if num > 1 or invalid == True or bool(re.match(r'^[0-9.,]+$', amount)) == False:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}) 

        recipient = request.form.get('recipient')
        sqlQuery =  "SELECT `ID` FROM `stuff` WHERE `ID` = %s;"
        result = sqlSelect(sqlQuery, (recipient,), True)
        if result['length'] == 0:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}) 

        type = request.form.get('type')

        sqlQuery = """INSERT INTO `partner_payments` (`affiliateID`, `type`, `amount`, `timestamp`) VALUES (%s, %s, %s, NOW())"""
        sqlValTuple = (recipient, type, amount)
        result = sqlInsert(sqlQuery, sqlValTuple)
        insertedID = result['inserted_id']
        if insertedID is None:
            return jsonify({'status': "0", 'answer': result['answer'], 'newCSRFtoken': newCSRFtoken}) 

        # print('Content After', content)
        content = request.form.get('content', '').strip()
        if content != '<p><br></p>':
            print('Content Before', content)
            # submit_product_text(content, insertedID)
            
            submit_notes_text(content, type, insertedID, 3)

        return jsonify({'status': "1", 'answer': 'Cool!', 'newCSRFtoken': newCSRFtoken})

# Subproduct situation and situations adding function
@app.route("/add_sps", methods=['POST'])
@login_required
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

    if request.form.get('spsRefKey', '') != '':
        spsRefKey = request.form.get('spsRefKey')
        # Check weather sps RefKey exists in current language
        # Return if exists
        sqlQueryCheckspsRefKey = "SELECT `ID` FROM `sps_relatives` WHERE `Ref_Key` = %s AND `Language_ID` = %s;"
        sqlValTuplespsRefKey = (spsRefKey, languageID)
        resultspsRefKey = sqlSelect(sqlQueryCheckspsRefKey, sqlValTuplespsRefKey, True)
        if resultspsRefKey['length'] > 0:
            answer = gettext('The current subproduct situation has already been translated!')
            response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
            return jsonify(response) 
        
    sqlQuery = "INSERT INTO `sub_product_specification` (`Name`, `User_ID`, `Status`) VALUES (%s, %s, %s)"
    sqlValTuple = (spsName, userID, 1)
    result = sqlInsert(sqlQuery, sqlValTuple)

    if not result['inserted_id']:
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response) 

    # Get refkey of sub product specification
    if request.form.get('spsRefKey', '') != '':
        spsRefKey = request.form.get('spsRefKey')
    else :            
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
    
    # Get refkey of sub product specificationS
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


# def table(structure):

#     structure = {
#         'rows': [], # [{}, {}, {}, ... ]
#         'header': [], # ['ID', 'Name', 'Status', ... ]
#         'buttons': [], # ['url', 'name']
#         'pagination': [] # True, False
#     }
    
#     return render_template('table.html', structure=structure, current_locale=get_locale())


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

    return render_template('slideshow.html', result=result, resultSubPr=resultSubPr, resultSpss=resultSpss, subProducts=subProducts, Title = resultTitle['data'][0]['Title'], mainCurrency=MAIN_CURRENCY, current_locale=get_locale())


@app.route("/get-spacifications", methods=["POST"])
@login_required
def get_specifications():
    newCSRFtoken = generate_csrf()
    if not request.form.get('LanguageID') or not request.form.get('spsID'):
        answer = gettext('Something went wrong. Please try again!')
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
@login_required
def get_product_types():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    prID = request.form.get('prID')
    dataType = True
    if request.form.get('type'):
        dataType = False
    
    originalData = ''
    if request.form.get('untranslated') == '1':
        # Get products in Original language 
        
        sqlQueryOriginalPR = """
                SELECT  `product_type_relatives`.`PT_Ref_Key`,    
                        `product_type`.`ID`,
                        `product_type`.`Title`,
                        `product_type`.`Price`,
                        `product_type`.`Order` AS `SubPrOrder`,
                        (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                        (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                        `product_type`.`Status`
                FROM `product_type`
                    LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_ID` = `product_type`.`ID`
                WHERE `product_type`.`Product_ID` = (SELECT `P_ID` FROM `product_relatives` 
                            WHERE `product_relatives`.`P_Ref_Key` = (SELECT `P_Ref_Key` FROM `product_relatives` WHERE `product_relatives`.`P_ID` = %s) 
                                AND `product_relatives`.`Language_ID` = %s) 
                    AND not find_in_set(`product_type_relatives`.`PT_Ref_Key`, (SELECT GROUP_CONCAT(`product_Type_relatives`.`PT_Ref_Key`) FROM `product_type_relatives` WHERE `product_type_relatives`.`Language_ID` = %s))
                ORDER BY `SubPrOrder` 
                ;"""
        sqlValTupleOriginalPR = (prID, getDefLang()['id'], getLangID())
        resultOriginalPR = sqlSelect(sqlQueryOriginalPR, sqlValTupleOriginalPR, dataType)

        if resultOriginalPR['length'] > 0:    
            originalData = resultOriginalPR['data']
            if dataType == False:
                originalData = json.dumps(resultOriginalPR['data'])

    sqlQuery = """
                    SELECT  `product_type_relatives`.`PT_Ref_Key`,    
                            `product_type`.`ID`,
                            `product_type`.`Title`,
                            `product_type`.`Price`,
                            `product_type`.`Order` AS `SubPrOrder`,
                            (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                            (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                            `product_type`.`Status`
                    FROM `product_type`
                        LEFT JOIN `product_type_relatives` ON `product_type_relatives`.`PT_ID` = `product_type`.`ID`
                    WHERE `product_type`.`Product_ID` = %s 
                    ORDER BY `SubPrOrder` 
                    ;"""
    sqlValTuple = (prID,)
    result = sqlSelect(sqlQuery, sqlValTuple, dataType)

    productTypeData = result['data']
    if dataType == False:
        productTypeData = json.dumps(result['data'])

    response = {'status': '1', 'data': productTypeData, 'originalData': originalData, 'length': result['length'], 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/get-product-types-quantity", methods=["POST"])
@login_required
def get_product_types_quantity():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        answer = gettext('Something went wrong. Please try again!')
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
                            (SELECT SUM(`q`.`Quantity`) FROM `Quantity` as q
                                WHERE `q`.`expDate` < CURRENT_DATE() AND `q`.`productTypeID` = `quantity`.`productTypeID`
                            ) AS `expired`,
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
        cartData = productTypesQuantity

        content = analyse_cart_data(cartData)
        result = content['result']
        ptIdQuantity = content['ptIdQuantity']
        cartMessage = content['cartMessage']

        return render_template('cart.html', result=result, ptIdQuantity=ptIdQuantity, MAIN_CURRENCY=MAIN_CURRENCY, cartMessage=cartMessage, current_locale=get_locale())

    else:
        if request.form.get('cart-data'):
            cartData = request.form.get('cart-data')
            content = analyse_cart_data(cartData)

            return jsonify({'content': content, 'status': "1", 'newCSRFtoken': generate_csrf()})


def analyse_cart_data(cartData):    
    languageID = getLangID() 
    result = {'length': 0}
    findInSetPtIDs = ''
    ptIdQuantity = []
    if cartData is not None:
        if '&' in cartData:
            array = cartData.split('&')
            for val in array:
                arr = val.split('-')
                ptID = arr[0]
                clientQuantity = arr[1]

                findInSetPtIDs = findInSetPtIDs + ptID + ','    
                ptIdQuantity.append([int(ptID), int(clientQuantity)])
            findInSetPtIDs = findInSetPtIDs[0:-1]
        elif '-' in cartData:
            array = cartData.split('-')
            findInSetPtIDs = array[0]
            ptIdQuantity.append([int(array[0]), int(array[1])])

    sqlQuery =  f"""
                    SELECT 
                        `product`.`Title` AS `prTitle`,
                        `product`.`url`,
                        `product_type`.`Title` AS `ptTitle`,
                        `product_type`.`Price`,
                        (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                        (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                        (SELECT SUM(`Quantity`) FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE()) AS `quantity`,
                        (SELECT `maxQuantity` FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE() ORDER BY `maxQuantity` DESC LIMIT 1) AS `maxAllowdQuantity`,
                        `product_type`.`ID` AS `ptID`        
                    FROM `product_type`
                        LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                    WHERE `product`.`Language_ID` = %s 
                        AND find_in_set(`product_type`.`ID`, %s)
                        AND (SELECT SUM(`Quantity`) FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE()) > 0
                    ORDER BY `product`.`ID`, `product_type`.`Order`; 
                """
    
    sqlValTuple = (languageID, findInSetPtIDs)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    cartMessage = [ 
                gettext("You have already added this product to the basket. You can change the quantity if You would like to."),
                generate_csrf(),
                gettext("In Basket"),
                gettext("The seller doesn't have that many left."),
    ]

    content = {
        'result': result,
        'ptIdQuantity': ptIdQuantity,
        'cartMessage': cartMessage
    }

    return content



# @app.route("/cart/<productTypesQuantity>", methods=["GET", "POST"])
# @app.route("/cart", methods=["GET", "POST"])
# def cart(productTypesQuantity=None):
#     languageID = getLangID() 
#     if request.method == "GET":
#         result = {'length': 0}
#         findInSetPtIDs = ''
#         ptIdQuantity = []
#         if productTypesQuantity is not None:
#             if '&' in productTypesQuantity:
#                 array = productTypesQuantity.split('&')
#                 for val in array:
#                     arr = val.split('-')
#                     ptID = arr[0]
#                     clientQuantity = arr[1]

#                     findInSetPtIDs = findInSetPtIDs + ptID + ','    
#                     ptIdQuantity.append([int(ptID), int(clientQuantity)])
#                 findInSetPtIDs = findInSetPtIDs[0:-1]
#             elif '-' in productTypesQuantity:
#                 array = productTypesQuantity.split('-')
#                 findInSetPtIDs = array[0]
#                 ptIdQuantity.append([int(array[0]), int(array[1])])

#         sqlQuery =  f"""
#                         SELECT 
#                             `product`.`Title` AS `prTitle`,
#                             `product`.`url`,
#                             `product_type`.`Title` AS `ptTitle`,
#                             `product_type`.`Price`,
#                             (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
#                             (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
#                             (SELECT SUM(`Quantity`) FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE()) AS `quantity`,
#                             (SELECT `maxQuantity` FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE() ORDER BY `maxQuantity` DESC LIMIT 1) AS `maxAllowdQuantity`,
#                             `product_type`.`ID` AS `ptID`        
#                         FROM `product_type`
#                             LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
#                         WHERE `product`.`Language_ID` = %s AND find_in_set(`product_type`.`ID`, %s)
#                         ORDER BY `product`.`ID`, `product_type`.`Order`; 
#                     """
        
#         sqlValTuple = (languageID, findInSetPtIDs)
#         result = sqlSelect(sqlQuery, sqlValTuple, True)
#         cartMessage = [ 
#                     gettext("You have already added this product to the basket. You can change the quantity if You would like to."),
#                     generate_csrf(),
#                     gettext("In Basket")
#     ]
#         return render_template('cart.html', result=result, ptIdQuantity=ptIdQuantity, MAIN_CURRENCY=MAIN_CURRENCY, cartMessage=cartMessage, current_locale=get_locale())
#     else:
#         pass


@app.route("/get-pt-quantities", methods=["POST"])
def get_pt_quantities():     
    newCSRFtoken = generate_csrf()
    if not request.form.get('ptID'):
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
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
                    `product_type`.`Price`,
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
                WHERE `quantity`.`productTypeID` = %s 
                    AND `quantity`.`Quantity` > 0
                    AND `quantity`.`Status` = '1' {filters}
                ;
            """
    
    result = sqlSelect(sqlQuary, sqlValTuple, True)
    # ptQuantityData = json.dumps(result['data'])
    ptQuantityData = result['data']

    response = {'status': '1', 'data': ptQuantityData, 'length': result['length'], 'answer': result['error'], 'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/get-pt-quantity", methods=["POST"])
def get_pt_quantity():     
    newCSRFtoken = generate_csrf()
    if not request.form.get('ptID') or not request.form.get('quantity'):
        answer = gettext('Something went wrong. Please try again!')
        response = {'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken}
        return jsonify(response)
    
    ptID = request.form.get('ptID')
    quantity = float(request.form.get('quantity'))

    
    sqlValTuple = (ptID,)
    sqlQuary = f"""
                SELECT 
                    SUM(`quantity`.`Quantity`) AS `quantity`,
                    `product_type`.`Price`,
                    MAX(`quantity`.`maxQuantity`) AS `maxQuantity`
                FROM `quantity` 
                    LEFT JOIN `product_type` ON `product_type`.`ID` = `quantity`.`productTypeID`
                WHERE `quantity`.`productTypeID` = %s AND `quantity`.`Status` = '1' AND `quantity`.`expDate` > CURDATE() 
                ;
            """
    
    result = sqlSelect(sqlQuary, sqlValTuple, True)
    status, message = [0, '']

    if result['data'][0]['maxQuantity'] is not None:
        maxQuantity = result['data'][0]['maxQuantity']
        if float(maxQuantity) >= quantity:
            if float(result['data'][0]['quantity']) >= quantity:
                status = 1
                result['price'] = quantity * float(result['data'][0]['Price'])
        else:
            message = gettext('The specified amount is unavailable.')        
    else:
        if float(result['data'][0]['quantity']) >= quantity:
            status = 1
            result['price'] = quantity * float(result['data'][0]['Price'])
        else:
            message = gettext('The specified amount is unavailable.')      

    response = {'status': status, 'data': result, 'message': message,  'newCSRFtoken': newCSRFtoken}
    return jsonify(response)


@app.route("/edit-store/<quantity_pt_IDs>", methods=["GET"])
@app.route("/edit-store", methods=["POST"])
@login_required
def edit_store(quantity_pt_IDs=None):
    newCSRFtoken = generate_csrf()
    if request.method == "POST":
        if not request.form.get('quantityID') or request.form.get('quantityID') == 'null':
            answer = gettext('Something went wrong. Please try again!')
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
            return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'),  'newCSRFtoken': newCSRFtoken})

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
                return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!') + 'sSSSDASDF',  'newCSRFtoken': newCSRFtoken})

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
        if result['status'] == '-1':
            # response = {'status': '0', 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}
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
@login_required
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
                    ORDER BY `product`.`Order`, `product_type`.`Order` 
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
            return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'),  'newCSRFtoken': newCSRFtoken})

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
                return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!') + 'sSSSDASDF',  'newCSRFtoken': newCSRFtoken})

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
            return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'),  'newCSRFtoken': newCSRFtoken})

        answer = 'Done!'
        return jsonify({'status': '1', 'answer': answer,  'newCSRFtoken': newCSRFtoken})



@app.route("/create-promo-code", methods=["GET", "POST"])
# @login_required
def create_promo_code():
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
                        -- AND `product_type`.`Status` = 1
                    ORDER BY `product`.`ID`, `product_type`.`Order` 
                    -- LIMIT 2
                    ;
                    """
        sqlValTuple = (languageID,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        prData = json.dumps(result['data']) 

        sqlQueryAffiliate = "SELECT `ID`, `Firstname`, `Lastname`, `email` FROM `stuff` WHERE `rolID` = 2 AND `Status` = 1;"
        affiliates = sqlSelect(sqlQueryAffiliate, (), True)

        sideBar = side_bar_stuff()

        return render_template('create-promo-code.html', dataLength=result['length'], prData=prData, affiliates=affiliates, sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale())
    
    if request.method == "POST":
        if not request.form.get('products') or not request.form.get('expDate') or not request.form.get('promo'):
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!')})
        
        promo = request.form.get('promo')

        sqlQuery = "SELECT `promo` FROM `promo_code` WHERE `promo` = %s;"
        sqlValTuple = (promo,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        if result['length'] > 0:
            answer = promo + ' ' + gettext('code exists')
            return jsonify({'status': '0', 'answer': answer})


        json_str = request.form.get('products')
        try:
            products = json.loads(json_str)
        except json.JSONDecodeError as e:
            # "error": "Invalid JSON data", "message": str(e),
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

        # check products validity 
        for row in products:
            for key, value in row.items():
                if value == '':
                    return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})    

            if int(row['discount']) > 99:
                return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}) 
                
            if row.get('revard_option') == '0':
                if int(row['revard']) > 99:
                    return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})    

        affiliate = 0
        columns = "(`promo_code_id`, `discount_status`, `ptID`, `discount`,  `Status`)"
        values = "(%s, %s, %s, %s, %s)," * len(products)  
        if request.form.get('affiliate'):
            affiliate = request.form.get('affiliate')
            columns = "(`promo_code_id`, `discount_status`, `ptID`, `discount`,  `revard_value`, `revard_type`, `Status`)"
            values = "(%s, %s, %s, %s, %s, %s, %s)," * len(products)  
        
        expDate = request.form.get('expDate').replace("-", "/")

        sqlinsertPromo = f"""INSERT INTO `promo_code` (`Promo`, `affiliateID`, `expDate`, `Status`) VALUES (%s, %s, STR_TO_DATE(%s, '%m/%d/%Y'), 1);"""
        valTuplePromo = (promo, affiliate, expDate)
        resultInsert = sqlInsert(sqlinsertPromo, valTuplePromo)
        if resultInsert['status'] == 0:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}) 
        
        # Create tuple prototype for db insert
        promoID = resultInsert['inserted_id']
        protoTuple = []
        for row in products:
            protoTuple.append(promoID)
            for key, value in row.items():                   
                protoTuple.append(int(value))

            protoTuple.append(1)
     
        valTuples = tuple(protoTuple)


        sqlInsertDiscount = f"INSERT INTO `discount` {columns} VALUES {values[:-1]}"
        
        discountInsert = sqlInsert(sqlInsertDiscount, valTuples)                                                                
        if discountInsert['status'] == 0:
            return jsonify({'status': "0", 'answer': discountInsert['answer']})

    return jsonify({'status': "1", 'answer': gettext('Promo Code Created Successfully')})


@app.route('/promo-codes', methods=['GET'])
# @login_required
def promo_codes():

    sqlQuery = """
                    SELECT 
                        `promo_code`.`ID`, 
                        `promo_code`.`Promo`,
                        `stuff`.`Firstname`, 
                        `stuff`.`Lastname`, 
                        `stuff`.`Email`, 
                        `promo_code`.`expDate`, 
                        `promo_code`.`Status` 
                    FROM `promo_code` 
                    LEFT JOIN `stuff` ON `stuff`.`ID` = `promo_code`.`affiliateID`
                    WHERE `promo_code`.`Status` = 1
                    ORDER BY `promo_code`.`ID` DESC
                    ;
                """
    result = sqlSelect(sqlQuery, (), True)

    newCSRFtoken = generate_csrf()
    sideBar = side_bar_stuff()
    return render_template('promo-codes.html', result=result, currentDate=date.today(), sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale()) 

    
@app.route('/edit-promo', methods=['POST'])
# @login_required
def edit_promo():
    newCSRFtoken = generate_csrf()
    if not request.form.get('products') or not request.form.get('promoID') or not request.form.get('expDate') or not request.form.get('promo'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    promo = request.form.get('promo')
    promoID = int(request.form.get('promoID'))

    sqlQuery = "SELECT `promo` FROM `promo_code` WHERE `promo` = %s AND `ID` != %s;"
    sqlValTuple = (promo, promoID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        answer = promo + ' ' + gettext('code exists')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})


    json_str = request.form.get('products')
    try:
        products = json.loads(json_str)
    except json.JSONDecodeError as e:
        # "error": "Invalid JSON data", "message": str(e),
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    # check products validity 
    for row in products:
        for key, value in row.items():
            if value == '':
                return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})    

        if int(row['discount']) > 99:
            return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken}) 
            
        if row.get('revard_option') == '0':
            if int(row['revard']) > 99:
                return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})    
    
    
    sqlSelectOldData =  f"""
                        SELECT 
                            `promo_code`.`ID`, 
                            `promo_code`.`Promo`,
                            `promo_code`.`affiliateID`,
                            `promo_code`.`expDate`, 
                            `promo_code`.`Status`,
                            `product`.`ID` AS `prID`,
                            `product_type`.`ID` AS `ptID`,
                            `product`.`Title` AS `prTitle`,
                            `product_type`.`Title` AS `ptTitle`,
                            `discount`.`ID` AS `discountID`,
                            `discount`.`discount`,
                            `discount`.`discount_status`,
                            `discount`.`revard_value`,
                            `discount`.`revard_type` 
                        FROM `promo_code` 
                            LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID`
                            LEFT JOIN `product_type` ON `product_type`.`ID` = `discount`.`ptID`
                            LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                        WHERE `promo_code`.`ID` = %s;
                        """
    
    resultOldData = sqlSelect(sqlSelectOldData, (promoID,), True)

    promoCheck = resultOldData['data'][0]
    # promoStatus = int(request.form.get('promo-status'))
    promoStatus = 1
    affiliateID = 0
    if request.form.get('affiliate') and int(request.form.get('affiliate')) > 0:
        affiliateID = int(request.form.get('affiliate'))
    expDate = datetime.strptime(request.form.get('expDate'), "%m-%d-%Y").date()
    
    # Update for table `promo_code`
    if promoCheck['Promo'] != promo or promoCheck['expDate'] != expDate or promoCheck['affiliateID'] != affiliateID or promoCheck['Status'] != promoStatus:
        sqlPromoUpdate = "UPDATE `promo_code` SET `Promo` = %s, expDate = %s, affiliateID = %s, Status = %s WHERE `ID` = %s"
        sqlValTuple = (promo, expDate, affiliateID, promoStatus, promoID)
        sqlUpdate(sqlPromoUpdate, sqlValTuple)

    sqlQueryUpdate =    """
                        UPDATE `discount` SET
                            `discount` = %s,
                            `discount_status` = %s,
                            `revard_value` = %s,
                            `revard_type` = %s
                        WHERE `promo_code_id` = %s AND `ptID` = %s
                        """
    for row in resultOldData['data'][:]:
        for product in products[:]:
            if row['ptID'] == int(product['ptID']):

                productRevard = product.get('revard')
                if productRevard is not None:
                    productRevard = int(product.get('revard'))
                
                productRevardOption = product.get('revard_option')
                if productRevardOption is not None:
                    productRevardOption = int(product.get('revard_option'))

                if row['discount'] != int(product['discount']) or row['discount_status'] != int(product['discount_status']) or row['revard_value'] != productRevard or row['revard_type'] != productRevardOption:
                    # print(f"row['discount'] is {row['discount']} and product['discount'] is {product['discount']}")
                    sqlValTuple = (int(product['discount']), int(product['discount_status']), productRevard, productRevardOption, promoID, row['ptID'])
                    updateResult = sqlUpdate(sqlQueryUpdate, sqlValTuple)
                    # print(updateResult['answer'])
                products.remove(product)
                resultOldData['data'].remove(row)

    if len(resultOldData['data']) > 0:
        placeholders = "%s," * len(resultOldData['data'])
        placeholders = placeholders[:-1]

        protoTuple = []
        for row in resultOldData['data']:
            protoTuple.append(row['discountID'])
            
        sqlValTuple = tuple(protoTuple)
        sqlQueryDelete = f"DELETE FROM `discount` WHERE `ID` IN ({placeholders});"
        sqlDelete(sqlQueryDelete, sqlValTuple)

    if len(products) > 0:
        affiliate = 0
        columns = "(`promo_code_id`, `discount_status`, `ptID`, `discount`,  `Status`)"
        values = "(%s, %s, %s, %s, %s)," * len(products)  
        if request.form.get('affiliate'):
            affiliate = request.form.get('affiliate')
            columns = "(`promo_code_id`, `discount_status`, `ptID`, `discount`,  `revard_value`, `revard_type`, `Status`)"
            values = "(%s, %s, %s, %s, %s, %s, %s)," * len(products)  
        
        protoTuple = []
        for row in products:
            protoTuple.append(promoID)
            for key, value in row.items():                   
                protoTuple.append(int(value))

            protoTuple.append(1)
     
        valTuples = tuple(protoTuple)

        sqlInsertDiscount = f"INSERT INTO `discount` {columns} VALUES {values[:-1]}"
        
        discountInsert = sqlInsert(sqlInsertDiscount, valTuples)  

    return jsonify({'status': "1", 'answer': gettext('Promo Code updated successfully!') , 'newCSRFtoken': newCSRFtoken})    


@app.route('/edit-promo-code/<promoID>', methods=['GET'])
# @login_required
def edit_promo_code(promoID):

    sqlQuery = """
                    SELECT 
                        `promo_code`.`ID`, 
                        `promo_code`.`Promo`,
                        `promo_code`.`affiliateID`,
                        DATE_FORMAT(`promo_code`.`expDate`, '%m-%d-%Y') AS `expDate`, 
                        `promo_code`.`Status`,
                        `product`.`ID` AS `prID`,
                        `product_type`.`ID` AS `ptID`,
                        `product`.`Title` AS `prTitle`,
                        `product_type`.`Title` AS `ptTitle`,
                        `discount`.`ID` AS `discountID`,
                        `discount`.`discount`,
                        `discount`.`discount_status`,
                        `discount`.`revard_value`,
                        `discount`.`revard_type` 
                    FROM `promo_code` 
                        LEFT JOIN `discount` ON `discount`.`promo_code_id` = `promo_code`.`ID`
                        LEFT JOIN `product_type` ON `product_type`.`ID` = `discount`.`ptID`
                        LEFT JOIN `product` ON `product`.`ID` = `product_type`.`Product_ID`
                    WHERE `promo_code`.`ID` = %s
                    ORDER BY `product`.`Order` ASC, `product_type`.`Order` ASC; 
                """
    discountsResult = sqlSelect(sqlQuery, (promoID,), True)
    discounts = json.dumps(discountsResult['data']) 


    sqlQueryAffiliate = "SELECT `ID`, `Firstname`, `Lastname`, `email` FROM `stuff` WHERE `rolID` = 2 AND `Status` = 1;"
    affiliates = sqlSelect(sqlQueryAffiliate, (), True)

    languageID = getLangID()
    sqlQuery = """SELECT 
                    `product`.`ID`,
                    `product`.`Title`,
                    `product_type`.`ID` AS `ptID`,
                    `product_type`.`Title` AS `ptTitle`
                FROM `product` 
                    LEFT JOIN `product_type` ON `product_type`.`Product_ID` = `product`.`ID`
                WHERE `product`.`Language_ID` = %s 
                    -- AND `product_type`.`Status` = 1
                ORDER BY `product`.`Order`, `product_type`.`Order` 
                ;
                """
    sqlValTuple = (languageID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    prData = json.dumps(result['data']) 

    newCSRFtoken = generate_csrf()
    sideBar = side_bar_stuff()
    return render_template('edit-promo-code.html', affiliateID=discountsResult['data'][0]['affiliateID'], promoCode=discountsResult['data'][0]['Promo'], expDate=discountsResult['data'][0]['expDate'], discounts=discounts,  affiliates=affiliates, prData=prData, promoID=promoID, dataLength=result['length'], sideBar=sideBar, newCSRFtoken=newCSRFtoken, current_locale=get_locale()) 

    
# Get Discounts With Promo Code
@app.route('/get-promo-discounts', methods=['POST'])
def get_promo_discounts():
    newCSRFtoken = generate_csrf()
    if not request.form.get('promo') or not request.form.get('products'):
        return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    promo = request.form.get('promo', '').strip()
    json_str = request.form.get('products')
    try:
        products = json.loads(json_str)
    except json.JSONDecodeError as e:
        # "error": "Invalid JSON data", "message": str(e),
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    # check products validity 
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
        answer = gettext('Invalid Promo Code')
        return jsonify({'status': "0", 'answer': answer, 'newCSRFtoken': newCSRFtoken})

    # Deside prices with discount
    discountPrice = 0
    totalPrice = 0
    for row in result['data']:
        for r in products:
            if row['ptID'] == r['ptID']:
                # print(f"row['Price'] is {type(row['Price'])} and r['quantity'] is {type(r['quantity'])} AND row['discount'] is {type(row['discount'])}")
                discountPrice = discountPrice + (row['Price'] * int(r['quantity']) * row['discount'] / 100)

    return jsonify({'status': "1", 'data': result['data'], 'discountPrice': discountPrice, 'totalPrice': totalPrice, 'newCSRFtoken': newCSRFtoken})


# Check weather promo code exists
@app.route('/check-promo-code', methods=['POST'])
def check_promo_code():
    newCSRFtoken = generate_csrf()
    if not request.form.get('promo'):
        return jsonify({'status': '0', 'newCSRFtoken': newCSRFtoken})
    
    # Check weather promo code exists in db
    promo = request.form.get('promo')
    sqlQuery = "SELECT `promo` FROM `promo_code` WHERE `promo` = %;"
    sqlValTuple = (promo,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] > 0:
        return jsonify({'status': '0'})
    

    return jsonify({'status': '1', 'val': promo})


# Check if product type exists in specified quantity
@app.route('/check-pt-quantity', methods=['POST'])
def check_pt_quantity():
    newCSRFtoken = generate_csrf()
    if not request.form.get('num') or not request.form.get('ptID') :
        answer = gettext('Something went wrong. Please try again!')
        return jsonify({'status': '0', 'answer': answer,  'newCSRFtoken': newCSRFtoken})
    
    ptID = request.form.get('ptID') 
    num = request.form.get('num') 

    sqlQuery = "SELECT SUM(`Quantity`) AS `Quantity` FROM `quantity` WHERE `productTypeID` = %s AND `expDate` >= CURDATE() AND `Status` = 1;"
    sqlValTuple = (ptID,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    
    if result['data'][0]['Quantity'] == None or result['data'][0]['Quantity'] == 0:
        answer = gettext("The seller doesn't have that many left.")
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

    if int(result['data'][0]['Quantity']) == 0:
        maxQuantity = result['data'][0]['Quantity']

        answer = gettext("Out of stock") 
        return jsonify({'status': '2', 'max': maxQuantity, 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    if int(result['data'][0]['Quantity']) < int(num):
        maxQuantity = result['data'][0]['Quantity']

        answer = gettext("Maximum available quantity is ") + str(maxQuantity) + '. ' + str(maxQuantity) + ' ' + gettext("item added to the cart") 
        return jsonify({'status': '2', 'max': maxQuantity, 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    return jsonify({'status': '1', 'newCSRFtoken': newCSRFtoken})


@app.route('/<myLinks>')
def index(myLinks):
    
    content = get_RefKey_LangID_by_link(myLinks)
    slideShow = []
    supportedLangsData = []
    metaTags = ''
    ptID = ''
    
    if content is not None:  
        langData = getLangdatabyID(content['LanguageID'])
        session['lang'] = langData['Prefix']

        if content['ptID']:
            ptID = content['ptID']
        
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
    else:
        myHtml = 'error.html'
        prData = ''
    cartMessage = [ 
                    gettext("You have already added this product to the basket. You can change the quantity if You would like to."),
                    generate_csrf(),
                    gettext("In Basket")
    ]  

    return render_template(myHtml, cartMessage=cartMessage, prData=prData, ptID=ptID, slideShow=slideShow, supportedLangsData=supportedLangsData, metaTags=metaTags, current_locale=get_locale())


@app.route("/get_langs", methods=["POST"])
def get_langs():

    arr = supported_langs()
    defLang = getDefLang()
    currentLangPrefix = session.get('lang', defLang['Prefix'])
    langData = []
    for row in arr:
        selected = False
        if currentLangPrefix == row['Prefix']:
            selected = True
        childDict = {'value':  row['Prefix'], 'text': row['Language'], 'selected': selected}
        langData.append(childDict)
        
    return langData


@app.route("/subscribe", methods=["POST"])
def subscribe():
    newCSRFtoken = generate_csrf()
    # Check if email exists
    if not request.form.get('Email'):
        answer = gettext('Please specify email!')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})  
    
    Email = request.form.get('Email').strip()

    # Validate email
    emailPattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    # Check if the email matches the pattern
    if not re.match(emailPattern, Email):
        answer = gettext('Invalid email format')
        return jsonify({'status': '0', 'answer': answer, 'newCSRFtoken': newCSRFtoken})
    
    sqlQuery = "SELECT `email` FROM `emails` WHERE `email` = %s;"
    result = sqlSelect(sqlQuery, (Email,), True)
    if result['length'] > 0:
        sqlQueryUpdate = "UPDATE `emails` SET `Status` = 2 WHERE `email` = %s;"
        resultUpdate = sqlUpdate(sqlQueryUpdate, (Email,))
        if resultUpdate['status'] == '-1':
            return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})

    else:
        langID = getLangdata(session['lang'])['ID']
        sqlQueryInsert = "INSERT INTO `emails` (`email`, `langID`, `Status`) VALUES (%s, %s, %s)"
        sqlValTuple = (Email, langID, 2)
        resultInsert = sqlInsert(sqlQueryInsert, sqlValTuple)
        if resultInsert['status'] == 0:
            return jsonify({'status': '0', 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})


    answer = gettext("You have subscribed successfully!")
    return jsonify({'status': '1', 'answer': answer, 'newCSRFtoken': newCSRFtoken})


@app.route("/get-available-pts", methods=["POST"])
def get_available_pts():
    newCSRFtoken = generate_csrf()
    if not request.form.get('prID'):
        return jsonify({'status': "0", 'answer': gettext('Something went wrong. Please try again!'), 'newCSRFtoken': newCSRFtoken})
    
    prID = request.form.get('prID')
    langID = getLangID()

    sqlQuery =  """
                    SELECT 
                    `product`.`Title` AS `prTitle`,
                    `product`.`url`,
                    `product_type`.`Title` AS `ptTitle`,
                    `product_type`.`Price`,
                    `product_type`.`Status`,
                    (SELECT `Name` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 AND `slider`.`Order` = 0 LIMIT 1) AS `imgName`,
                    (SELECT `AltText` FROM `slider` WHERE `slider`.`ProductID` = `product_type`.`ID` AND `slider`.`Type` = 2 LIMIT 1) AS `AltText`,
                    (SELECT SUM(`Quantity`) FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE()) AS `quantity`,
                    (SELECT `maxQuantity` FROM `quantity` WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE() ORDER BY `maxQuantity` DESC LIMIT 1) AS `maxAllowdQuantity`,
                    `product_type`.`ID` AS `ptID`        
                FROM `product`
                    LEFT JOIN `product_type` ON `product_type`.`Product_ID` = `product`.`ID`
                WHERE `product`.`ID` = %s 
                    AND `product`.`Language_ID` = %s 
                    AND (SELECT SUM(`Quantity`) FROM `quantity` 
                        WHERE `quantity`.`productTypeID` = `product_type`.`ID` AND `quantity`.`expDate` > CURDATE()) > 0
                ORDER BY `product`.`ID`, `product_type`.`Order`;            
                """
    sqlValTuple = (prID, langID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    if result['length'] == 0:
        return jsonify({'status': "0", 'answer': gettext("Out of stock."), 'newCSRFtoken': newCSRFtoken})
    
    return jsonify({'status': "1", 'data': result['data'], 'newCSRFtoken': newCSRFtoken})


# @app.route("/timer", methods=["GET"])
# def random_reminder():
#     return render_template('random-reminder.html')



if __name__ == '__main__':
    app.run(ssl_context=(cert_file, key_file), debug=True)
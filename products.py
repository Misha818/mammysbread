from flask import session, redirect, jsonify
from dotenv import load_dotenv
from flask_babel import Babel, _, lazy_gettext as _l, gettext

from sysadmin import checkForRedundantFiles, removeRedundantFiles, get_pr_id_by_lang, sqlInsert, sqlSelect, sqlUpdate, getLangID, getDefLang, getSupportedLangs, getUserID, get_pc_ref_key, get_pc_id_by_lang, pr_name_check, pr_url_check, fileUpload


import mysql.connector
import os
import re
import base64
import uuid

load_dotenv()

# Determine the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Set the static folder path relative to the current script's directory
static_folder_path = os.path.join(current_dir, 'static')
target_directory = os.path.join(static_folder_path, 'images/quilljs')
os.makedirs(target_directory, exist_ok=True)

# Create a connection to the MySQL database
db_connection = mysql.connector.connect(
    host=os.getenv('LOCALHOST'),
    user=os.getenv('USER'),
    password=os.getenv('PASSWORD'),
    database=os.getenv('DATABASE')
)


def submit_reach_text(html_content, productID):
    
    # Regular expression to extract the base64 string from the <img> tag
    pattern = r'<img\s+[^>]*src="data:image/([^;]+);filename=([^;]+);base64,([^"]+)"[^>]*>'
    matches = re.findall(pattern, html_content)

    # Placeholder for the modified HTML content
    modified_html = html_content
    
    for idx, match in enumerate(matches):
        # Match contains (image_type, base64_string)
        image_type, filename, base64_string = match

        # Check if the filename already exists
        image_filename = filename
        old_file_name = filename
        
        # Check if the filename exists and create a unique filename if it does
        file_path = os.path.join(target_directory, image_filename)
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
            image_filename = unique_filename
            
            # Update the file path with the new unique filename
            file_path = os.path.join(target_directory, unique_filename)
            


        
        # Create the image path
        image_path = os.path.join(target_directory, image_filename)
        
        # Decode the base64 string and write the image file
        image_data = base64.b64decode(base64_string)
        with open(image_path, 'wb') as image_file:
            image_file.write(image_data)
        
        # Replace the base64 string with the new image link
        image_url = f'/static/images/quilljs/{image_filename}'
        base64_pattern = re.escape(f'data:image/{image_type};filename={old_file_name};base64,') + '([^"]+)'
        modified_html = re.sub(base64_pattern, image_url, modified_html, 1)
    
    img_src_pattern = r'<img[^>]+src="([^">]+)"'

    new_img_urls = set(re.findall(img_src_pattern, modified_html))

    # Check for unused files and remove them
    sqlQueryOld = "SELECT `Text` FROM `article` WHERE `ID` = %s;"
    sqlQueryOldVal = (productID,)
    result = sqlSelect(sqlQueryOld, sqlQueryOldVal, True)

    if result['data'][0]['Text'] is not None:
        old_img_urls = set(re.findall(img_src_pattern, result['data'][0]['Text']))

        imgs_to_remove = list(old_img_urls - new_img_urls)

        for url in imgs_to_remove:
            arr = url.split('/')
            fileName = arr[4]
            fileDir = arr[2] + '/' + arr[3]
        
            removeRedundantFiles(fileName, fileDir)
                
    # Insert the content into the MySQL database
    sqlUpdateRT =   f"""UPDATE `article` SET
                        `Text` = %s,
                        `DateModified` = CURDATE()
                        WHERE `ID` = %s     
                    """
    sqlUpdateRTValTuple = (modified_html, productID)
    resultRT = sqlUpdate(sqlUpdateRT, sqlUpdateRTValTuple)

    return resultRT


# Add product category database action
def add_p_c_sql(categoryName, file, AltText, currentLanguage):
    
    # Check whether Category Name exists
    sqlQuery = "SELECT `Article_Category_ID` FROM `article_category` WHERE `Article_Category_Name` = %s;"
    sqlValuesTuple = (categoryName,)
    result = sqlSelect(sqlQuery, sqlValuesTuple, True)
    
    if result['length'] > 0:
        answer = gettext('Category Exists!')
        return jsonify({'status': '3', 'answer': answer}) # categoryName Exists 
    
    # Save the file
    unique_filename = ''
    if file:
        unique_filename = fileUpload(file, 'images/pc_uploads')

    # Insert the content into the MySQL database
    sqlQuery = "INSERT INTO `article_category` (`Article_Category_Name`, `Article_Category_Images`, `AltText`, `User_ID`, `Article_Category_Status`) VALUES (%s, %s, %s, %s, '1')"
    userID = getUserID()
    sqlValuesTuple =  (categoryName, unique_filename, AltText, userID)
    result = sqlInsert(sqlQuery, sqlValuesTuple)
    insertedID = result['inserted_id']
        
    # Get the highest AC_Ref_Key value
    sqlQueryLatestRel_ID = "SELECT `AC_Ref_Key` FROM `article_c_relatives` ORDER BY `AC_REF_KEY` DESC LIMIT 1"
    result = sqlSelect(sqlQueryLatestRel_ID, False, True)

    
    NewRef_KEY = 1
    if result['length'] > 0:
        NewRef_KEY = result['data'][0]['AC_Ref_Key'] + 1

    langID = currentLanguage

    # Insert into article_c_relatives
    sqlQueryRel = "INSERT INTO `article_c_relatives` (`AC_Ref_Key`, `AC_ID`, `Language_ID`, `User_ID`) VALUES (%s, %s, %s, %s)"
    sqlRelValuesTuple = (NewRef_KEY, insertedID, langID, userID)
    resultRel = sqlInsert(sqlQueryRel, sqlRelValuesTuple)
    
    answer = resultRel['answer']
    
    return jsonify({'status': '1', 'answer': answer, 'location': 'add-product-category'})


# Edit product category database action
def edit_p_c_sql(categoryName, file, AltText, pc_id, image, categoryStatus, relImage):
    
    # Check whether Category Name exists
    sqlQueryCheck = "SELECT `Article_Category_ID` FROM `article_category` WHERE `Article_Category_Name` = %s AND `Article_Category_ID` != %s ;"
    sqlValueTuple = (categoryName, pc_id)
    result = sqlSelect(sqlQueryCheck, sqlValueTuple, True)
   
    if result['length'] > 0:
        answer = gettext('Category Name Exists!')
        return jsonify({'status': '3', 'answer': answer}) # categoryName Exists 


    # Save the file
    unique_filename = fileUpload(file, 'images/pc_uploads')  

    # if len(relImage) > 0:
    #     unique_filename = relImage
    # else:
    #     if file != None and image != '1':
    #         upload_to = os.path.join(static_folder_path, 'images/pc_uploads')
    #         filename = file.filename
    #         file_path = os.path.join(upload_to, filename)
            
    #         # Check if the file exists and create a unique filename if it does
    #         if os.path.exists(file_path):
    #             unique_filename = f"{uuid.uuid4().hex}_{filename}"
    #             file_path = os.path.join(upload_to, unique_filename)
    #         else:
    #             unique_filename = filename

    #         file.save(file_path)



    # STegh es haskaci es inch if u else a!!!!!!!!!
    if image == '1':
        sqlScript = ''
        sqlValueTuple = (categoryName, categoryStatus, pc_id)    
    else:
        sqlScript = '`Article_Category_Images` = %s,'                
        sqlValueTuple = (categoryName, unique_filename, categoryStatus, pc_id)    


    # Update the content in the MySQL database
    sqlQuery = f"""
            UPDATE `article_category` 
            SET `Article_Category_Name` = %s, 
            {sqlScript}
                `Article_Category_Status` = %s 
            WHERE `Article_Category_ID` = %s
            """
   
    result = sqlUpdate(sqlQuery, sqlValueTuple)
    

    # new_id = '2'
    if result['status'] == 1:
        answer = gettext('Done!')
    else:
        answer = result['answer']

    return jsonify({'status': '1', 'answer': answer, 'location': 'article-categories'})


def edit_p_c_view(pc_ref_key):  
                                 
    sqlCheck = "SELECT `AC_ID` FROM `article_c_relatives` WHERE `AC_Ref_Key` = %s;"
    sqlCheckValTuple = (pc_ref_key,)
    rCheck = sqlSelect(sqlCheck, sqlCheckValTuple, True)

    if rCheck['length'] == 0:
        content = {'content': False}
        return content

    langID = getLangID()
    
    sqlQuery =  f"""SELECT * FROM `article_category` 
                    WHERE `Article_Category_ID` = (SELECT `AC_ID` FROM `article_c_relatives` WHERE `AC_Ref_Key` = %s AND `Language_ID` = %s);
                """
    
    sqlValueTuple = (pc_ref_key, langID)
    result = sqlSelect(sqlQuery, sqlValueTuple, True)

    if result['length'] == 0:
        userID = getUserID()
        sqlInsertPC = "INSERT INTO `article_category` SET `User_ID` = %s, `Article_Category_Status` = %s;" 
        sqlValueTuplePC = (userID, 1)
        resultPC = sqlInsert(sqlInsertPC, sqlValueTuplePC)

        inserted_id =  resultPC['inserted_id']

        
        sqlInsertPC_Rel = f"""INSERT INTO `article_c_relatives` (`Language_ID`, `AC_ID`, `AC_Ref_Key`, `User_ID`) 
                            VALUES (%s, %s, %s, %s) 
                            """
        sqlInsertPC_RelVal = (langID, inserted_id, pc_ref_key, userID)

        resultPC_Rel = sqlInsert(sqlInsertPC_Rel, sqlInsertPC_RelVal)

        if resultPC_Rel['inserted_id']:

            sqlQuery1 =  f"""SELECT * FROM `article_category` 
                WHERE `Article_Category_ID` = (SELECT `AC_ID` FROM `article_c_relatives` WHERE `AC_Ref_Key` = %s AND `Language_ID` = %s);
            """

            sqlValueTuple1 = (pc_ref_key, langID)
            result1 = sqlSelect(sqlQuery1, sqlValueTuple1, True)



            if result1['length'] > 0:
                image1 = 0
                if result1['data'][0]['Article_Category_Images']:
                    image1 = result1['data'][0]['Article_Category_Images']

                myName = ''
                if result1['data'][0]['Article_Category_Name']:
                    myName = result1['data'][0]['Article_Category_Name']
                
                AltText = ''
                if result1['data'][0]['AltText']:
                    AltText = result1['data'][0]['AltText']

                content = {
                    'name': myName, 
                    'image': image1, 
                    'AltText': AltText, 
                    'status': result1['data'][0]['Article_Category_Status'], 
                    'pc_id': result1['data'][0]['Article_Category_ID'],
                    'content': True
                }
        else:
            content = {'content': False}
    else:
        myImage = 0
        if result['data'][0]['Article_Category_Images']:
            myImage = result['data'][0]['Article_Category_Images']
        
        myName = ''
        if result['data'][0]['Article_Category_Name']:
            myName = result['data'][0]['Article_Category_Name']
        
        AltText = ''
        if result['data'][0]['AltText']:
            AltText = result['data'][0]['AltText']


        content = {
            'name': myName, 
            'image': myImage, 
            'AltText': AltText, 
            'status': result['data'][0]['Article_Category_Status'], 
            'pc_id': result['data'][0]['Article_Category_ID'],
            'content': True
        }

    return content


def get_product_categories(pc_id, languageID):

    if pc_id is not None:
        # Get `Product_Category_ID` from `product` table
        sqlQuery = """
                    SELECT `Article_Category_ID` FROM `article` WHERE `ID` = %s
                   """
        sqlQueryValTuple = (pc_id,)
        result = sqlSelect(sqlQuery, sqlQueryValTuple, True)
        if result['length'] > 0:
            pc_id = result['data'][0]['Article_Category_ID']
        else:
            pc_id = None    

    # Select the content from `Product_Category` table
    sqlQueryCategory = f"""
                        SELECT `Article_Category_ID`, `Article_Category_Name`, `AC_Ref_Key`
                        FROM `article_category`
                        LEFT JOIN `article_c_relatives`
                            ON `article_c_relatives`.`AC_ID` = `article_category`.`Article_Category_ID`
                        WHERE `Article_Category_Status` = 1 AND `article_c_relatives`.`Language_ID` = %s;
                        """
    sqlQueryCatVal = (languageID,)
    resultCategory = sqlSelect(sqlQueryCategory, sqlQueryCatVal, True)

    answer = {
        'article_category': resultCategory,
        'Article_Category_ID': pc_id
    }

    return answer


def get_thumbnail_images(RefKey):
    langID = getLangID()
    sqlQuery = f"""SELECT `Thumbnail`, `AltText` 
                FROM `article` 
                LEFT JOIN `article_relatives` 
                    ON `article`.`ID` = `article_relatives`.`A_ID`
                WHERE `A_Ref_Key` = %s AND `article_relatives`.`Language_ID` != %s;
                """
    sqlValueTuple = (RefKey, langID)
    result = sqlSelect(sqlQuery, sqlValueTuple, True)

    answer = {'imageList': [], 'image': False}

    if result['length'] > 0:
        i = 0
        while i < len(result['data']):
            if result['data'][i]['Thumbnail'] is not None:
                if len(result['data'][i]['Thumbnail']) > 0:
                    answer['image'] = True
                    myDict = {'thumbnail': result['data'][i]['Thumbnail'], 'altText': result['data'][i]['AltText']}
                    answer['imageList'].append(myDict)
            i = i + 1

    return answer


def get_article_category_images(RefKey):
    langID = getLangID()
    sqlQuery = f"""SELECT `Article_Category_Images`, `AltText` 
                FROM `article_category` 
                LEFT JOIN `article_c_relatives` 
                    ON `article_category`.`Article_Category_ID` = `article_c_relatives`.`AC_ID`
                WHERE `article_c_relatives`.`AC_Ref_Key` = %s AND `article_c_relatives`.`Language_ID` != %s;
                """
    sqlValueTuple = (RefKey, langID)
    
    # print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
    # print(sqlValueTuple)
    # print('BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB')

    result = sqlSelect(sqlQuery, sqlValueTuple, True)

    answer = {'imageList': [], 'image': False}

    if result['length'] > 0:
        i = 0
        while i < len(result['data']):
            if result['data'][i]['Article_Category_Images'] is not None:
                if len(result['data'][i]['Article_Category_Images']) > 0:
                    answer['image'] = True
                    myDict = {'Article_Category_Images': result['data'][i]['Article_Category_Images'], 'altText': result['data'][i]['AltText']}
                    answer['imageList'].append(myDict)
            i = i + 1

    return answer

# Add product action
def add_product(productName, productLink, languageID, CategoryID, file, AltText, shortDescription, longDescription, RefKey): # 9

    myResponse = {'status': '1', 'answer': 'Done!'}

    # Check if product name (Product_Title) exists
    prNameCheck = pr_name_check(productName, languageID, None)    
    if prNameCheck['status'] == '1':    
        myResponse['status'] = '3'    
        myResponse['answer'] = prNameCheck['answer']    

        return myResponse

    
    # Check if link (Product_Url) exists
    prUrlCheck = pr_url_check(productLink, languageID, None)
    if prUrlCheck['status'] == '1':
        myResponse['status'] = '5'   
        myResponse['answer'] = prUrlCheck['answer']  
    
        return myResponse
 
    unique_filename = fileUpload(file, 'images/thumbnails')

    userID = getUserID()  # Stegh es: short u long descriptionner@ lracru table - um!
    sqlQueryInsert = "INSERT INTO `article` (`Title`, `Url`, `User_ID`, `Language_ID`, `Article_Category_ID`, `Thumbnail`, `AltText`,  `Article_Status`, `ShortDescription`, `LongDescription`) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    sqlQueryValInsert = (productName, productLink, userID, languageID, CategoryID, unique_filename, AltText, 1, shortDescription, longDescription)

    resultInsert = sqlInsert(sqlQueryInsert, sqlQueryValInsert)

    if resultInsert['inserted_id']:
        inserted_id = resultInsert['inserted_id']
        
        myResponse['Ref_Key'] = RefKey
        if RefKey != '':

            sqlInsertRel = "INSERT INTO `article_relatives` (`A_ID`, `A_Ref_Key`, `Language_ID`, `User_ID`) VALUES (%s, %s, %s, %s)"
            sqlInsertRelVal = (inserted_id, RefKey, languageID, userID)
            resultRelAction = sqlInsert(sqlInsertRel, sqlInsertRelVal)

            if resultRelAction['inserted_id'] is None:
                myResponse['status'] = '0'     
                myResponse['answer'] = gettext('Something Wrong!')  
 

        else:
             
            PR_Ref_Key = 1

            sqlQueryRef_Key = "SELECT `A_Ref_Key` FROM `article_relatives` ORDER BY `A_REF_KEY` DESC LIMIT 1" 
            resultRefKey = sqlSelect(sqlQueryRef_Key, False, True)

            if resultRefKey['length'] > 0:
                PR_Ref_Key = resultRefKey['data'][0]['A_Ref_Key'] + 1

            sqlInsertRel = "INSERT INTO `article_relatives` (`A_ID`, `A_Ref_Key`, `Language_ID`, `User_ID`) VALUES (%s, %s, %s, %s)"
            sqlInsertRelVal = (inserted_id, PR_Ref_Key, languageID, userID)
            resultRelAction = sqlInsert(sqlInsertRel, sqlInsertRelVal)

            if resultRelAction['inserted_id'] is None:
                myResponse['status'] = '0'     
                myResponse['answer'] = gettext('Something Wrong! First')  

            myResponse['Ref_Key'] = PR_Ref_Key
    else:
        myResponse['status'] = '0'     
        myResponse['answer'] = gettext('Something Wrong! Second')  

    return myResponse


def add_product_lang(productName, productLink, languageID, CategoryID, RefKey, file, AltText, shortDescription, longDescription): # 9

    myResponse = {'status': '1', 'answer': 'Done!'}
    
    # Check if product name (Product_Title) exists
    sqlQueryCheck3 = "SELECT `ID` FROM `article` WHERE `Title` = %s AND `Language_ID` = %s"
    sqlQueryCheck3Val = (productName, languageID)
    result3 = sqlSelect(sqlQueryCheck3, sqlQueryCheck3Val, True)

    if result3['length'] > 0:
        myResponse['status'] = '3'     
        myText = f"""'{productName}' Product Exists!"""
        myResponse['answer'] = gettext(myText)    

        return myResponse
    
    # Check if link (Product_Url) exists
    sqlQueryCheck5 = "SELECT `ID` FROM `article` WHERE `Url` = %s  AND `Language_ID` = %s"
    sqlQueryCheck5Val = (productLink, languageID)
    result5 = sqlSelect(sqlQueryCheck5, sqlQueryCheck5Val, True)

    if result5['length'] > 0:
        myResponse['status'] = '5'     
        myText = f"""'{productLink}' Link Exists!"""
        myResponse['answer'] = gettext(myText)    

        return myResponse
    
    unique_filename = fileUpload(file, 'images/thumbnails')
    
    userID = getUserID()
    # sqlQueryInsert = "INSERT INTO `article` (`Title`, `Url`, `User_ID`, `Language_ID`, `Article_Category_ID`, `Article_Status`, `Thumbnail`, `AltText`, `ShortDescription`, `LongDescription`) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    # sqlQueryValInsert = (productName, productLink, userID, languageID, CategoryID, 1, unique_filename, altText, shortDescription, longDescription)
    sqlQueryInsert = "INSERT INTO `article` (`Title`, `Url`, `User_ID`, `Language_ID`, `Article_Category_ID`, `Thumbnail`, `AltText`,  `Article_Status`, `ShortDescription`, `LongDescription`) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    sqlQueryValInsert = (productName, productLink, userID, languageID, CategoryID, unique_filename, AltText, 1, shortDescription, longDescription)

    print('Lang')
    print(sqlQueryValInsert)
    print('End of Lang')

    resultInsert = sqlInsert(sqlQueryInsert, sqlQueryValInsert)

    # print(resultInsert)
    if resultInsert['inserted_id']:
        inserted_id = resultInsert['inserted_id']

        sqlInsertRel = "INSERT INTO `article_relatives` (`A_ID`, `A_Ref_Key`, `Language_ID`, `User_ID`) VALUES (%s, %s, %s, %s)"
        sqlInsertRelVal = (inserted_id, RefKey, languageID, userID)
        resultRelAction = sqlInsert(sqlInsertRel, sqlInsertRelVal)

        if resultRelAction['inserted_id'] is None:
            myResponse['status'] = '0'     
            myResponse['answer'] = gettext('Something Wrong!')  

        myResponse['Ref_Key'] = RefKey
    else:
        myResponse['status'] = '0'     
        myResponse['answer'] = gettext('Something Wrong!')   # Problem is here

    return myResponse


def productDetails(RefKey, articleStatus):
    sqlQuery = f""" SELECT 
                        `article`.`ID`,
                        `article`.`Article_Category_ID`,
                        `article`.`Url`,
                        `article`.`Title`,
                        `article`.`Text`,
                        `article`.`Thumbnail`,
                        `article`.`Language_ID`,
                        `article`.`ShortDescription`,
                        `article`.`LongDescription`,
                        `article`.`DateModified`,
                        `article`.`DatePublished`,
                        `article`.`Article_Status`
                    FROM `article`
                    LEFT JOIN `article_relatives` 
                        ON `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`A_Ref_Key` = %s 
                    AND `article`.`Language_ID` = %s
                    {articleStatus}
                    
                """
    Language_ID = getLangID()
    sqlValTuple = (RefKey, Language_ID)
    result = sqlSelect(sqlQuery, sqlValTuple, True)
    return result


def constructPrData(RefKey, articleStatus):
    prData = productDetails(RefKey, articleStatus)
    content = {'content': False, 'headers': False}
    if prData['length'] > 0:
        row = prData['data'][0]
        content = {
            'Product_ID': row['ID'], 
            'Product_Category_ID': row['Article_Category_ID'], 
            'Url': row['Url'], 
            'Title': row['Title'], 
            'Text': row['Text'], 
            'Thumbnail': row['Thumbnail'], 
            'ShortDescription': row['ShortDescription'], 
            'LongDescription': row['LongDescription'], 
            'DateModified': row['DateModified'], 
            'DatePublished': row['DatePublished'], 
            'RefKey': RefKey, 
            'LanguageID': row['Language_ID'], 
            'prUpdate': gettext('Update'), 
            'prSaving': gettext('Saving...'), 
            'Status': row['Article_Status'], 
            'content': True
        }  

        if len(row['Title']) > 0 or len(row['Url']) > 0:
            content['headers'] = True   
    else:
        # Check whether product exists in any available language
        sqlQuery = "SELECT * FROM `article_relatives` WHERE `A_Ref_Key` = %s"
        sqlValTuple = (RefKey,)
        result = sqlSelect(sqlQuery, sqlValTuple, True)
        if result['length'] > 0:
            sqlQueryPC = "SELECT `Article_Category_ID` FROM `article` WHERE `ID` = %s"
            sqlQueryValPC = (result['data'][0]['A_ID'],)
            resultCategory = sqlSelect(sqlQueryPC, sqlQueryValPC, True)

            pcRefKey = get_pc_ref_key(resultCategory['data'][0]['Article_Category_ID'])
            pc_id = get_pc_id_by_lang(pcRefKey)
            content['content'] = True
            content['Article_Category_ID'] = pc_id
            content['Product_Category_ID'] = pc_id
            content['ID'] = result['data'][0]['A_ID']


    return content

# product headers update action
def edit_p_h(productName, productLink, languageID, CategoryID, RefKey, ShortDescription, LongDescription):
    
    productID = get_pr_id_by_lang(RefKey, languageID)
    myResponse = {'status': '1', 'answer': 'Done!'}

    # Check if product name exists
    nameCheck = pr_name_check(productName, languageID, productID)
    if nameCheck['status'] == '1':    
        myResponse['status'] = '3'    
        myResponse['answer'] = nameCheck['answer']    

        return myResponse

    # Check if product link exists
    urlCheck = pr_url_check(productLink, languageID, productID)
    if urlCheck['status'] == '1':
        myResponse['status'] = '5'   
        myResponse['answer'] = urlCheck['answer']  
    
        return myResponse
    
    userID = getUserID()
    sqlPRUpdate = f"""UPDATE `article`
                    SET `Title` = %s, 
                        `Url` = %s, 
                        `User_ID` = %s, 
                        `Language_ID` = %s, 
                        `ShortDescription` = %s, 
                        `LongDescription` = %s,
                        `DateModified` = CURDATE(), 
                        `Article_Category_ID` = %s
                    WHERE `ID` = %s
                    """
    sqlPRUpdateVal = (productName, productLink, userID, languageID, ShortDescription, LongDescription, CategoryID, productID)

    resulUpdate = sqlUpdate(sqlPRUpdate, sqlPRUpdateVal)

    return resulUpdate


def checkCategoryName(RefKey, languageID, categoryName):

    # Get article_category ID
    sqlQuery = f""" SELECT `AC_ID` FROM `article_c_relatives` 
                    WHERE `article_c_relatives`.`AC_Ref_Key` = %s
                      AND `article_c_relatives`.`Language_ID` = %s;                      
                """
    
    # WHERE Article_Category_ID != to our article category
    sqlVal = (RefKey, languageID)
    result = sqlSelect(sqlQuery, sqlVal, True)

    categoryID = result['data'][0]['AC_ID']

    sqlQueryCheck = f"""
                    SELECT `Article_Category_ID` FROM `article_category` 
                    WHERE `Article_Category_ID` != %s
                        AND `Article_Category_Name` = %s      
                    """
    sqlValCheck = (categoryID, categoryName)
    resultCheck = sqlSelect(sqlQueryCheck, sqlValCheck, True)

    if resultCheck['length'] > 0:
        return True
    else:
        return False

def get_RefKey_LangID_by_link(myLink):
    sqlQuery = "SELECT `ID`, `Language_ID` FROM `article` WHERE `Url` = %s;"
    sqlValTuple = (myLink,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    print('AAAAAAAAAAAAAAAAAAAAA111')
    print(result)
    print('BBBBBBBBBBBBBBBBBBBBB222')

    if result['length'] == 0:
        return None
    
    articleID = result['data'][0]['ID']

    sqlQueryRef = "SELECT `A_Ref_Key` FROM `article_relatives` WHERE `A_ID` = %s;"
    sqlValRef = (articleID,)
    resultRef = sqlSelect(sqlQueryRef, sqlValRef, True)

    if result['length'] == 0:
        return None
    
    content = {
        'RefKey': resultRef['data'][0]['A_Ref_Key'],
        'LanguageID': result['data'][0]['Language_ID'],
    }

    return content


def get_ArticleID_LangID_by_link(myLink):
    sqlQuery = "SELECT `ID`, `Language_ID` FROM `article` WHERE `Url` = %s;"
    sqlValTuple = (myLink,)
    result = sqlSelect(sqlQuery, sqlValTuple, True)

    if result['length'] == 0:
        return None
    
    content = {
        'ArticleID': result['data'][0]['ID'],
        'LanguageID': result['data'][0]['Language_ID'],
    }

    return content
    
def removeRedundantIMG(content):
    fileName = content['fileName']
    colonName = content['colonName']
    tableName = content['tableName']
    fileDir = content['fileDir']
    
    if checkForRedundantFiles(fileName, colonName, tableName) == True:
        removeRedundantFiles(fileName, fileDir)

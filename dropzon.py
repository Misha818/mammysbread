
# View form
@app.route('/thumbnail/<RefKey>', methods=['GET'])
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

    if result['length'] == 0:
        return render_template('thumbnail.html', errorMessage=True,  current_locale=get_locale())    
   
    
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

    return render_template('thumbnail.html', result=result, resultIMG=resultIMG, thumbnailImages=thumbnailImages, languageID=languageID, RefKey=RefKey, errorMessage=False, current_locale=get_locale() ) 

# End of view Form


# edititing action
@app.route('/edit_thumbnail', methods=['POST'])
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
    
    state = json.loads(state)

    if state['status'] == 0:
        unique_filename = state['file']     
    else:
        file = request.files.get('file')

        unique_filename = fileUpload(file, 'images/thumbnails')

    sqlQueryID = f"""
                    SELECT `article`.`ID`
                    FROM `article`
                    LEFT JOIN `article_relatives` ON `article_relatives`.`A_ID` = `article`.`ID`
                    WHERE `article_relatives`.`A_Ref_Key` = %s
                    AND `article_relatives`.`Language_ID` = %s
                    """
    
    sqlQueryValId = (RefKey, languageID)

    resultID = sqlSelect(sqlQueryID, sqlQueryValId, True)
    
    if resultID['length'] > 0:  
        articleID = resultID['data'][0]['ID']
    else:
        answer = gettext('Something is wrong!')
        return jsonify({'status': '0', 'answer': answer}) 

    sqlQuery   = f"""   
                    UPDATE `article`
                    SET `thumbnail` = %s, `AltText` = %s
                    WHERE `ID` = %s;
                 """
    
    sqlQueryVal = (unique_filename, altText, articleID)

    result = sqlUpdate(sqlQuery, sqlQueryVal)
    return result

# End of editing action







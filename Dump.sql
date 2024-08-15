-- Drop the existing database if it exists
DROP DATABASE IF EXISTS `blog_db`;

-- Create the database again
CREATE DATABASE `blog_db`
    DEFAULT CHARACTER SET utf8
    DEFAULT COLLATE utf8_general_ci;

-- Select the newly created database
USE `blog_db`;

-- Drop tables if they exist and create them again
DROP TABLE IF EXISTS `article`;
CREATE TABLE `article` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `Title` VARCHAR(255),
    `Url` VARCHAR(255),
    `AltText` VARCHAR(255),
    `Thumbnail` VARCHAR(255),
    `ShortDescription` VARCHAR(255) NOT NULL,
    `LongDescription` TEXT NOT NULL,
    `Text` TEXT,
    `DatePublished` DATE,
    `DateModified` DATE,
    `Article_Category_ID` INT,
    `Article_Status` INT,
    `Language_ID` INT,
    `User_ID` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `article` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `article_category`;
CREATE TABLE `article_category` (
    `Article_Category_ID` INT NOT NULL AUTO_INCREMENT,
    `Article_Category_Name` VARCHAR(255),
    `Article_Category_Images` TEXT,
    `AltText` VARCHAR(255),
    `User_ID` INT,
    `Article_Category_Status` INT,
    PRIMARY KEY (`Article_Category_ID`)
) ENGINE=InnoDB;
ALTER TABLE `article_category` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `languages`;
CREATE TABLE `languages` (
    `Language_ID` INT NOT NULL AUTO_INCREMENT,
    `Language` VARCHAR(100) NOT NULL,
    `Prefix` VARCHAR(10) NOT NULL,
    PRIMARY KEY (`Language_ID`)
) ENGINE=InnoDB;
ALTER TABLE `languages` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `article_c_relatives`;
CREATE TABLE `article_c_relatives` (
    `article_c_relatives_ID` INT AUTO_INCREMENT,
    `AC_Ref_Key` INT,
    `User_ID` INT,
    `AC_ID` INT,
    `Language_ID` INT,
    PRIMARY KEY (`article_c_relatives_ID`)
) ENGINE=InnoDB;
ALTER TABLE `article_c_relatives` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `article_relatives`;
CREATE TABLE `article_relatives` (
    `article_relatives_ID` INT AUTO_INCREMENT,
    `A_Ref_Key` INT,
    `User_ID` INT,
    `A_ID` INT,
    `Language_ID` INT,
    PRIMARY KEY (`article_relatives_ID`)
) ENGINE=InnoDB;
ALTER TABLE `article_relatives` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `Stuff`;
CREATE TABLE `Stuff` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Username` VARCHAR(255),
    `Password` VARCHAR(255),
    `Email` VARCHAR(255),
    `Firstname` VARCHAR(255),
    `Lastname` VARCHAR(255),
    `RolID` INT,
    `LanguageID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `Stuff` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `Rol`;
CREATE TABLE `Rol` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Rol` VARCHAR(255),
    `ActionIDs` VARCHAR(255),
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `Rol` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `Actions`;
CREATE TABLE `Actions` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Action` VARCHAR(255),
    `ActionDir` VARCHAR(255),
    `ActionName` VARCHAR(255),
    `ActionGroup` INT,
    `ActionType` INT,
    `Img` VARCHAR(255),
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `Actions` AUTO_INCREMENT = 1;

INSERT INTO `Actions` (`Action`, `ActionDir`, `ActionName`, `ActionGroup`, `ActionType`, `Img`)
VALUES 
    ('team', 'team', 'Team', 1, 1, 'tema.png'),
    ('add_teammate', 'add-teammate', 'Add teammate', 1, 1, 'new-teammate.png'),
    ('edit_teammate', 'edit-teammate', 'Edit Teammate', 1, 2, 'edit-teammate.png'),    
    ('roles', 'roles', 'Roles', 2, 1, 'roles.png'),  
    ('add_role', 'add-role', 'Add Role', 2, 1, 'add-role.png'),
    ('edit_role', 'edit-role/', 'Edit Role', 2, 2, 'add-role.png'),
    ('article_categories', 'article-categories', 'Article Categories', 3, 1, 'article-categories.png'),    
    ('addPC', 'add-article-category', 'Add Article Category', 3, 1, 'add-article-category.png'),    
    ('add_p_c', 'add-article-category', 'Add Article Category', 3, 2, 'add-article-category.png'),    
    ('edit_product_category', 'edit-article-category', 'Edit Article Category', 3, 2, 'edit-article-category.png'),    
    ('edit_p_c', 'edit-article-category', 'Edit Article Category', 3, 2, 'edit-article-category.png'),    
    ('articles', 'articles', 'Articles', 4, 1, 'articles.png'),    
    ('pd', 'article/new', 'Add Article', 4, 1, 'add-article.png'),    
    ('add_pr', 'article/new', 'Add Article', 4, 2, 'add-article.png'),    
    ('pd', 'article/', 'Article', 4, 2, 'article.png'),    
    ('edit_pr_headers', 'edit_article_headers', 'Edit Article Headers', null, 2, 'edit-article-headers.png'),    
    ('submit_r_t', 'submit_reach_text', 'Article Content', null, 2, 'article-content.png'),    
    ('thumbnail', 'thumbnail/', 'Thumbnail', null, 2, 'thumbnail.png'),  
    ('edit_thumbnail', 'edit_thumbnail', 'Edit Thumbnail', null, 2, 'edit_thumbnail.png'),  
    ('publishA', 'publish', 'Publish', null, 2, 'publish.png') 
    ;

DROP TABLE IF EXISTS `buffer`;
CREATE TABLE `buffer` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `Email` VARCHAR(255),
    `Url` VARCHAR(255),
    `RoleID` INT,
    `Deadline` DATETIME,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `buffer` AUTO_INCREMENT = 1;

INSERT INTO `Stuff` (`Username`, `Password`, `Email`, `Firstname`, `Lastname`, `RolID`, `LanguageID`, `Status`)
VALUES 
    ('superuser', 'scrypt:32768:8:1$gA4uJNdnHmDVnE7E$5f5ab03f948509ea13d2807eb5f48f85b202e2d09bc99cb8476f26e1f8151b0ba3e0e5c5a85b4b351d628b0a1757c017e9e0ea52ad6802b1ebc644002024e64c', 'test@test.com', 'John', 'Smith', 1, 2, 1),
    ('user2', 'scrypt:32768:8:1$gA4uJNdnHmDVnE7E$5f5ab03f948509ea13d2807eb5f48f85b202e2d09bc99cb8476f26e1f8151b0ba3e0e5c5a85b4b351d628b0a1757c017e9e0ea52ad6802b1ebc644002024e64c', 'user2@test.com', 'Second', 'User', 2, 2, 1);

INSERT INTO `Rol` (`Rol`, `ActionIDs`, `Status`)
VALUES ('superuser', '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15', 1);

-- If ActionType = 1 show on dushboard, 2 => actions with POST requests
INSERT INTO `Actions` (`Action`, `ActionDir`, `ActionName`, `ActionGroup`, `ActionType`, `Img`)
VALUES 
    ('team', 'team', 'Team', 1, 1, 'tema.png'),
    ('add_teammate', 'add-teammate', 'Add teammate', 1, 1, 'new-teammate.png'),
    ('edit_teammate', 'edit-teammate', 'Edit Teammate', 1, 2, 'edit-teammate.png'),    
    ('roles', 'roles', 'Roles', 2, 1, 'roles.png'),  
    ('add_role', 'add-role', 'Add Role', 2, 1, 'add-role.png'),
    ('edit_role', 'edit-role/', 'Edit Role', 2, 2, 'add-role.png'),
    ('article_categories', 'article-categories', 'Article Categories', 3, 1, 'article-categories.png'),    
    ('addPC', 'add-article-category', 'Add Article Category', 3, 1, 'add-article-category.png'),    
    ('add_p_c', 'add-article-category', 'Add Article Category', 3, 2, 'add-article-category.png'),    
    ('edit_product_category', 'edit-article-category', 'Edit Article Category', 3, 2, 'edit-article-category.png'),    
    ('articles', 'articles', 'Articles', 4, 1, 'articles.png'),    
    ('pd', 'article/new', 'Add Article', 4, 1, 'add-article.png'),    
    ('add_pr', 'article/new', 'Add Article', 4, 2, 'add-article.png'),    
    ('pd', 'article/', 'Article', 4, 2, 'article.png'),    
    ('edit_pr_headers', 'edit_article_headers', 'Edit Article Headers', null, 2, 'edit-article-headers.png'),    
    ('submit_r_t', 'submit_reach_text', 'Article Content', null, 2, 'article-content.png'),    
    ('thumbnail', 'thumbnail/', 'Thumbnail', null, 2, 'thumbnail.png'),  
    ('edit_thumbnail', 'edit_thumbnail', 'Edit Thumbnail', null, 2, 'edit_thumbnail.png'),  
    ('publishA', 'publish', 'Publish', null, 2, 'publish.png') 
    ;


INSERT INTO `languages` (`Language`, `Prefix`) VALUES
('Հայերեն', 'hy'),
('English', 'en'),
('中文 (普通话)', 'zh'),
('Español', 'es'),
('हिन्दी', 'hi'),
('বাংলা', 'bn'),
('Português', 'pt'),
('Русский', 'ru'),
('日本語', 'ja'),
('پنجابی (ਪੰਜਾਬੀ)', 'pa'),
('मराठी', 'mr'),
('తెలుగు', 'te'),
('吴语', 'wuu'),
('Türkçe', 'tr'),
('한국어', 'ko'),
('Français', 'fr'),
('Deutsch', 'de'),
('Tiếng Việt', 'vi'),
('தமிழ்', 'ta'),
('粤语 (廣東話)', 'yue'),
('اردو', 'ur'),
('ꦧꦱꦗꦮ', 'jv'),
('Italiano', 'it'),
('اللغة العربية المصرية', 'arz'),
('ગુજરાતી', 'gu'),
('فارسی', 'fa'),
('भोजपुरी', 'bho'),
('閩南語', 'nan'),
('客家话', 'hak'),
('晋语', 'cjy'),
('Hausa', 'ha')


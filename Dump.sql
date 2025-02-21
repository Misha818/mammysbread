-- Drop the existing database if it exists
DROP DATABASE IF EXISTS `db`;

-- Create the database again
CREATE DATABASE `db`
    DEFAULT CHARACTER SET utf8
    DEFAULT COLLATE utf8_general_ci;

-- Select the newly created database
USE `db`;

-- Drop tables if they exist and create them again
DROP TABLE IF EXISTS `product`;
CREATE TABLE `product` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `Title` VARCHAR(255),
    `Url` VARCHAR(255),
    `AltText` VARCHAR(255),
    `Thumbnail` VARCHAR(255),
    `Slides` TEXT,
    `ShortDescription` VARCHAR(255) NOT NULL,
    `LongDescription` TEXT NOT NULL,
    `Text` TEXT,
    `DatePublished` DATE,
    `DateModified` DATE,
    `Order` INT NOT NULL,
    `Product_Category_ID` INT,
    `Product_Status` INT,
    `Language_ID` INT,
    `User_ID` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `product` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `product_type`;
CREATE TABLE `product_type` (
    `ID` INT AUTO_INCREMENT,
    `Price` INT,
    `Title` VARCHAR(255),
    `Description` TEXT,
    `Order` INT,
    `User_ID` INT,
    `Product_ID` INT,
    `spsID` INT,
    -- `Slides` TEXT,
    -- `Language_ID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `product_type` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `product_category`;
CREATE TABLE `product_category` (
    `Product_Category_ID` INT NOT NULL AUTO_INCREMENT,
    `Product_Category_Name` VARCHAR(255),
    `Product_Category_Images` TEXT,
    `AltText` VARCHAR(255),
    `User_ID` INT,
    `spsID` INT,
    `Product_Category_Status` INT,
    PRIMARY KEY (`Product_Category_ID`)
) ENGINE=InnoDB;
ALTER TABLE `product_category` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `product_c_relatives`;
CREATE TABLE `product_c_relatives` (
    `product_c_relatives_ID` INT AUTO_INCREMENT,
    `PC_Ref_Key` INT,
    `User_ID` INT,
    `PC_ID` INT,
    `Language_ID` INT,
    PRIMARY KEY (`product_c_relatives_ID`)
) ENGINE=InnoDB;
ALTER TABLE `product_c_relatives` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `product_relatives`;
CREATE TABLE `product_relatives` (
    `product_relatives_ID` INT AUTO_INCREMENT,
    `P_Ref_Key` INT,
    `User_ID` INT,
    `P_ID` INT,
    `Language_ID` INT,
    PRIMARY KEY (`product_relatives_ID`)
) ENGINE=InnoDB;
ALTER TABLE `product_relatives` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `sub_product`;
CREATE TABLE `sub_product` (
    `ID` INT AUTO_INCREMENT,
    `Price` INT,
    `Title` VARCHAR(255),
    `Order` INT,
    `Product_ID` INT,
    `User_ID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `sub_product` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `sp_relatives`;
CREATE TABLE `sp_relatives` (
    `ID` INT AUTO_INCREMENT,
    `Ref_Key` INT,
    `User_ID` INT,
    `SP_ID` INT,
    `Order` INT,
    `Language_ID` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `sp_relatives` AUTO_INCREMENT = 1;

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

DROP TABLE IF EXISTS `languages`;
CREATE TABLE `languages` (
    `Language_ID` INT NOT NULL AUTO_INCREMENT,
    `Language` VARCHAR(100) NOT NULL,
    `Prefix` VARCHAR(10) NOT NULL,
    PRIMARY KEY (`Language_ID`)
) ENGINE=InnoDB;
ALTER TABLE `languages` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `stuff`;
CREATE TABLE `stuff` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Username` VARCHAR(255),
    `Password` VARCHAR(255),
    `Email` VARCHAR(255),
    `Firstname` VARCHAR(255),
    `Lastname` VARCHAR(255),
    `Avatar` TEXT,
    `AltText` VARCHAR(255),
    `RolID` INT,
    `LanguageID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `stuff` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `rol`;
CREATE TABLE `rol` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Rol` VARCHAR(255),
    `ActionIDs` VARCHAR(255),
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `rol` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `actions`;
CREATE TABLE `actions` (
    `ID` INT AUTO_INCREMENT NOT NULL,
    `Action` VARCHAR(255),
    `ActionDir` VARCHAR(255),
    `ActionName` VARCHAR(255),
    `ActionGroup` INT,
    `ActionType` INT,
    `Img` VARCHAR(255),
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `actions` AUTO_INCREMENT = 1;

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

DROP TABLE IF EXISTS `slider`;
CREATE TABLE `slider` (
    `ID` INT NOT NULL AUTO_INCREMENT,
    `ProductID` INT,
    `Order` INT,
    `Name` VARCHAR(255),
    `AltText` VARCHAR(255),
    `Type` INT, -- (1 => Product, 2 => PtoductType (subproduct) )
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `slider` AUTO_INCREMENT = 1;


DROP TABLE IF EXISTS `sub_product_specification`;
CREATE TABLE `sub_product_specification` (
    `ID` INT AUTO_INCREMENT,
    `Name` VARCHAR(255),
    `User_ID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `sub_product_specification` AUTO_INCREMENT = 1;

DROP TABLE IF EXISTS `sub_product_specifications`;
CREATE TABLE `sub_product_specifications` (
    `ID` INT AUTO_INCREMENT,
    `Name` VARCHAR(255),
    `spsID` INT,
    `Order` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `sub_product_specifications` AUTO_INCREMENT = 1;



DROP TABLE IF EXISTS `sps_relatives`;
CREATE TABLE `sps_relatives` (
    `ID` INT AUTO_INCREMENT,
    `Ref_Key` INT,
    `User_ID` INT,
    `SPS_ID` INT,
    `Language_ID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `sps_relatives` AUTO_INCREMENT = 1;


DROP TABLE IF EXISTS `spss_relatives`;
CREATE TABLE `spss_relatives` (
    `ID` INT AUTO_INCREMENT,
    `Ref_Key` INT,
    `SPSS_ID` INT,
    `User_ID` INT,
    `Language_ID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `spss_relatives` AUTO_INCREMENT = 1;


DROP TABLE IF EXISTS `product_type_details`;
CREATE TABLE `product_type_details` (
    `ID` INT AUTO_INCREMENT,
    `Text` VARCHAR(255),
    `spssID` INT,
    `productTypeID` INT,
    -- `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `product_type_details` AUTO_INCREMENT = 1;


DROP TABLE IF EXISTS `quantity`;
CREATE TABLE `quantity` (
    `ID` INT AUTO_INCREMENT,
    `productTypeID` INT,
    `storeID` INT,
    `userID` INT,
    `Quantity` INT,
    `maxQuantity` INT,
    `productionDate` DATE,
    `expDate` DATE,
    `addDate` DATE,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `quantity` AUTO_INCREMENT = 1;


DROP TABLE IF EXISTS `store`;
CREATE TABLE `store` (
    `ID` INT AUTO_INCREMENT,
    `Name` VARCHAR(255),
    `Address` VARCHAR(255),
    `userID` INT,
    `Status` INT,
    PRIMARY KEY (`ID`)
) ENGINE=InnoDB;
ALTER TABLE `store` AUTO_INCREMENT = 1;

INSERT INTO `stuff` (`Username`, `Password`, `Email`, `Firstname`, `Lastname`, `RolID`, `LanguageID`, `Status`)
VALUES 
    ('superuser', 'scrypt:32768:8:1$gA4uJNdnHmDVnE7E$5f5ab03f948509ea13d2807eb5f48f85b202e2d09bc99cb8476f26e1f8151b0ba3e0e5c5a85b4b351d628b0a1757c017e9e0ea52ad6802b1ebc644002024e64c', 'test@test.com', 'John', 'Smith', 1, 2, 1),
    ('user2', 'scrypt:32768:8:1$gA4uJNdnHmDVnE7E$5f5ab03f948509ea13d2807eb5f48f85b202e2d09bc99cb8476f26e1f8151b0ba3e0e5c5a85b4b351d628b0a1757c017e9e0ea52ad6802b1ebc644002024e64c', 'user2@test.com', 'Second', 'User', 2, 2, 1);

INSERT INTO `rol` (`Rol`, `ActionIDs`, `Status`)
VALUES ('superuser', '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60', 1);

-- If ActionType = 1 show on dushboard, 2 => actions with POST requests.
INSERT INTO `actions` (`Action`, `ActionDir`, `ActionName`, `ActionGroup`, `ActionType`, `Img`)
VALUES 
    ('products', 'products', 'Products', 1, 1, 'products.png'),    
    ('pd', 'product/new', 'Add Product', 1, 1, 'add-products.png'),    
    ('add_pr', 'add_product', 'Add Product', 1, 2, 'add-product.png'),    
    ('pd', 'product/', 'Product Page', 1, 2, 'product.png'), 

    ('product_categories', 'product-categories', 'Product Categories', 2, 1, 'product-categories.png'),    
    ('addPC', 'add-product-category', 'Add Product Category', 2, 1, 'add-product-category.png'),    
    ('add_p_c', 'add_product_category', 'Add Product Category', 2, 2, 'add-product-category.png'),    
    ('edit_product_category', 'edit-product-category/', 'Edit Product Category', 2, 2, 'edit-product-category.png'),    
    ('edit_p_c', 'edit_product_category', 'Edit Product Category', 2, 2, 'edit-product-category.png'),    
    
    ('pt_specifications', 'pt-specifications', 'Product Type Specifications', 3, 1, 'pt-specifications.png'),  
    ('add_sps_view', 'add-sps', 'Add Product Type Specification', 3, 1, 'add-pt-specifications.png'),  
    ('add_sps', 'add_sps', 'Add Product Type Specification', 3, 2, 'add-pt-specifications.png'),  
    ('edit_pts_view', 'edit-pts/', 'Edit Product Type Specification', 3, 2, 'edit-pt-specifications.png'),  
    ('edit_pts', 'edit-pts', 'Edit Product Type Specification', 3, 2, 'edit-pt-specifications.png'),  
    
    ('store', 'store', 'Store', 4, 1, 'store.png'),    
    ('add_to_store', 'add-to-store', 'Add To Store', 4, 1, 'add-to-store.png'),    
    ('add_to_store', 'add-to-store/', 'Add To Store', 4, 2, 'add-to-store.png'),    
    ('add_to_store', 'add-to-store', 'Add To Store', 4, 2, 'add-to-store.png'),    
    ('edit_store', 'edit-store', 'Edit Store', 4, 2, 'edit-store.png'),  
    ('edit_store', 'edit-store/', 'Edit Store', 4, 2, 'edit-store.png'),  

    ('edit_pr_headers', 'edit_product_headers', 'Edit Product Headers', 5, 3, 'edit-product-headers.png'),    
    ('submit_r_t', 'submit_reach_text', 'Product Content', 5, 3, 'product-content.png'),    
    ('pr_thumbnail', 'pr-thumbnail/', 'Thumbnail', 5, 3, 'thumbnail.png'),  
    ('edit_pr_thumbnail', 'edit_pr_thumbnail', 'Edit Thumbnail', 5, 3, 'edit_thumbnail.png'),  
    ('publishP', 'publish-product', 'Publish Product', 5, 3, 'publish-product.png'),

    ('team', 'team', 'Team', 6, 1, 'tema.png'),
    ('add_teammate', 'add-teammate', 'Add teammate', 6, 1, 'new-teammate.png'),
    ('teampage', 'team/', 'Team', 6, 2, 'tema.png'),
    ('edit_teammate', 'edit-teammate/', 'Edit Teammate', 6, 2, 'edit-teammate.png'),

    ('roles', 'roles', 'Roles', 7, 1, 'roles.png'),  
    ('add_role', 'add-role', 'Add Role', 7, 1, 'add-role.png'),
    ('edit_role', 'edit-role/', 'Edit Role', 7, 2, 'add-role.png'), 

    ('stuff', 'stuff', 'Stuff', 8, 2, 'stuff.png'), 

    ('change_pr_order', 'changeprorder', 'Change Product Order', 9, 2, 'changeprorder.png'), 
    ('add_price', 'add-price/', 'Add Price', 9, 2, 'changeprorder.png'), 
    ('add_price', 'add-price/', 'Add Price', 9, 2, 'changeprorder.png'), 
    ('upload_slides', 'upload_slides', 'Add Price, Upload Slides', 9, 2, 'upload-slides.png'), 
    ('edit_price', 'edit-price/', 'Edit Price', 9, 2, 'editprice.png'), 
    ('editprice', 'editprice', 'Edit Price', 9, 2, 'editprice.png'), 
    ('get_product_types_quantity', 'get-product-types-quantity', 'Get Product Types Quantity', 9, 2, 'get_product_types_quantity.png'), 
    ('get_specifications', 'get-spacifications', 'Get Spacifications', 9, 2, 'get-spacifications.png'), 
    ('get_product_types', 'get-product-types', 'Get Product Types', 9, 2, 'get-product-types.png'), 
    ('change_type_order', 'change-type-order', 'Get Type Order', 9, 2, 'change-type-order.png'), 
    ('chaneg_pt_status', 'chaneg-pt-status', 'Change Product Type Status', 9, 2, 'change-type-order.png'), 
    ('submit_product_t', 'submit_product_text', 'Submit Product Text', 9, 2, 'change-type-order.png'), 
    ('get_slides', 'get_slides', 'Get Slides', 9, 2, 'get_slides.png') 
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
;

INSERT INTO `store` (`Name`, `Address`, `userID`, `Status`) Values('Main', 'Main str.', 1, 1);



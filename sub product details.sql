-- sub product details
USE `db`;

-- insert into sub_product_specifications (`Name`,`spsID`, `Order`, `Status`)
-- VALUES
-- ('Weight', 1, 0, 1),
-- ('Color', 1, 1, 1),
-- ('Ingredients', 1, 2, 1)

-- insert into sub_product_details (`Text`,`spssID`, `subProductID`, `Status`)
-- VALUES
-- ('900gr', 1, 15, 1),
-- ('Brown', 2, 15, 1),
-- ('Flour, water, soult, sourdoug', 3, 15, 1)


SELECT 
    `sub_product_details`.`ID` AS `spdID`,
    `sub_product_specifications`.`Name`,
    `sub_product_details`.`Text`,
    `sub_product_specifications`.`Order`,
    `sub_product_specification`.`Name` AS `spsName`
FROM `sub_product_details`
    LEFT JOIN `sub_product_specifications` ON `sub_product_specifications`.`ID` = `sub_product_details`.`spssID`
    LEFT JOIN `sub_product_specification` ON `sub_product_specification`.`ID` = `sub_product_specifications`.`spsID`
WHERE `sub_product_details`.`Status` = 1
    AND `sub_product_details`.`subProductID` = 15


-- DROP TABLE IF EXISTS `sub_product_specification`;
-- CREATE TABLE `sub_product_specification` (
--     `ID` INT AUTO_INCREMENT,
--     `Name` VARCHAR(255),
--     `Status` INT,
--     PRIMARY KEY (`ID`)
-- ) ENGINE=InnoDB;
-- ALTER TABLE `sub_product_specification` AUTO_INCREMENT = 1;

-- DROP TABLE IF EXISTS `sub_product_specifications`;
-- CREATE TABLE `sub_product_specifications` (
--     `ID` INT AUTO_INCREMENT,
--     `Name` VARCHAR(255),
--     `spsID` INT,
--     `Order` INT,
--     `Status` INT,
--     PRIMARY KEY (`ID`)
-- ) ENGINE=InnoDB;
-- ALTER TABLE `sub_product_specifications` AUTO_INCREMENT = 1;

-- DROP TABLE IF EXISTS `sub_product_details`;
-- CREATE TABLE `sub_product_details` (
--     `ID` INT AUTO_INCREMENT,
--     `Text` VARCHAR(255),
--     `spssID` INT,
--     `subProductID` INT,
--     `Status` INT,
--     PRIMARY KEY (`ID`)
-- ) ENGINE=InnoDB;
-- ALTER TABLE `sub_product_details` AUTO_INCREMENT = 1;
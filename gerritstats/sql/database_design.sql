-- MySQL dump 10.13  Distrib 5.5.25a, for osx10.7 (i386)
--
-- Host: localhost    Database: reviewdb
-- ------------------------------------------------------
-- Server version	5.5.25a

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts` (
  `registered_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `full_name` varchar(255) DEFAULT NULL,
  `preferred_email` varchar(255) DEFAULT NULL,
  `contact_filed_on` timestamp NULL DEFAULT NULL,
  `maximum_page_size` smallint(6) NOT NULL DEFAULT '0',
  `show_site_header` char(1) NOT NULL DEFAULT 'N',
  `use_flash_clipboard` char(1) NOT NULL DEFAULT 'N',
  `download_url` varchar(20) DEFAULT NULL,
  `download_command` varchar(20) DEFAULT NULL,
  `copy_self_on_email` char(1) NOT NULL DEFAULT 'N',
  `date_format` varchar(10) DEFAULT NULL,
  `time_format` varchar(10) DEFAULT NULL,
  `display_patch_sets_in_reverse_order` char(1) NOT NULL DEFAULT 'N',
  `display_person_name_in_review_category` char(1) NOT NULL DEFAULT 'N',
  `inactive` char(1) NOT NULL DEFAULT 'N',
  `account_id` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`account_id`),
  KEY `accounts_byPreferredEmail` (`preferred_email`),
  KEY `accounts_byFullName` (`full_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `changes`
--

DROP TABLE IF EXISTS `changes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changes` (
  `change_key` varchar(60) NOT NULL DEFAULT '',
  `created_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_updated_on` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `sort_key` varchar(16) NOT NULL DEFAULT '',
  `owner_account_id` int(11) NOT NULL DEFAULT '0',
  `dest_project_name` varchar(255) NOT NULL DEFAULT '',
  `dest_branch_name` varchar(255) NOT NULL DEFAULT '',
  `open` char(1) NOT NULL DEFAULT 'N',
  `status` char(1) NOT NULL DEFAULT '',
  `nbr_patch_sets` int(11) NOT NULL DEFAULT '0',
  `current_patch_set_id` int(11) NOT NULL DEFAULT '0',
  `subject` varchar(255) NOT NULL DEFAULT '',
  `topic` varchar(255) DEFAULT NULL,
  `row_version` int(11) NOT NULL DEFAULT '0',
  `change_id` int(11) NOT NULL DEFAULT '0',
  `last_sha1_merge_tested` varchar(40) CHARACTER SET utf8 COLLATE utf8_bin DEFAULT NULL,
  `mergeable` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`change_id`),
  KEY `changes_byOwnerOpen` (`open`,`owner_account_id`,`created_on`,`change_id`),
  KEY `changes_byOwnerClosed` (`open`,`owner_account_id`,`last_updated_on`),
  KEY `changes_submitted` (`status`,`dest_project_name`,`dest_branch_name`,`last_updated_on`),
  KEY `changes_allOpen` (`open`,`sort_key`),
  KEY `changes_byProjectOpen` (`open`,`dest_project_name`,`sort_key`),
  KEY `changes_byProject` (`dest_project_name`),
  KEY `changes_allClosed` (`open`,`status`,`sort_key`),
  KEY `changes_key` (`change_key`),
  KEY `changes_byBranchClosed` (`status`,`dest_project_name`,`dest_branch_name`,`sort_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patch_set_approvals`
--

DROP TABLE IF EXISTS `patch_set_approvals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `patch_set_approvals` (
  `value` smallint(6) NOT NULL DEFAULT '0',
  `granted` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `change_open` char(1) NOT NULL DEFAULT 'N',
  `change_sort_key` varchar(16) DEFAULT NULL,
  `change_id` int(11) NOT NULL DEFAULT '0',
  `patch_set_id` int(11) NOT NULL DEFAULT '0',
  `account_id` int(11) NOT NULL DEFAULT '0',
  `category_id` varchar(4) NOT NULL DEFAULT '',
  PRIMARY KEY (`change_id`,`patch_set_id`,`account_id`,`category_id`),
  KEY `patch_set_approvals_openByUser` (`change_open`,`account_id`),
  KEY `patch_set_approvals_closedByUser` (`change_open`,`account_id`,`change_sort_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `patch_sets`
--

DROP TABLE IF EXISTS `patch_sets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `patch_sets` (
  `revision` varchar(40) DEFAULT NULL,
  `uploader_account_id` int(11) NOT NULL DEFAULT '0',
  `created_on` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `change_id` int(11) NOT NULL DEFAULT '0',
  `patch_set_id` int(11) NOT NULL DEFAULT '0',
  `draft` char(1) NOT NULL DEFAULT 'N',
  PRIMARY KEY (`change_id`,`patch_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-08-14 15:30:54

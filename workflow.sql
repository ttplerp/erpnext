-- MariaDB dump 10.19  Distrib 10.6.12-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: _4721ca5b028e4b6e
-- ------------------------------------------------------
-- Server version	10.6.12-MariaDB-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tabWorkflow`
--

DROP TABLE IF EXISTS `tabWorkflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tabWorkflow` (
  `name` varchar(140) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(140) DEFAULT NULL,
  `owner` varchar(140) DEFAULT NULL,
  `docstatus` int(1) NOT NULL DEFAULT 0,
  `idx` int(8) NOT NULL DEFAULT 0,
  `workflow_name` varchar(140) DEFAULT NULL,
  `document_type` varchar(140) DEFAULT NULL,
  `is_active` int(1) NOT NULL DEFAULT 0,
  `override_status` int(1) NOT NULL DEFAULT 0,
  `send_email_alert` int(1) NOT NULL DEFAULT 1,
  `workflow_state_field` varchar(140) DEFAULT 'workflow_state',
  `_user_tags` text DEFAULT NULL,
  `_comments` text DEFAULT NULL,
  `_assign` text DEFAULT NULL,
  `_liked_by` text DEFAULT NULL,
  PRIMARY KEY (`name`),
  UNIQUE KEY `workflow_name` (`workflow_name`),
  KEY `modified` (`modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tabWorkflow`
--

LOCK TABLES `tabWorkflow` WRITE;
/*!40000 ALTER TABLE `tabWorkflow` DISABLE KEYS */;
INSERT INTO `tabWorkflow` VALUES ('Employee Advance','2023-06-27 10:52:49.544388','2023-07-27 11:11:35.096734','Administrator','Administrator',0,0,'Employee Advance','Employee Advance',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Employee Transfer Request','2023-07-31 16:36:24.051279','2023-08-01 15:14:16.126065','Administrator','Administrator',0,0,'Employee Transfer Request','Employee Transfer Request',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Leave Application','2023-06-17 22:06:38.821420','2023-07-27 14:19:37.958198','Administrator','Administrator',0,0,'Leave Application','Leave Application',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Leave Encashment','2023-07-27 15:36:36.232284','2023-08-02 11:00:20.279600','dechen.lhaden@thimphutechpark.bt','deki.wangmo@thimphutechpark.bt',0,0,'Leave Encashment','Leave Encashment',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Material Request','2023-06-07 14:16:29.818232','2023-08-02 14:09:30.114698','Administrator','tshering.lham@thimphutechpark.bt',0,0,'Material Request','Material Request',1,0,0,'workflow_state',NULL,NULL,NULL,NULL),('Overtime Application','2023-06-27 13:09:57.201085','2023-06-27 13:16:27.588559','Administrator','Administrator',0,0,'Overtime Application','Overtime Application',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Repair And Services','2023-06-16 15:41:54.996637','2023-08-01 14:50:28.535222','Administrator','tshering.lham@thimphutechpark.bt',0,0,'Repair And Services','Repair And Services',1,0,1,'workflow_state',NULL,NULL,NULL,NULL),('Travel Request','2023-06-14 14:56:53.433339','2023-06-27 19:04:39.049057','Administrator','Administrator',0,0,'Travel Request','Travel Request',1,0,0,'workflow_state',NULL,NULL,NULL,NULL),('Vehicle Request','2023-07-25 13:03:20.186559','2023-07-25 13:03:20.186559','tshering.lham@thimphutechpark.bt','tshering.lham@thimphutechpark.bt',0,0,'Vehicle Request','Repair And Services',0,0,1,'workflow_state',NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `tabWorkflow` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-08-02 14:51:02

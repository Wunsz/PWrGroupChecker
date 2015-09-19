CREATE TABLE `courses_types` (
  `id_course_type` VARCHAR(2) NOT NULL,
  `type` VARCHAR(45) NOT NULL,
  `polish` VARCHAR(45) NOT NULL,
  CONSTRAINT `PK__courses_types` PRIMARY KEY (`id_course_type`)
);

CREATE TABLE `courses` (
  `id_course` VARCHAR(16) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `type` VARCHAR(2) NOT NULL,
  CONSTRAINT `PK__courses` PRIMARY KEY (`id_course`),
  INDEX `IDX__courses__id_course_type` (`type` ASC),
  CONSTRAINT `FK__courses__courses_types`
  FOREIGN KEY (`type`)  REFERENCES `courses_types` (`id_course_type`)
    ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE `groups` (
  `id_group` VARCHAR(16) NOT NULL,
  `id_course` VARCHAR(16) NOT NULL,
  `capacity` INT NOT NULL,
  `assigned` INT NOT NULL,
  `building` VARCHAR(16) NULL,
  `room` VARCHAR(16) NULL,
  `day` SMALLINT(1) NULL,
  `start` TIME,
  `end` TIME,
  `lecturer` VARCHAR(255) NULL,
  `updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `last_change` TIMESTAMP NULL,
  CONSTRAINT `PK__groups` PRIMARY KEY (`id_group`),
  INDEX `IDX__groups__id_course` (`id_course` ASC),
  CONSTRAINT `FK__groups__courses`
  FOREIGN KEY (`id_course`) REFERENCES `courses` (`id_course`)
    ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE TABLE `groups_logs` (
  `id_group_log` INT NOT NULL AUTO_INCREMENT,
  `id_group` VARCHAR(2) NOT NULL,
  `assigned` INT NOT NULL,
  `check_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `PK__groups_logs` PRIMARY KEY (`id_group_log`),
  INDEX `IDX__groups_logs__id_group` (`id_group` ASC),
  INDEX `IDX__groups_logs__check_time` (`check_time` ASC),
  CONSTRAINT `FK__groups_logs__groups`
  FOREIGN KEY (`id_group`) REFERENCES `groups` (`id_group`)
    ON DELETE RESTRICT ON UPDATE RESTRICT
);

INSERT INTO `courses_types` (`type`, `polish`, `id_course_type`) VALUES ('Lecture', 'Wykład', 'W');
INSERT INTO `courses_types` (`type`, `polish`, `id_course_type`) VALUES ('Laborartory', 'Laboratorium', 'L');
INSERT INTO `courses_types` (`type`, `polish`, `id_course_type`) VALUES ('Excercises', 'Ćwiczenia', 'C');
INSERT INTO `courses_types` (`type`, `polish`, `id_course_type`) VALUES ('Seminary', 'Seminarium', 'S');
INSERT INTO `courses_types` (`type`, `polish`, `id_course_type`) VALUES ('Diploma', 'Dyplom', 'D');
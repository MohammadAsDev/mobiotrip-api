USE `mobiotrip`;

CREATE VIEW riders AS (
    SELECT 
        `email_or_phone_number` ,
        `password` , 
        `first_name`,
        `last_name`,
        `birth_date`,
        `gender`
    FROM `mobiotrip_users` WHERE `user_type` = 0
);

CREATE VIEW drivers AS (
    SELECT 
        `email_or_phone_number` ,
        `password` , 
        `first_name`,
        `last_name`,
        `birth_date`,
        `gender`
    FROM `mobiotrip_users` WHERE `user_type` = 1
);

CREATE VIEW staffs AS (
    SELECT 
        `email_or_phone_number` ,
        `password` , 
        `first_name`,
        `last_name`,
        `birth_date`,
        `gender`
    FROM `mobiotrip_users` WHERE `user_type` = 2
);

CREATE VIEW publishers AS (
    SELECT 
        `email_or_phone_number` ,
        `password` , 
        `first_name`,
        `last_name`,
        `birth_date`,
        `gender`
    FROM `mobiotrip_users` WHERE `user_type` = 3
);
USE `mobiotrip`;
CREATE OR REPLACE VIEW `driver_vehicle` AS (
    SELECT 
    `mobiotrip_users`.`id`,
    `email_or_phone_number` , 
    `first_name` ,
    `last_name` ,
    `birth_date` ,
    `gender` , 
    `vehicle_number` , 
    `vehicle_color`,
    `vehicle_governorate`,
    `vehicle_type`,
    `seats_number`
    FROM `mobiotrip_users` JOIN `vehicles_manager_vehicle` ON `owner_id` = `mobiotrip_users`.`id`
)
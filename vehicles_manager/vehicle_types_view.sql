USE `mobiotrip`;
CREATE OR REPLACE VIEW `personal_vehicles` AS (
    SELECT 
    `vehicle_number` , 
    `vehicle_color`,
    `vehicle_governorate`,
    `seats_number`
    FROM `vehicles_manager_vehicle` WHERE `vehicle_type` = 1 
);
CREATE OR REPLACE VIEW `public_vehicles` AS (
    SELECT 
    `vehicle_number` , 
    `vehicle_color`,
    `vehicle_governorate`,
    `seats_number`
    FROM `vehicles_manager_vehicle` WHERE `vehicle_type` = 0 
);
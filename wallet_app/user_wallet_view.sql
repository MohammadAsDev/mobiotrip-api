USE `mobiotrip`;

CREATE OR REPLACE VIEW user_wallet_view AS (
    SELECT 
        `owner_id`,
        `email_or_phone_number` AS `phone_number`,
        `password` , 
        `first_name`,
        `last_name`,
        `birth_date`,
        `gender`
        `balance` , 
        `pin_code` , 
        `wallet_uuid`,
        `wallet_app_wallet`.`created_at`
    FROM `wallet_app_wallet` JOIN `mobiotrip_users`  ON owner_id = mobiotrip_users.id  
);
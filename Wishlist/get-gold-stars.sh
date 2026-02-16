#!/bin/sh

TMC_K2_MONTHLY=170223
TMC_34_MONTHLY=170226
TMC_56_MONTHLY=170230
TMC_K2_YEARLY=170210
TMC_34_YEARLY=170219
TMC_56_YEARLY=170220
TMC_K6_MONTHLY=170221
TMC_K6_YEARLY=170209

TMC_K6_FT=729842




## Get the maximum number of Unlocks (points) a Sparkler can have.
##
function get_max_unlocks {
	mysql 	-u sparklersclub -pWaterSkiSC12 			\
			-h dss-production-v2.coouoxfzx0u1.us-east-1.rds.amazonaws.com	\
			sparklersclub	\
			--skip-column-names 					\
			--batch							\
			--raw							\
            --skip-column-names                             \
<<EOM
    SELECT  COUNT(rules.trigger_points)
    FROM    wp_7_wlpoints_point_rules as rules
    WHERE   rules.trigger_slug = 'wlm_add_to_membership'
    AND     rules.id != 107
    AND     rules.id != 65
    AND     rules.id != 66
    AND     rules.id != 67
    AND     rules.id != 68
    AND     rules.id != 69
    AND     rules.id != 70
    AND     rules.id != 71
    AND     rules.id != 72
    AND     rules.id != 73
    AND     rules.id != 74
    AND     rules.id != 75
    AND     rules.id != 104
    AND     rules.id != 5
    AND     rules.id != 6
    AND     rules.id != 10
    AND     rules.id != 16
    AND     rules.id != 21
    AND     rules.id != 25
    AND     rules.id != 31
    AND     rules.id != 39
    AND     rules.id != 48
    ;
EOM
}

## Set the MAX_UNLOCKS global
##
MAX_UNLOCKS=$(get_max_unlocks)


## Get points transactions with date, email, points, and status
function get_gold_stars {
	mysql 	-u sparklersclub -pWaterSkiSC12 			\
			-h dss-production-v2.coouoxfzx0u1.us-east-1.rds.amazonaws.com	\
			sparklersclub	\
			--skip-column-names 					\
			--batch							\
			--raw							\
<<EOM
SELECT
            LCASE(users.user_email)
    FROM    wp_posts as posts
    JOIN    wp_postmeta as postmeta
        ON      posts.post_type     = 'shop_subscription'
        AND (
                posts.post_status   = 'wc-active'
            OR  posts.post_status   = 'wc-on-hold'
            OR  posts.post_status   = 'wc-pending-cancel'
        )
        AND     postmeta.post_id    = posts.ID
        AND     postmeta.meta_key   = '_customer_user'
    JOIN    wp_woocommerce_order_items as order_items
        ON      order_items.order_id = posts.ID
    JOIN    wp_woocommerce_order_itemmeta as order_itemmeta
        ON      order_itemmeta.meta_key = '_product_id'
        AND     order_items.order_item_id = order_itemmeta.order_item_id
        AND (
                order_itemmeta.meta_value = '$TMC_K2_MONTHLY'
            OR  order_itemmeta.meta_value = '$TMC_34_MONTHLY'
            OR  order_itemmeta.meta_value = '$TMC_56_MONTHLY'
            OR  order_itemmeta.meta_value = '$TMC_K6_MONTHLY'
            OR  order_itemmeta.meta_value = '$TMC_K2_YEARLY'
            OR  order_itemmeta.meta_value = '$TMC_34_YEARLY'
            OR  order_itemmeta.meta_value = '$TMC_56_YEARLY'
            OR  order_itemmeta.meta_value = '$TMC_K6_YEARLY'
            OR  order_itemmeta.meta_value = '$TMC_K6_FT'
        )
    JOIN    wp_users as users
        ON      users.ID            = postmeta.meta_value

JOIN (
    SELECT
            COUNT(DISTINCT(p3.module_id)) as unlocked,
            p3.user_id as ID
    FROM    wp_7_wlpoints_user_points as p3
    WHERE   p3.points_flag = 'redeemed'
    AND     p3.module_id != 107
    AND     p3.module_id != 65
    AND     p3.module_id != 66
    AND     p3.module_id != 67
    AND     p3.module_id != 68
    AND     p3.module_id != 69
    AND     p3.module_id != 70
    AND     p3.module_id != 71
    AND     p3.module_id != 72
    AND     p3.module_id != 73
    AND     p3.module_id != 74
    AND     p3.module_id != 75
    AND     p3.module_id != 104
    AND     p3.module_id != 5
    AND     p3.module_id != 6
    AND     p3.module_id != 10
    AND     p3.module_id != 16
    AND     p3.module_id != 21
    AND     p3.module_id != 25
    AND     p3.module_id != 31
    AND     p3.module_id != 39
    AND     p3.module_id != 48
    GROUP BY p3.user_id
) as t3

        ON t3.ID = users.ID
        AND t3.unlocked = $MAX_UNLOCKS
    ;


EOM
}

function format_as_csv {
	awk '
	BEGIN {
		FS = "\t"
		OFS = ","
		print "Email"
	}
	{
		# Get fields
		email = $1
	
		
		# Handle empty/null values
		if (email == "" || email == "NULL") email = ""
		
		
		# Properly escape quotes in fields (double any existing quotes)
		gsub(/"/, "\"\"", email)
		
		# Quote fields if they contain commas or quotes
		if (email ~ /[,"]/) {
			email = "\"" email "\""
		}
		
		print email
	}'
}


get_gold_stars      \
	| format_as_csv      \
	> gold-stars.csv

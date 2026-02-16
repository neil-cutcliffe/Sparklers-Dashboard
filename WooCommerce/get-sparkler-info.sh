#!/bin/sh


## Get subscription customers with their first subscription date, email, name, status, payment plan, and number of cancelled subscriptions
function get_sparkler_info {
	mysql 	-u sparklersclub -pWaterSkiSC12 			\
			-h dss-production-v2.coouoxfzx0u1.us-east-1.rds.amazonaws.com	\
			sparklersclub	\
			--skip-column-names 					\
			--batch							\
			--raw							\
<<EOM
	WITH subscription_data AS (
		SELECT
			users.ID AS user_id,
			LCASE(users.user_email) AS email,
			TRIM(CONCAT(
				COALESCE(first_name_meta.meta_value, ''),
				' ',
				COALESCE(last_name_meta.meta_value, '')
			)) AS name,
			posts.ID AS subscription_id,
			posts.post_date AS subscription_date,
			posts.post_status,
			billing_period_meta.meta_value AS billing_period,
			ROW_NUMBER() OVER (PARTITION BY users.ID ORDER BY posts.post_date ASC) AS first_sub_rank
		FROM	wp_users as users
		JOIN    wp_postmeta as postmeta
			ON      postmeta.meta_key   = '_customer_user'
			AND	    postmeta.meta_value = users.ID
		JOIN	wp_posts as posts
			ON	    posts.ID = postmeta.post_id
			AND	    posts.post_type		= 'shop_subscription'
			AND	    posts.post_status  != 'wc-pending'
		LEFT JOIN wp_usermeta as first_name_meta
			ON      first_name_meta.user_id = users.ID
			AND     first_name_meta.meta_key = 'first_name'
		LEFT JOIN wp_usermeta as last_name_meta
			ON      last_name_meta.user_id = users.ID
			AND     last_name_meta.meta_key = 'last_name'
		LEFT JOIN wp_postmeta as billing_period_meta
			ON      billing_period_meta.post_id = posts.ID
			AND     billing_period_meta.meta_key = '_billing_period'
	),
	customers_with_completed_orders AS (
		SELECT DISTINCT
			sd.user_id
		FROM subscription_data sd
		JOIN wp_posts subscription_post
			ON subscription_post.ID = sd.subscription_id
			AND subscription_post.post_parent > 0
		JOIN wp_posts parent_order
			ON parent_order.ID = subscription_post.post_parent
			AND parent_order.post_type = 'shop_order'
			AND parent_order.post_status = 'wc-completed'
	),
	first_subscription AS (
		SELECT
			user_id,
			DATE(subscription_date) AS first_subscription_date,
			email,
			name,
			post_status,
			billing_period
		FROM subscription_data
		WHERE first_sub_rank = 1
	),
	cancelled_counts AS (
		SELECT
			user_id,
			COUNT(*) AS cancelled_subscriptions
		FROM subscription_data
		WHERE post_status = 'wc-cancelled'
		GROUP BY user_id
	)
	SELECT
		fs.first_subscription_date AS Date,
		fs.email AS Email,
		fs.name AS Name,
		fs.post_status AS Status,
		fs.billing_period AS BillingPeriod,
		COALESCE(cc.cancelled_subscriptions, 0) AS CancelledCount
	FROM customers_with_completed_orders cwco
	JOIN first_subscription fs ON cwco.user_id = fs.user_id
	LEFT JOIN cancelled_counts cc ON cwco.user_id = cc.user_id
	ORDER BY fs.first_subscription_date ASC, fs.email ASC
	;
EOM
}

function format_as_csv {
	awk '
	BEGIN {
		FS = "\t"
		OFS = ","
		print "Date,Email,Name,Status,Payment Plan,Number of Cancels"
	}
	{
		# Get fields
		date = $1
		email = $2
		name = $3
		status = $4
		billing_period = $5
		cancelled_count = $6
		
		# Handle empty/null values
		if (date == "" || date == "NULL") date = ""
		if (email == "" || email == "NULL") email = ""
		if (name == "" || name == "NULL") name = "N/A"
		if (status == "" || status == "NULL") status = ""
		if (billing_period == "" || billing_period == "NULL") billing_period = ""
		if (cancelled_count == "" || cancelled_count == "NULL") cancelled_count = "0"
		
		# Map status values
		if (status == "wc-active") status = "Active"
		else if (status == "wc-cancelled") status = "Cancelled"
		else if (status == "wc-pending-cancel") status = "Pending Cancel"
		else if (status == "wc-on-hold") status = "On Hold"
		
		# Map billing period to payment plan
		if (billing_period == "month") billing_period = "Monthly"
		else if (billing_period == "year") billing_period = "Yearly"
		else if (billing_period == "") billing_period = ""
		
		# Properly escape quotes in fields (double any existing quotes)
		gsub(/"/, "\"\"", name)
		gsub(/"/, "\"\"", email)
		gsub(/"/, "\"\"", status)
		gsub(/"/, "\"\"", billing_period)
		
		# Quote fields if they contain commas or quotes
		if (name ~ /[,"]/) {
			name = "\"" name "\""
		}
		if (email ~ /[,"]/) {
			email = "\"" email "\""
		}
		if (status ~ /[,"]/) {
			status = "\"" status "\""
		}
		if (billing_period ~ /[,"]/) {
			billing_period = "\"" billing_period "\""
		}
		
		print date, email, name, status, billing_period, cancelled_count
	}'
}


get_sparkler_info 		\
	| format_as_csv	\
	> sparkler-subscriptions.csv

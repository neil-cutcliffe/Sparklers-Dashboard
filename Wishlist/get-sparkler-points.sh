#!/bin/sh


## Get points transactions with date, email, points, and status
function get_sparkler_points {
	mysql 	-u sparklersclub -pWaterSkiSC12 			\
			-h dss-production-v2.coouoxfzx0u1.us-east-1.rds.amazonaws.com	\
			sparklersclub	\
			--skip-column-names 					\
			--batch							\
			--raw							\
<<EOM

SELECT *
FROM (
    SELECT
        DATE_FORMAT(FROM_UNIXTIME(p.transaction_date), '%Y-%m-%d') AS transaction_date,
        LCASE(u.user_email) AS email,
        p.user_points AS points,
        p.points_status AS points_status,
        p.transaction_date AS transaction_ts
    FROM wp_7_wlpoints_user_points AS p
    JOIN wp_users AS u
        ON u.ID = p.user_id
    ORDER BY p.transaction_date DESC
    LIMIT 1499999
) AS recent
ORDER BY recent.transaction_ts ASC, recent.email ASC;

EOM
}

function format_as_csv {
	awk '
	BEGIN {
		FS = "\t"
		OFS = ","
		print "Date,Email,Points,Status"
	}
	{
		# Get fields
		date = $1
		email = $2
		points = $3
		points_status = $4
		
		# Handle empty/null values
		if (date == "" || date == "NULL") date = ""
		if (email == "" || email == "NULL") email = ""
		if (points == "" || points == "NULL") points = "0"
		if (points_status == "" || points_status == "NULL") points_status = ""
		
		# Map status values
		if (points_status == "added") points_status = "Added"
		else if (points_status == "deducted") points_status = "Unlocked"
		
		# Properly escape quotes in fields (double any existing quotes)
		gsub(/"/, "\"\"", email)
		gsub(/"/, "\"\"", points_status)
		
		# Quote fields if they contain commas or quotes
		if (email ~ /[,"]/) {
			email = "\"" email "\""
		}
		if (points_status ~ /[,"]/) {
			points_status = "\"" points_status "\""
		}
		
		print date, email, points, points_status
	}'
}


get_sparkler_points      \
	| format_as_csv      \
	> sparkler-points.csv

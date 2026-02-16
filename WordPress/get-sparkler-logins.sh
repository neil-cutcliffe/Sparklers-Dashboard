#!/bin/sh

## Get login attempts with date, email, and success status
function get_sparkler_logins {
	mysql 	-u sparklersclub -pWaterSkiSC12 			\
			-h dss-production-v2.coouoxfzx0u1.us-east-1.rds.amazonaws.com	\
			sparklersclub	\
			--skip-column-names 					\
			--batch							\
			--raw	<<EOM

SELECT
    DATE_FORMAT(l.time, '%Y-%m-%d') as login_time,
    CASE
        WHEN l.login_result = 1 THEN u.user_email
        ELSE l.user_login
    END AS email,
    l.login_result
FROM wp_simple_login_log l
LEFT JOIN wp_users u
    ON u.ID = l.uid
WHERE l.time >= '2023-01-01'
ORDER BY l.time ASC;
EOM
}



function format_as_csv {
	awk '
	BEGIN {
		FS = "\t"
		OFS = ","
		print "Date,Email,Logged In"
	}
	{
		login_time = $1
		email = $2
		login_result = $3

		if (login_time == "" || login_time == "NULL") login_time = ""
		if (email == "" || email == "NULL") email = ""

		if (login_result == "1") {
			login_status = "Success"
		} else {
			login_status = "Failed"
		}

		gsub(/"/, "\"\"", login_time)
		gsub(/"/, "\"\"", email)
		gsub(/"/, "\"\"", login_status)

		if (login_time ~ /[,"]/) {
			login_time = "\"" login_time "\""
		}
		if (email ~ /[,"]/) {
			email = "\"" email "\""
		}
		if (login_status ~ /[,"]/) {
			login_status = "\"" login_status "\""
		}

		print login_time, email, login_status
	}'
}

get_sparkler_logins \
	| format_as_csv \
	> sparkler-logins.csv


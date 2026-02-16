#!/bin/sh

# The IDs of the spreadsheets
SPARKLER_DATA_WORDPRESS="1uS5wqj7nrVmZlSHA06kEK6QgGg2A0RYreT8SjCI2ABk"
ALL_SPARKLERS="All Sparklers"
ALL_SPARKLERS_ROWS=6

SPARKLER_DATA_LOGINS="1uS5wqj7nrVmZlSHA06kEK6QgGg2A0RYreT8SjCI2ABk"
LOGGED_IN="Logged In"
LOGGED_IN_ROWS=3

SPARKLER_DATA_BUN_CREDS="1T0kWyi920M0M3I5qioSefzYb00qLUXVXtbE3muZ_8C8"
BUNDLE_CREDITS="Bundle Credits"
BUNDLE_CREDITS_ROWS=4

SPARKLER_GOLD_STARS="1Vg3lmhnI_2F-aoqpJxk1LqIMs_0F5NseaFVeG8u4p18"
GOLD_STARS="Gold Stars"
GOLD_STARS_ROWS=1

source venv/bin/activate


#Jan 29th - Row param no longer needed. It is grabbed dynamically from csv file in python code



#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_DATA_WORDPRESS}"        \
#    "${ALL_SPARKLERS}"                  \
#    "../WooCommerce/sparkler-subscriptions.csv"

echo
python3 upload_to_sheets.py             \
    "${SPARKLER_DATA_LOGINS}"           \
    "${LOGGED_IN}"                      \
    "../WordPress/sparkler-logins.csv"


#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_DATA_BUN_CREDS}"        \
#    "${BUNDLE_CREDITS}"                 \
#    "../Wishlist/sparkler-points.csv"

#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_GOLD_STARS}"        \
#    "${GOLD_STARS}"                 \
#    "../Wishlist/gold-stars.csv"


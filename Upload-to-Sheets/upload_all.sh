#!/bin/sh

# The IDs of the spreadsheets, and the name of the tab
SPARKLER_DATA_WORDPRESS="1uS5wqj7nrVmZlSHA06kEK6QgGg2A0RYreT8SjCI2ABk"
ALL_SPARKLERS="All Sparklers"

SPARKLER_DATA_LOGINS="1uS5wqj7nrVmZlSHA06kEK6QgGg2A0RYreT8SjCI2ABk"
LOGGED_IN="Logged In"

SPARKLER_DATA_BUN_CREDS="1T0kWyi920M0M3I5qioSefzYb00qLUXVXtbE3muZ_8C8"
BUNDLE_CREDITS="Bundle Credits"

SPARKLER_GOLD_STARS="1Vg3lmhnI_2F-aoqpJxk1LqIMs_0F5NseaFVeG8u4p18"
GOLD_STARS="Gold Stars"

SPARKLER_KLAVIYO="11IhWEVIPbM23meiS1HbNUgkc0lUCVjXRicYqS_MuL2s"
NEWSLETTER_1="1 Week"

SPARKLER_KLAVIYO="11IhWEVIPbM23meiS1HbNUgkc0lUCVjXRicYqS_MuL2s"
NEWSLETTER_2="2 Weeks"

SPARKLER_KLAVIYO="11IhWEVIPbM23meiS1HbNUgkc0lUCVjXRicYqS_MuL2s"
NEWSLETTER_4="4 Weeks"

SPARKLER_KLAVIYO="11IhWEVIPbM23meiS1HbNUgkc0lUCVjXRicYqS_MuL2s"
NEWSLETTER_6="6 Weeks"

source venv/bin/activate


#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_DATA_WORDPRESS}"        \
#    "${ALL_SPARKLERS}"                  \
#    "../WooCommerce/sparkler-subscriptions.csv"

#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_DATA_LOGINS}"           \
#    "${LOGGED_IN}"                      \
#    "../WordPress/sparkler-logins.csv"


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

#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_KLAVIYO}"               \
#    "${NEWSLETTER_1}"                   \
#    "../Klaviyo/TSC-Newsletter-Opens-1.csv"

#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_KLAVIYO}"               \
#    "${NEWSLETTER_2}"                   \
#    "../Klaviyo/TSC-Newsletter-Opens-2.csv"

#echo
#python3 upload_to_sheets.py             \
#    "${SPARKLER_KLAVIYO}"               \
#    "${NEWSLETTER_4}"                   \
#    "../Klaviyo/TSC-Newsletter-Opens-4.csv"

echo
python3 upload_to_sheets.py             \
    "${SPARKLER_KLAVIYO}"               \
    "${NEWSLETTER_6}"                   \
    "../Klaviyo/TSC-Newsletter-Opens-6.csv"


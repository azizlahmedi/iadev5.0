from django.conf import settings

EMAIL_SENDER = settings.ADMINS[0][0]
FROM_EMAIL = settings.DEFAULT_FROM_EMAIL
RECIPIENTS = [
    "olivier.mansion@neoxam.com",
    "abdellatif.ettaleb@neoxam.com",
]

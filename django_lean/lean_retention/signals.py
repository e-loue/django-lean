from django.dispatch import Signal


# User has signed in after some inactivity
sign_in = Signal(providing_args=['sign_in', 'request'])

# User has triggered activity for the first time today
new_day = Signal(providing_args=['daily_activity', 'request'])

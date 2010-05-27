from django.dispatch import Signal


# User has signed in after some inactivity
sign_in = Signal(providing_args=['sign_in', 'request'])

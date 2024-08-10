from functools import wraps
from flask import session, redirect

def login_required(f):
    """
    Decorate routes to require login.
    And check if the git is working correctly!
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # if session.get("user_id") is None:
        #     return redirect("/login")
        print("Original function name:", f.__name__)
        return f(*args, **kwargs)
    return decorated_function

@login_required
def edit_role():
    pass

# Test the decorator
edit_role()

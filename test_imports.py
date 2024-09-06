import sys
print(sys.path)

try:
    import flask
    print("Flask imported successfully")
except ImportError as e:
    print(f"Failed to import Flask: {e}")

try:
    from flask_cors import CORS
    print("Flask-CORS imported successfully")
except ImportError as e:
    print(f"Failed to import Flask-CORS: {e}")
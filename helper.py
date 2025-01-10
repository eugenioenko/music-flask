from model import User
from bcrypt import checkpw
#Helpers
def user_login_validation(email, password):
	try:
		user = User.get(User.email == email)
		if checkpw(str(password).encode('utf-8'), str(user.password).encode('utf-8')):
			return user
		else:
			return None
	except User.DoesNotExist:
		return None
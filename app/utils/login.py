from app.models.models import User
from app import login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

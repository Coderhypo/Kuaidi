from flask_script import Manager, Server
from app import create_app, init_db

app = create_app()
manager = Manager(app)
manager.add_command("runserver", Server(host="0.0.0.0", port=5000))


@manager.command
def init():
    init_db()


if __name__ == "__main__":
    manager.run()

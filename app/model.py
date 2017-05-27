import uuid
import json
import datetime
from itsdangerous import JSONWebSignatureSerializer, BadSignature
from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

from app.client import Client
from config import TOKEN_SECRET_KEY

db = SQLAlchemy()
login_manager = LoginManager()
serializer = JSONWebSignatureSerializer(TOKEN_SECRET_KEY, salt="token salt")


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(user_id=user_id).first()


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("view.login"))


class User(db.Model):
    user_id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String)
    create_time = db.Column(db.DateTime())

    def __init__(self, username, email, password):
        self.user_id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = generate_password_hash(password)
        self.create_time = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

    @property
    def is_authenticated(self):
        if self.user_id:
            return True
        return False

    @property
    def is_active(self):
        if self.email and self.password:
            return True
        return False

    @property
    def is_anonymous(self):
        if self.is_authenticated:
            return False
        return True

    def get_id(self):
        return self.user_id

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_token(self):
        data = {
            "user_id": self.user_id,
            "random": str(uuid.uuid4()).split("-")[0],
        }
        return str(serializer.dumps(data), encoding="utf-8")

    @classmethod
    def get_user_by_token(cls, token):
        try:
            data = serializer.loads(token)
        except BadSignature:
            return None
        user_id = data.get("user_id")
        return cls.query.filter_by(user_id=user_id).first()


class Express(db.Model):
    express_id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(80))
    code = db.Column(db.String(120), index=True, unique=True)
    tel = db.Column(db.String(120))
    create_time = db.Column(db.DateTime())
    update_time = db.Column(db.DateTime())

    def __init__(self, name, code, tel):
        self.express_id = str(uuid.uuid4())
        self.name = name
        self.code = code
        self.tel = tel

        self.create_time = datetime.datetime.now()
        self.update_time = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_all_express(cls):
        rsp = Client().get_all_express()
        result = []

        for r in rsp:
            e = cls.query.filter_by(code=r['type']).first()
            if not e:
                e = cls(r['name'], r['type'], r.get("tel"))
            result.append(e)
        return result

    def render(self):
        return {
            "name": self.name,
            "code": self.code,
            "tel": self.tel,
        }


class Package(db.Model):
    package_id = db.Column(db.String(64), primary_key=True)
    nicename = db.Column(db.String(150))
    user_id = db.Column(db.String(64), index=True)
    express_id = db.Column(db.String(64), index=True)
    number = db.Column(db.String(120), index=True)
    delivery_status = db.Column(db.Integer)
    info = db.Column(db.Text)
    is_watching = db.Column(db.Boolean)
    update_time = db.Column(db.DateTime())
    create_time = db.Column(db.DateTime())

    ON_THE_WAY = 1
    IN_DELIVERY = 2
    SIGNED = 3
    DELIVERY_FAILURE = 4

    def __init__(self, user_id, express_id, info):
        self.package_id = str(uuid.uuid4())
        self.user_id = user_id
        self.is_watching = False
        self.info = json.dumps(info)

        self.number = info['number']
        self.express_id = express_id
        self.delivery_status = int(info['deliverystatus'])

        self.create_time = datetime.datetime.now()
        self.update_time = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_package(cls, user_id, express_code, package_number):
        try:
            package_info = Client().get_package(express_code, package_number)
        except:
            return None
        express = Express.query.filter_by(code=express_code).first()
        package = cls.query.filter_by(user_id=user_id, number=package_number).first()
        if not package:
            package = cls(user_id, express.express_id, package_info)
        else:
            package.update(package_info)
        return package

    @classmethod
    def get_package_by_id(cls, package_id):
        pkg = Package.query.filter_by(package_id=package_id).first()
        if pkg and pkg.delivery_status != cls.SIGNED:
            express = Express.query.filter_by(express_id=pkg.express_id).first()
            package_info = Client().get_package(express.code, pkg.number)
            pkg.update(package_info)
        return pkg

    @classmethod
    def get_watching_package_by_user_id(cls, user_id):
        watches = WatchPackage.query.filter_by(user_id=user_id).order_by(WatchPackage.update_time.desc()).all()
        result = []
        for w in watches:
            w.update()
            pkg = Package.query.filter_by(package_id=w.package_id).first()
            result.append(pkg)
        return result

    def update(self, info):
        self.info = json.dumps(info)
        self.delivery_status = info['deliverystatus']

        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.query(WatchPackage).filter_by(package_id=self.package_id).delete()
        db.session.delete(self)
        db.session.commit()

    @property
    def express(self):
        return Express.query.filter_by(express_id=self.express_id).first()

    def watching(self, nicename):
        if self.is_watching:
            return
        self.is_watching = True
        self.nicename = nicename
        db.session.add(self)
        db.session.commit()
        WatchPackage(self.user_id, self.package_id)

    def unwatching(self):
        if not self.is_watching:
            return
        self.is_watching = False
        db.session.add(self)
        db.session.query(WatchPackage).filter_by(user_id=self.user_id, package_id=self.package_id).delete()
        db.session.commit()

    @property
    def status(self):
        if self.delivery_status == self.ON_THE_WAY:
            return '<span class="label label-info"><b>在途中</b></span>'
        if self.delivery_status == self.IN_DELIVERY:
            return '<span class="label label-warning"><b>正在派送</b></span>'
        if self.delivery_status == self.SIGNED:
            return '<span class="label label-success"><b>已签收</b></span>'
        if self.delivery_status == self.DELIVERY_FAILURE:
            return '<span class="label label-danger"><b>派送失败</b></span>'

    @property
    def details(self):
        info = json.loads(self.info)
        info_list = info['list']
        result = []

        for l in info_list:
            i = {
                "datetime": datetime.datetime.strptime(l['time'], "%Y-%m-%d %H:%M:%S"),
                "status": l['status']
            }
            result.append(i)

        if len(result) > 0:
            last_status = result[0]
            update_time = last_status['datetime']
            self.update_time = update_time
            db.session.add(self)
            db.session.commit()
        return result

    def set_nicename(self, nicename):
        self.nicename = nicename
        db.session.add(self)
        db.session.commit()

    def render(self):
        return {
            "package_id": self.package_id,
            "nicename": self.nicename,
            "user_id": self.user_id,
            "express": self.express.render(),
            "number": self.number,
            "status": self.delivery_status,
            "update_time": self.update_time,
            "create_time": self.create_time,
            "details": self.details,
        }


class WatchPackage(db.Model):
    watch_id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), index=True)
    package_id = db.Column(db.String(64), index=True)
    package_status = db.Column(db.Integer)
    update_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime)

    def __init__(self, user_id, package_id):
        self.watch_id = str(uuid.uuid4())
        self.user_id = user_id
        self.package_id = package_id
        self.create_time = datetime.datetime.now()
        db.session.add(self)
        db.session.commit()

    def update(self):
        package = Package.get_package_by_id(self.package_id)
        self.package_status = package.delivery_status
        self.update_time = package.update_time
        db.session.add(self)
        db.session.commit()


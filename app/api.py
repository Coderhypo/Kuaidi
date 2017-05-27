from functools import wraps
from flask import Blueprint, jsonify, request, abort, g

from app.model import Express, User, Package


api = Blueprint("api", __name__)


def validate_token(func):
    @wraps(func)
    def validate(*args, **kwargs):
        token = request.headers.get("token")
        if not token:
            abort(400)
        user = User.get_user_by_token(token)
        if not user:
            abort(403)
        g.user = user
        return func(*args, **kwargs)
    return validate


@api.route("/_ping")
def ping():
    return "PONG"


@api.route("/api/express")
@validate_token
def get_all_express():
    flash = request.args.get("flash")
    try:
        if int(flash) == 0:
            flash = True
        else:
            flash = False
    except:
        flash = False

    if flash:
        objects = Express.get_all_express()
    else:
        objects = Express.query.all()
    result = []
    for o in objects:
        result.append(o.render())

    return jsonify(result)


@api.route("/api/express/<express_code>/<package_number>")
@validate_token
def get_package_by_number(express_code, package_number):
    user = g.user
    package = Package.get_package(user.user_id, express_code, package_number)
    if not package:
        abort(400)
    return jsonify(package.render())


@api.route("/api/package/<package_id>")
@validate_token
def get_package_by_id(package_id):
    user = g.user
    package = Package.get_package_by_id(package_id)
    if not package or package.user_id != user.user_id:
        abort(404)
    return jsonify(package.render())


@api.route("/api/watching")
@validate_token
def get_all_watching():
    user = g.user
    packages = Package.get_watching_package_by_user_id(user.user_id)
    result = []
    for p in packages:
        p_info = p.render()
        p_info.pop("details")
        result.append(p_info)
    return jsonify(result)


@api.route("/api/token", methods=['POST'])
def get_token():
    json = request.json
    username = json.get("username")
    password = json.get("password")

    if not username or not password:
        abort(400)
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        abort(404)

    return jsonify({
        "user_id": user.user_id,
        "token": user.get_token()
    })


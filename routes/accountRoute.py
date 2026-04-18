from flask import Blueprint

from controllers.accountController import (
    create_account,
    delete_account,
    get_account,
    list_accounts,
    patch_account,
)

account_bp = Blueprint("accounts", __name__)


@account_bp.route("/accounts", methods=["GET"])
def list_accounts_route():
    return list_accounts()


@account_bp.route("/accounts", methods=["POST"])
def create_account_route():
    return create_account()


@account_bp.route("/accounts/<int:item_id>", methods=["GET"])
def get_account_route(item_id):
    return get_account(item_id)


@account_bp.route("/accounts/<int:item_id>", methods=["PATCH"])
def patch_account_route(item_id):
    return patch_account(item_id)


@account_bp.route("/accounts/<int:item_id>", methods=["DELETE"])
def delete_account_route(item_id):
    return delete_account(item_id)

from flask import render_template, jsonify, request

from utils.databaseUtil import execute_query,fetch_query


def getListProducts():
    products = fetch_query("SELECT * FROM storages LIMIT 20")
    if products:
        # Giả sử bạn biết cột là id, name, price
        products_list = [{"id": p[0], "name": p[1], "price": p[2]} for p in products]
        return jsonify(products_list)
    else:
        return jsonify({"message": "Khong co san pham"})
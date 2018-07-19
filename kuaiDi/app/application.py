# coding=utf-8
#coding = utf-8
from app import app
from flask import render_template, request, url_for, jsonify
from kdf0623 import checkworker
import os

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/learn")
def learn():
    return render_template("learn.html")

@app.route("/download", methods=["POST"])
def data_check():
    file_1 = request.files['file_1']
    file_2 = request.files['file_2']
    # 获取文件类型
    ext_1 = file_1.filename.split(".")[-1]
    ext_2 = file_2.filename.split(".")[-1]
    # 文件保存路径
    upload_file_path = "/Users/dongliangzhou/Desktop/programming/haozhenxian/web/app/res/"
    # 下载文件名
    out_file_name_1 = "没有重量的商品清单."+ext_1
    out_file_name_2 = "快递费比较."+ext_2
    file_1.save(os.path.join(upload_file_path, file_1.filename))
    file_2.save(os.path.join(upload_file_path, file_2.filename))
    worker = checkworker()
    try:
        worker.run(os.path.join(upload_file_path, file_1.filename),
                    os.path.join(upload_file_path, file_2.filename),
                    os.path.join(upload_file_path, out_file_name_1),
                    os.path.join(upload_file_path, out_file_name_2))

        return render_template("download.html",
                           filename1=url_for('static', filename='res/{}'.format(out_file_name_1)),
                           filename2=url_for('static', filename='res/{}'.format(out_file_name_2)))

    except Exception as e:
        print(e)
        return render_template("error.html", err=str(e))
    #return jsonify({"msg":"ok", "path":url_for('static', filename='res/b.xlsx')})

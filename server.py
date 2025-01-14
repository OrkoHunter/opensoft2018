#!/usr/bin/env python3

import glob
import json
import time
import hashlib
import os
import os.path
import threading
import webbrowser
import requests
import datetime as DT
from flask import Flask, render_template, session, request, redirect, url_for
from werkzeug.utils import secure_filename
from json2html import *

import traceback
from aws import aws_fileupload, aws_read, replace
from nlp import correct_json

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = CUR_DIR + '/static/files/uploads'
RESULTS_FOLDER = CUR_DIR + '/static/files/results'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/uploadfile", methods=['POST'])
def uploadfile():
    # check if the post request has the file part
    files = request.files.getlist("file[]")
    # if 'file' not in request.files:
    #     raise Exception('No file part')
    #     return redirect(request.url)
    for file in files:
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            raise Exception('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return ('success', 200)


@app.route("/processfile/<filename>")
def processfile(filename):
    print("begin")
    try:
        aws_fileupload.file_upload(filename, UPLOAD_FOLDER)
        print("uploaded")
        aws_result = aws_read.file_read(filename, UPLOAD_FOLDER)
        print ("start")
        corrected_result = correct_json.main(aws_result)
        print ("end")
        replace.main(json.loads(corrected_result), filename, UPLOAD_FOLDER)
        return (filename, 200)
    except Exception as e:
        print(e)
        traceback.print_exc()
        return (filename, 500)


@app.route("/history")
def history():
    kwargs = {}

    files = glob.glob(RESULTS_FOLDER+'/*')

    resultfiles= []
    idnames=[]
    uploadfiles = []
    scans = []

    for file in files:
        resultfiles.append(file.replace(CUR_DIR,""))


    for file in resultfiles:
        uploadfiles.append(file.replace("results","uploads"))

    for file in files:
        idnames.append(DT.datetime.utcfromtimestamp(os.stat(file).st_mtime+19800).isoformat())

    for i,idname in enumerate(idnames):
        temp={
            'id' : idname,
            'original_filename' : uploadfiles[i],
            'output': resultfiles[i],
        }
        scans.append(temp)

    kwargs['scans'] = scans
    
    return render_template('history.html', **kwargs)


@app.route("/insights", methods=['GET', 'POST'])
def insights():
    token = '71c4161312f0f36b120f80f4b015717bee72c4e337fc4800840786fa50102ccb'
    if request.method == 'POST':
        query = request.form['query']
        if len(query) == 0 or not query.isalnum():
            return render_template('insights.html')
        option = request.form['options']
        print(option)
        if option == "Medicine":
            print(query)
            r = requests.get(
                "http://www.healthos.co/api/v1/autocomplete/medicines/brands/" + query,
                headers={
                    'Authorization': 'Bearer ' + token})
            if len(
                    r.content) > 2:  # checking if the response has more than just two brackets []
                parsed = json.loads(r.content.decode('utf-8'))
                for element in parsed:
                    del element['medicine_id']
                    del element['id']
                    del element['search_score']

                finaltable = json2html.convert(json=parsed).replace('>', '>\n')

                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                cssname = """<link href="/static/assets/css/table.css" rel="stylesheet"/>"""
                contents.insert(27, cssname)
                contents.insert(39, finaltable)
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)
                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()

                with open("templates/new.html", "r") as f:
                    for num, line in enumerate(f, 1):
                        if num == 39:
                            newline = """<table class="table" border="1">"""
                            line = newline
            else:
                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                contents.insert(39, "<b>Your query returned no results.</b>")
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)
                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()
            return render_template('new.html')

        elif option == "LabTest":
            print(query)
            r = requests.get(
                "http://www.healthos.co/api/v1/autocomplete/lab_tests/" + query,
                headers={
                    'Authorization': 'Bearer ' + token})
            if len(
                    r.content) > 2:  # checking if the response has more than just two brackets []
                parsed = json.loads(r.content.decode('utf-8'))
                for element in parsed:
                    del element['lab_test_id']
                    del element['id']
                    del element['search_score']
                finaltable = json2html.convert(json=parsed).replace('>', '>\n')

                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                cssname = """<link href="/static/assets/css/table.css" rel="stylesheet"/>"""
                contents.insert(27, cssname)
                contents.insert(39, finaltable)
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)
                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()

                with open("templates/new.html", "r") as f:
                    for num, line in enumerate(f, 1):
                        if num == 39:
                            newline = """<table class="table" border="1">"""
                            line = newline
            else:
                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                contents.insert(39, "<b>Your query returned no results.</b>")
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)
                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()
            return render_template('new.html')
        else:
            r = requests.get(
                "http://www.healthos.co/api/v1/autocomplete/diseases/" + query,
                headers={
                    'Authorization': 'Bearer ' + token})

            if len(
                    r.content) > 2:  # checking if the response has more than just two brackets []
                parsed = json.loads(r.content.decode('utf-8'))
                for element in parsed:
                    del element['disease_id']
                    del element['disease_cat']
                    del element['search_score']

                finaltable = json2html.convert(json=parsed).replace('>', '>\n')

                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                cssname = """<link href="/static/assets/css/table.css" rel="stylesheet"/>"""
                contents.insert(27, cssname)
                contents.insert(39, finaltable)
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)

                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()

                with open("templates/new.html", "r") as f:
                    for num, line in enumerate(f, 1):
                        if num == 39:
                            newline = """<table class="table" border="1">"""
                            line = newline
            else:
                f = open("templates/template.html", "r")
                contents = f.readlines()
                f.close()
                contents.insert(39, "<b>Your query returned no results.</b>")
                contents.insert(40,
                                """
                                    <br><br>
                                    <a href="/insights" class="button">Search again</a>
                                """)
                f = open("templates/new.html", "wb")
                contents = "".join(contents)
                f.write(contents.encode('utf-8'))
                f.close()
            return render_template('new.html')
    else:
        return render_template('insights.html')


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/feedback",methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['Name']
        email = request.form['email']
        idnum = request.form['idnum']
        phone = request.form['phone']
        feedbacktext = request.form['feedbacktext']
        
        if not os.path.exists('feedbacks'):
            os.makedirs('feedbacks')

        f = open("feedbacks/"+name+".txt", "wb")
        f.write(("Name ->"+name+'\n').encode('utf-8'))
        f.write(("email ->"+email+'\n').encode('utf-8'))
        f.write(("Id ->"+idnum+'\n').encode('utf-8'))
        f.write(("phone ->"+phone+'\n').encode('utf-8'))
        f.write(("Feedback ->"+feedbacktext+'\n').encode('utf-8'))
        f.close()

        f = open("templates/template.html", "r")
        contents = f.readlines()
        f.close()
        contents.insert(39, "<h3>Your response was captured and saved to the Feedback folder.</h3>")
        contents.insert(40,
                        """
                            <br><br>
                            <a href="/" class="button">Return to home.</a>
                        """)

        f = open("templates/feedbackdone.html", "wb")
        contents = "".join(contents)
        f.write(contents.encode('utf-8'))
        f.close()

        return render_template('feedbackdone.html')
    else:
        return render_template('feedback.html')


if __name__ == '__main__':
    app.debug = True
    port = 8000
    url = "http://127.0.0.1:{0}".format(port)
    print(""" * DigiCon v1.0 is running on port 8000\n
        Please open {0} in your browser to use the software.
        """.format(url))

    if not app.debug:
        threading.Timer(1.00, lambda: webbrowser.open(url)).start()

    app.run(port=port)

#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, make_response, session
from markupsafe import escape
import pymongo
import datetime
from bson.objectid import ObjectId
import os
import subprocess

# instantiate the app
app = Flask(__name__)

import credentials
config = credentials.get()

if config['FLASK_ENV'] == 'development':
    # turn on debugging, if in development
    app.debug = True # debug mode


# make one persistent connection to the database
connection = pymongo.MongoClient(config['MONGO_HOST'], 27017, 
                                username=config['MONGO_USER'],
                                password=config['MONGO_PASSWORD'],
                                authSource=config['MONGO_DBNAME'])
db = connection[config['MONGO_DBNAME']] # store a reference to the database

users_collection = db['users'] #store a reference to the users collection

# set up the routes
@app.route('/')
def home():
    """
    Route for the home page
    """
    return render_template('index.html')


# check if the password is correct, if it is then redirect to the work experience html 
@app.route('/password',methods=['POST']) 
def password():
    password = request.form['password']
    if password == 'PleaseHireAlice': 
        return redirect(url_for('experiences'))
    else: 
        return redirect(url_for('index'))
    

@app.route('/experiences')
def experiences():
    docs = db.exampleapp.find({}).sort("end_year", -1) # sort in descending order of created_at timestamp
    return render_template('experiences.html', docs=docs)

@app.route('/experiences', methods=['POST'])
def create_post():
    """
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    company = request.form['company']
    experience = request.form['experience']
    start_month = request.form['month']
    start_year = request.form['year']
    end_month = request.form['end_month']
    end_year = request.form['end_year']


    # create a new document with the data the user entered
    doc = {
        "company": company,
        "experience": experience,
        "start_year": start_year,
        "start_month": start_month,
        "end_year": end_year,
        "end_month": end_month,
        "created_at": datetime.datetime.utcnow()
    }
    db.exampleapp.insert_one(doc) # insert a new document

    return redirect(url_for('experiences')) # tell the browser to make a request for the /read route

# Skills page 
@app.route('/skills') 
def skills():
    docs = db.exampleapp.find({}).sort("created_at", -1) # sort in descending order of created_at timestamp
    return render_template('skills.html', docs=docs)

@app.route('/skills',methods=['POST']) 
def create_skill():
    skills = request.form['skills']
    projects = request.form['projects']
    
    doc = {
        "skills": skills,
        "projects": projects,
        "created_at": datetime.datetime.utcnow()
    }
    
    db.exampleapp.insert_one(doc)
    
    return redirect(url_for('skills'))

# Education page 
@app.route('/education')
def education():
    docs = db.exampleapp.find({}).sort("end_year", -1) # sort in descending order of created_at timestamp
    return render_template('education.html', docs=docs)

@app.route('/education',methods=['POST']) 
def create_education():
    education = request.form['education']
    start_year = request.form['start_year']
    start_month = request.form['start_month']
    end_year = request.form['end_year']
    end_month = request.form['end_month']
    
    
    doc = {
        "education": education,
        "start_year": start_year,
        "start_month": start_month,
        "end_year": end_year,
        "end_month": end_month
    }
    
    db.exampleapp.insert_one(doc)
    
    return redirect(url_for('education'))

# EDIT EXPERIENCE
@app.route('/edit/<mongoid>')
def edit(edit_type,mongoid):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """
    
    doc = db.exampleapp.find_one({"_id": ObjectId(mongoid)})
    if edit_type == 'skills':
        return render_template('edit_skills.html', mongoid=mongoid, doc=doc)
    elif edit_type == 'education':
        return render_template('edit_education.html', mongoid=mongoid,doc=doc)
    else:
        return render_template('edit.html', mongoid=mongoid, doc=doc)
    # render the edit template based on the edit type

@app.route('/edit/<mongoid>', methods=['POST'])
def edit_post(edit_type, mongoid):
    """
    Route for POST requests to the edit page.
    Accepts the form submission data for the specified document and updates the document in the database.
    """
    if edit_type == 'experiences':
        company = request.form['company']
        experience = request.form['experience']
        start_month=request.form['start_month']
        start_year = request.form['start_year']
        end_month=request.form['end_month']
        end_year = request.form['end_year']

        doc = {
            # "_id": ObjectId(mongoid), 
            "company": company, 
            "experience": experience, 
            "created_at": datetime.datetime.utcnow(),
            "start_year": start_year,
            "start_month": start_month,
            "end_year": end_year,
            "end_month": end_month
        }

        db.exampleapp.update_one(
            {"_id": ObjectId(mongoid)}, # match criteria
            { "$set": doc }
        )

        return redirect(url_for('experiences')) # tell the browser to make a request for the /experience route 
    elif edit_type == 'skills':
        skills = request.form['skills']
        projects = request.form['projects']
        
        doc = {
            "skills": skills,
            "projects": projects,
            "created_at": datetime.datetime.utcnow
        }
        
        db.exampleapp.update_one(
            {"_id": ObjectId(mongoid)}, # match criteria
            { "$set": doc }
        )

        return redirect(url_for('skills')) # tell the browser to make a request for the /skills route 
    
    else: 
        education = request.form['education']
        start_month=request.form['start_month']
        start_year = request.form['start_year']
        end_month=request.form['end_month']
        end_year = request.form['end_year']
        doc = {
            "education": request.form['education'],
            "start_year": start_year,
            "start_month": start_month,
            "end_year": end_year,
            "end_month": end_month
        }
        
        return redirect(url_for('experience'))
        
@app.route('/delete/<mongoid>')
def delete(mongoid):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.exampleapp.delete_one({"_id": ObjectId(mongoid)})
    return redirect(url_for('experiences')) # tell the web browser to make a request for the /read route.


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    GitHub can be configured such that each time a push is made to a repository, GitHub will make a request to a particular web URL... this is called a webhook.
    This function is set up such that if the /webhook route is requested, Python will execute a git pull command from the command line to update this app's codebase.
    You will need to configure your own repository to have a webhook that requests this route in GitHub's settings.
    Note that this webhook does do any verification that the request is coming from GitHub... this should be added in a production environment.
    """
    # run a git pull command
    process = subprocess.Popen(["git", "pull"], stdout=subprocess.PIPE)
    pull_output = process.communicate()[0]
    # pull_output = str(pull_output).strip() # remove whitespace
    process = subprocess.Popen(["chmod", "a+x", "flask.cgi"], stdout=subprocess.PIPE)
    chmod_output = process.communicate()[0]
    # send a success response
    response = make_response('output: {}'.format(pull_output), 200)
    response.mimetype = "text/plain"
    return response

@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template('error.html', error=e) # render the error template


if __name__ == "__main__":
    #import logging
    #logging.basicConfig(filename='/home/ak8257/error.log',level=logging.DEBUG)
    app.run(debug = True)

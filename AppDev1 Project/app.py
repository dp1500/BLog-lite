from flask import Flask, url_for, redirect, flash, jsonify
import requests
from flask import render_template
from flask import request
from flask_login import login_user
from flask_login import LoginManager
from flask_login import current_user
from werkzeug.utils import secure_filename 
from flask_restful import Resource, Api
from getImage import *
from useful_functions import *


from requests.adapters import HTTPAdapter

# Create a session with a specific number of retries
s = requests.Session()
adapter = HTTPAdapter(max_retries=3)
s.mount('https://', adapter)

from APIs import *

import os

from models import *

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import create_engine
# from sqlalchemy import Table, Column, Integer, String, ForeignKey, delete

current_dir = os.path.abspath(os.path.dirname(__file__))



app = Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(
  current_dir, "database.sqlite3")



from database import db

db.init_app(app)

login_manager = LoginManager(app)
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
  return users.query.get(int(user_id))

# #configuring path and constraint to save images
# UPLOAD_FOLDER = 'static\images'
# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# def allowed_file(filename):
#   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#configuring flask api
api = Api(app)
api.init_app(app)

app.app_context().push()

engine = create_engine("sqlite:///./database.sqlite3")


@app.route('/', methods=["GET", "POST"])
def home():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    user = users.query.filter_by(username=username).first()
    if user:
      if user.password == password:

        print(user.username + "logged in")
        login_user(user)
        
        return redirect(url_for('feed'))
      else:
        print('Wrong password')
    else:
      print('Username does not exist')
  
  return render_template("index.html")


@app.route('/SignUp', methods=['GET', 'POST'])
def SignUp():
  if request.method == 'POST':

    username = request.form.get('username')
    name = request.form.get('name')
    password = request.form.get('password')
    repeat_password = request.form.get('repeat_password')

    username_exists = users.query.filter_by(username=username).first()

    if username_exists:
    
      flash('Username already taken. Kindly enter another username')

    elif name == None:
      flash('Enter a name')

    elif len(password) < 5:
      flash('Length of password is too short. passqord should be atleast 5 characters long')
    
    elif password != repeat_password:
      flash('passwords dont match')

    else:
      
      data = {
            'name': name,
            'username': username,
            'password': password,
        }
      
      url = 'http://127.0.0.1:8080/api/ProfileData'
      response = requests.post(url, json=data)

      if response.status_code == 200:

        new_user = users.query.filter_by(username=username).first()
        print("level 1")
        print(new_user.name)
        print("leve 2l")
        login_user(new_user)
        print("leve 3")  
        return redirect(url_for('feed'))

  return render_template("signup.html") 


api.add_resource(FeedBlogsApi, "/api/FeedBlogsData","/api/FeedBlogsData/<string:Uid>")


@app.route('/feed')
# @login_required
def feed():
  user = current_user
  
  blog_response = requests.get('http://127.0.0.1:8080/api/FeedBlogsData/' + str(user.Uid)) 
  blog_data = blog_response.json()
  
  if blog_response.status_code == 204:
    return render_template("feed.html" , user=current_user , blog_data = blog_data)

  if blog_response.status_code == 200:
    return render_template("feed.html" , user=current_user , blog_data = blog_data)


api.add_resource(BlogApi, "/api/ViewBlogData","/api/ViewBlogData/<string:blog_id>")

@app.route('/blog/<blogger_name>/<blog_id>')
def view_blog(blogger_name,blog_id):

 
  blog_response = requests.get('http://127.0.0.1:8080/api/ViewBlogData/' + str(blog_id))

  if blog_response == 204:
    print("this is level 3")
    return "error getting blog, check the validity of blog id"
 
  blog_data = blog_response.json()
  return render_template("viewBlog.html" , user=current_user , blog_data = blog_data , blogger_name = blogger_name)


# start of profie related routes #

api.add_resource(ProfileDataApi, "/api/ProfileData","/api/ProfileData/<string:Uid>")
api.add_resource(ProfileBlogsApi, "/api/ProfileBlogsData","/api/ProfileBlogsData/<string:Uid>")

@app.route('/Profile', methods=["GET", "POST"])
def profile():
  user = current_user
  response = requests.get('http://127.0.0.1:8080/api/ProfileData/' + str(user.Uid))
  data = response.json()

  blog_response = requests.get('http://127.0.0.1:8080/api/ProfileBlogsData/' + str(user.Uid))
  blog_data = blog_response.json()
  
  if response.status_code == 204:
    return "error getting user details"
  
  if blog_response.status_code == 204:
    return render_template("my_profile_no_blogs.html", data=data, user=current_user)

  return render_template("my_profile.html", data=data, user=current_user , blog_data =blog_data)

@app.route('/following/<Uid>')
def following(Uid): 
    
    users_following_list = db.session.query(users).filter(users.Uid == Uid).first()

    print(":following level 1")
    followings = follows.query.filter(follows.follower == Uid).all()
    print(":following level 2")
    if followings:
      users_self_follow = []
      print(":following level 3")
      for follow in followings:
        print(":following level 4")
        user = db.session.query(users).filter(users.Uid == follow.following).first()

        users_self_follow.append({ "Uid": user.Uid, "name": user.name, "username": user.username, "posts": user.posts, "n_followers": user.n_followers, "n_following": user.n_following, "about": user.about, "profile_pic_url" : user.profile_pic_url})

      return render_template('following.html', followings = users_self_follow, user=current_user, users_following_list = users_following_list)
    else:
      return "follow people"

@app.route('/followers/<Uid>')
def followers(Uid): 
    
    users_follower_list = db.session.query(users).filter(users.Uid == Uid).first()

    print(":following level 1")
    followers_list = follows.query.filter(follows.following == Uid).all()
    print(":following level 2")
    if followers_list:
      users_self_follow = []
      print(":following level 3")
      for follow in followers_list:
        print(":following level 4")
        user = db.session.query(users).filter(users.Uid == follow.follower).first()

        users_self_follow.append({ "Uid": user.Uid, "name": user.name, "username": user.username, "posts": user.posts, "n_followers": user.n_followers, "n_following": user.n_following, "about": user.about, "profile_pic_url" : user.profile_pic_url})

      return render_template('followers.html', followings = users_self_follow, user=current_user, users_follower_list = users_follower_list)
    else:
      return "follow people"

# edit profile page
@app.route('/EditProfile', methods=["GET", "POST"])
def edit_profile():
  
  if request.method == 'POST':
    
    username = request.form.get('username')
    name = request.form.get('name')
    about = request.form.get('about')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    file = request.files['file']

    file_name = None
    
    user = current_user

    if 'file' not in request.files:
      pass
    # if user does not select file, browser also
        # submit a empty part without filename

    else:
      #configuring path and constraint to save images
      UPLOAD_FOLDER = 'static\images'
      ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
      app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
      def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

      if file.filename == '':
        print('No image selected')
        pass

      if file and allowed_file(file.filename):

        print(file.filename)
        filename = secure_filename(file.filename)
        basedir = os.path.abspath(os.path.dirname(__file__))
        file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
        # file.save(f'static/images/{filename}')
        file_name = f'/static/images/{filename}'

    data = {
            'name': name,
            'username': username,
            'about': about,
            'username': username,
            'old_password': old_password,
            'new_password': new_password,
            'file': file_name
        }      
                      
    url = 'http://127.0.0.1:8080/api/ProfileData/' + str(user.Uid)
    response = requests.put(url, json=data)

    

    if response.status_code == 400:
      flash('Passwords dont match')
      redirect(url_for('edit_profile'))

    if response.status_code == 200:

      user = current_user
      response = requests.get('http://127.0.0.1:8080/api/ProfileData/' + str(user.Uid))
      data = response.json()
      
      flash('profile submitted Submitted succesfully')

      return redirect(url_for('profile'))
      # return render_template("my_profile.html", data=data, user=current_user)

    

    if response.status_code == 204:
      flash('error getting user detail')
      redirect(url_for('edit_profile'))

    else:
        return 'error validating profile. Check submitted Credentials'

  else:
    user = current_user
    response = requests.get('http://127.0.0.1:8080/api/ProfileData/' + str(user.Uid))
    data = response.json()
    return render_template("editProfile.html", data = data,  user=current_user)

# edit blog page
@app.route('/EditBlog/<blog_id>', methods=["GET", "POST"])
def edit_blog(blog_id):
  if request.method == 'POST':

    title = request.form.get('title')
    description = request.form.get('description')
    about = request.form.get('about')
    file = request.files['file']

    file_name = None
    
    user = current_user

    if 'file' not in request.files:
      pass
    # if user does not select file, browser also
        # submit a empty part without filename

    else:
      #configuring path and constraint to save images
      UPLOAD_FOLDER = 'static\images'
      ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
      app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
      def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

      if file.filename == '':
        print('No image selected')
        pass

      if file and allowed_file(file.filename):

        print(file.filename)
        filename = secure_filename(file.filename)
        basedir = os.path.abspath(os.path.dirname(__file__))
        file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
        # file.save(f'static/images/{filename}')
        file_name = f'/static/images/{filename}'

    data = {
            'title': title,
            'description': description,
            'image_url': file_name
        }      
                      
    url = 'http://127.0.0.1:8080/api/ViewBlogData/' + str(blog_id)
    response = requests.put(url, json=data)

    if response.status_code == 200:
      return redirect(url_for('profile'))
    else:
      return "error updating blog, check validity of blog id"
    

  else:
    response = requests.get('http://127.0.0.1:8080/api/ViewBlogData/' + str(blog_id))
    
    if response == 204:
      return "error getting blog, check the validity of blog id"
  
    blog_data = response.json()
    return render_template("editBlog.html",  blog_data = blog_data, user=current_user)


@app.route('/delete_blog/<blog_id>')
def delete_blog(blog_id):

  response = requests.delete('http://127.0.0.1:8080/api/ViewBlogData/' + str(blog_id))

  if response == 204:
      return "error getting blog, check the validity of blog id"
  
  
  data = response.json()
  return redirect(url_for('profile'))




@app.route('/delete/<Uid>')
def delete(Uid):
  
  
  response = requests.delete('http://127.0.0.1:8080/api/ProfileData/' + str(Uid))
  if response.status_code == 204:
    return "error getting user detail"

  if response.status_code == 200:
    data = response.json()
    flash(data)
    return redirect(url_for('SignUp'))


  
# end of profie related routes #

#route for getting share a post page and to upload title/description/image

@app.route('/post', methods=["GET", "POST"])
def post():
  if request.method == 'POST':

    title = request.form.get('title')
    description = request.form.get('description')
    file_name = None

    #configuring path and constraint to save images
    UPLOAD_FOLDER = 'static\images'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    def allowed_file(filename):
      return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # check if the post request has the file part
    if 'file' not in request.files:

      flash('No file part')
      return render_template("post.html", user=current_user)
    # if user does not select file, browser also
        # submit a empty part without filename
    file = request.files['file']
    if file.filename == '':
      flash('No image selected')
      return render_template("post.html", user=current_user)

    if file and allowed_file(file.filename):
      print(file.filename)
      filename = secure_filename(file.filename)
      basedir = os.path.abspath(os.path.dirname(__file__))
      file.save(os.path.join(basedir, app.config['UPLOAD_FOLDER'], filename))
      file_name = f'/static/images/{filename}'

    data = {
          'title': title,
          'description': description,
          'image_url': file_name,
          'user_Uid': current_user.Uid
      }      
                      
    url = 'http://127.0.0.1:8080/api/ViewBlogData'
    response = requests.post(url, json=data)

    if response.status_code == 200:
      
      return redirect(url_for('profile'))

    else:
      flash('api errror')
      return render_template("post.html", user=current_user)

  return render_template("post.html", user=current_user)

@app.route('/search')
def search():
    user = current_user
    q = request.args.get('q')
    Users = users.query.filter(users.username.like(f'%{q}%')).all()
    return render_template('search_result.html', Users = Users, user=current_user)





@app.route('/UserProfile/<Uid>', methods=["GET", "POST"])
def UserProfile(Uid):

  if request.method == 'POST':
    Uid = int(Uid, 10)
    following_status = None

    Other_user = db.session.query(users).filter(users.Uid == Uid).first()
    following_status = get_follow_status(Other_user.username)
    print(following_status)
    new_status = not following_status
    
    update_follow_status(Other_user.username, new_status)
    following_status = get_follow_status(Other_user.username)
    print(following_status)
  
    response = requests.get('http://127.0.0.1:8080/api/ProfileData/' + str(Other_user.Uid))
    data = response.json()

    blog_response = requests.get('http://127.0.0.1:8080/api/ProfileBlogsData/' + str(Other_user.Uid))
    blog_data = blog_response.json()

    if response.status_code == 204:
      return "error getting user details"
    
    if blog_response.status_code == 204:
      return render_template("user_profile_no_blogs.html", data=data ,  follow_status = following_status , user=current_user)
    
    return render_template("user_profile.html", data=data , blog_data =blog_data , follow_status = following_status , user=current_user)
    

  # user = current_user
  # code to check if current logged in user is following the opened profile
  Uid = int(Uid, 10)
  following_status = False

  Other_user = db.session.query(users).filter(users.Uid == Uid).first()

  following_status = get_follow_status(Other_user.username)
  
  response = requests.get('http://127.0.0.1:8080/api/ProfileData/' + str(Other_user.Uid)) 
  data = response.json()

  blog_response = requests.get('http://127.0.0.1:8080/api/ProfileBlogsData/' + str(Other_user.Uid))
  blog_data = blog_response.json()

  if response.status_code == 204:
      return "error getting user details"
    
  if blog_response.status_code == 204:
    return render_template("user_profile_no_blogs.html", data=data ,  follow_status = following_status , user=current_user)
    
  
  return render_template("user_profile.html", data=data , blog_data =blog_data , follow_status = following_status , user=current_user)


def update_follow_status(username, new_status):

  Other_user = db.session.query(users).filter(users.username == username).first()

  if new_status == True:
    current_user.n_following = current_user.n_following + 1
    Other_user.n_followers = Other_user.n_followers + 1

    new_follows = follows(following = Other_user.Uid , follower = current_user.Uid)
    db.session.add(new_follows)
    db.session.commit()
  
  if new_status == False:
    current_user.n_following = current_user.n_following - 1
    Other_user.n_followers = Other_user.n_followers - 1

    follow = db.session.query(follows).filter(follows.following == Other_user.Uid and follows.follower == current_user.Uid).first()
    db.session.delete(follow)
    db.session.commit()


api.add_resource(BrowseBlogsApi, "/api/BrowseBlogsApi","/api/BrowseBlogsApi/<string:Uid>")

# browse page route that displays users random interesting posts
@app.route('/browse', methods=["GET", "POST"])
def browse():
  
  blog_response = requests.get('http://127.0.0.1:8080/api/BrowseBlogsApi')
  
  blog_data = blog_response.json()
  
  if blog_response.status_code == 200:
    return render_template("browse.html", user=current_user, blog_data = blog_data)
  
  if blog_response.status_code == 204:
    return render_template("noBlogsBrowse.html", user=current_user)
  


if __name__ == '__main__':
  app.secret_key = 'appdev1'
  app.debug = True
  app.run(host='0.0.0.0', port=8080)

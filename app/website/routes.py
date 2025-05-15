import smtplib, os, json
from flask import Blueprint, render_template, request, jsonify, make_response
from app.extensions import db
from app.website.contact import send_email
from app.models.contact import Blog_Contact
from app.models.themes import Blog_Theme
from app.models.posts import Blog_Posts
from app.models.user import Blog_User
from app.models.likes import Blog_Likes
from app.models.bookmarks import Blog_Bookmarks
from app.models.comments import Blog_Comments, Blog_Replies
from app.models.helpers import update_likes, update_bookmarks, delete_comment, delete_reply
from flask_login import current_user
from datetime import datetime
from sqlalchemy import desc
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from os import listdir

directory_image_about = "app/static/Pictures_Liquet_About/"
directory_image_post = "app/static/Pictures_Liquet_Post/"
directory_image_theme = "app/static/Pictures_Themes/"

website = Blueprint('website', __name__,
                    static_folder="../static", template_folder="../template")
load_dotenv()

# Blog website pages: Home Page, All posts, About, Contact page
# Routes available for registered and non-registered users alike

def text():
    with open("app/static/JSON/about_text.json", "r") as about_file, \
        open("app/static/JSON/title_post.json", "r") as post_file, \
        open("app/static/JSON/post.json", "r") as isi_file:

        about_data = json.load(about_file)
        post_data = json.load(post_file)
        isi_data = json.load(isi_file)
        return {
            "isi_about_data" : about_data,
            "isi_post_data" : post_data,
            "isi_isi_data" : isi_data
        }
    
def theme_photo():
    folder_theme = "/static/Pictures_Themes/"
    files = os.listdir(folder_theme)
    images = []
    for file in files:
        if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            images.append(folder_theme + '/' + file)
    return images

#ROUTE HALAMAN HOME LAMA
# @website.route("/")
# def home():
#     # query database for themes while getting picture src
#     posts_themes = [(u.theme, u.picture, u.id)
#                     for u in db.session.query(Blog_Theme).all()]
#     theme_list = [t[2] for t in posts_themes]
    
#     # query posts to get the latest 3 posts of each theme. 
#     # Important note: the code bellow is not maintainable if we increase the number of themes, but I could not achieve a better result on my own.
#     # This should be improved.
#     # The code also selects the forth theme's query results' ids to identify these posts, as this is the only group of posts displayed separately in index.html
#     posts_all = []
#     forth_theme_post_ids = []
#     for num_themes in theme_list:
#         query = db.session.query(Blog_Posts).filter(
#                 Blog_Posts.admin_approved == "TRUE", Blog_Posts.date_to_post <= datetime.utcnow(),
#             Blog_Posts.theme_id == num_themes).order_by(desc(Blog_Posts.date_to_post)).limit(3)
#         posts_all.append(query.all())
#         if num_themes == 4:
#             for this_query in query:
#                 forth_theme_post_ids.append(this_query.id)
#     posts_all = posts_all[0] + posts_all[1] + posts_all[2] + posts_all[3]

#     return render_template('website/index_lama.html', posts_all=posts_all, posts_themes=posts_themes, logged_in=current_user.is_authenticated, forth_theme_post_ids=forth_theme_post_ids)

@website.route("/")
def home():
    image_files = [
        img for img in os.listdir(directory_image_theme)
        if img.endswith(('.jpg', '.jpeg', 'png', '.gif', 'webp'))
    ]

    items = [
        {
            "id" : os.path.splitext(image_files[i])[0],
            "image" : '/static/Pictures_Themes/' + image_files[i]
        }
        for i, image in enumerate(image_files)
    ]
    return render_template('website/index.html', hasil = items)

#FUNGSI HALAMAN ALL LAMA
# route to 'All Posts' page or page by chosen theme
# @website.route("/all/<int:index>")
# def all(index):
#     index = int(index)
#     all_blog_posts = None
#     chosen_theme = ""
#     intros = []
#     if index != 0:
#         chosen_theme = db.session.query(
#             Blog_Theme).filter(Blog_Theme.id == index).first().theme
#         all_blog_posts = db.session.query(Blog_Posts).filter(Blog_Posts.theme_id == index,
#             Blog_Posts.admin_approved == "TRUE", Blog_Posts.date_to_post <= datetime.utcnow(),
#         ).order_by(desc(Blog_Posts.date_to_post)).limit(25)
#     else:
#         all_blog_posts = db.session.query(Blog_Posts).filter(
#             Blog_Posts.admin_approved == "TRUE", Blog_Posts.date_to_post <= datetime.utcnow(),
#             ).order_by(desc(Blog_Posts.date_to_post)).limit(25)
#     for post in all_blog_posts:
#         if len(post.intro) > 300:
#             cut_intro_if_too_long = f"{post.intro[:300]}..."
#             intros.append(cut_intro_if_too_long)
#         else:
#             intros.append(post.intro)

#     return render_template('website/contoh_all_post.html', all_blog_posts=all_blog_posts, chosen_theme=chosen_theme, intros=intros, logged_in=current_user.is_authenticated)

@website.route("/all")
def all():
    text_data = text()
    isi = []
    post_data = list(text_data.get("isi_post_data", {}).get("post", {}).values())
    for item in post_data:
        if len(item["content"]) > 150:
            cut_intro_if_too_long = f"{item["content"][:150]}..."
            isi.append(cut_intro_if_too_long)
    image_files = [
        img for img in os.listdir(directory_image_post)
        if img.endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    
    items = [
        {
            "id" : post_data[i]["id"],
            "image" : post_data[i]["image"],
            "title" : post_data[i]["title"]
                if i < len(post_data)
                    else "Default title",
            "content" : isi[i]
                if i < len(isi)
                    else "Default content"
        }
        for i, image in enumerate(image_files)
    ]
    print(items)
    return render_template('website/all_posts.html', items = items)

#FUNGSI ABOUT LAMA, UNTUK AMBIL SEMUA FOTO DI DATABASE
# @website.route("/about/")
# def about():
#     authors_all = db.session.query(Blog_User).filter(
#         Blog_User.blocked == "FALSE", Blog_User.type == "author",
#         ).order_by(desc(Blog_User.id)).limit(25)
#     return render_template('website/about.html', authors_all=authors_all, logged_in=current_user.is_authenticated)

@website.route("/about/")
def about():
    text_data = text()
    about_data = list(text_data.get("isi_about_data", {}).get("about", {}).values())
    image_files = [
        img for img in os.listdir(directory_image_about)
        if img.endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]

    items = [
        {
            "image" : f"/static/Pictures_Liquet_About/{image}",
            "title" : about_data[i]["title"] 
                if i < len(about_data) 
                    else "Default title",
            "content" : about_data[i]["content"] 
                if i < len(about_data) 
                    else "Default content"
        }
        for i, image in enumerate(image_files)
    ]
    
    return render_template('website/about.html', items = items)  

# FUNGSI CONTACT LAMA
# @website.route("/contact/", methods=['POST', 'GET'])
# def contact():
#     if request.method == "POST":
#         contact_name = request.form['contact_name']
#         contact_email = request.form['contact_email']
#         contact_message = request.form['contact_message']
#         new_contact = Blog_Contact(
#             name=contact_name, email=contact_email, message=contact_message)
#         try:
#             # push to database:
#             db.session.add(new_contact)
#             db.session.commit()
#             # send email:
#             send_email(contact_name, contact_email, contact_message)
#             return render_template('website/contact.html', msg_sent=True, logged_in=current_user.is_authenticated)
#         except:
#             return "There was an error adding message to the database."
#     return render_template('website/contact.html', msg_sent=False, logged_in=current_user.is_authenticated)

@website.route("/contact/", methods=['POST', 'GET'])
def contact():
    if request.method == "POST":
        SMTP_Server = "smtp.gmail.com"
        SMTP_Port = 587
        SMTP_Email = os.getenv("SMTP_EMAIL")
        SMTP_Password = os.getenv("SMTP_PASSWORD")
        recipients = ["hendratmobudihardjo@gmail.com", "onggaralidya25@gmail.com"]
        contact_name = request.form['contact_name']
        contact_email = request.form['contact_email']
        contact_message = request.form['contact_message']
        try:
            message = MIMEMultipart()
            message["Reply-To"] = contact_email
            message["To"] = ", ".join(recipients)
            message["Subject"] = f"Message from {contact_name}"
            message.attach(MIMEText(contact_message, "plain"))
            s = smtplib.SMTP(SMTP_Server, SMTP_Port)
            s.starttls()
            s.login(SMTP_Email, SMTP_Password)
            s.sendmail(SMTP_Email, recipients, message.as_string())
            s.quit()
            return render_template('website/contact.html', msg_sent=True, logged_in=current_user.is_authenticated)
        except:
            return "There was an error adding message to the database."
    return render_template('website/contact.html', msg_sent=False, logged_in=current_user.is_authenticated)


#FUNGSI POST LAMA
# @website.route("/post/<int:index>", methods=["GET", "POST"])
# def blog_post(index):
#     # get the post
#     blog_post = db.session.query(Blog_Posts).filter(Blog_Posts.id == index,
#                                                     Blog_Posts.admin_approved == "TRUE", Blog_Posts.date_to_post <= datetime.utcnow(),
#                                                     ).order_by(Blog_Posts.date_submitted.desc()).first()
#     # get the likes
#     post_likes = db.session.query(Blog_Likes).filter(
#         Blog_Likes.post_id == index).all()

#     # check if user is logged in, and if so, already liked or bookmarked this post
#     user_liked = False
#     user_bookmarked = False
#     if current_user.is_authenticated:
#         like = db.session.query(Blog_Likes).filter(
#             Blog_Likes.user_id == current_user.id, Blog_Likes.post_id == index).first()
#         bookmark = db.session.query(Blog_Bookmarks).filter(
#             Blog_Bookmarks.user_id == current_user.id, Blog_Bookmarks.post_id == index).first()
#     else:
#         like = False
#         bookmark = False
#     if like:
#         user_liked = True
#     if bookmark:
#         user_bookmarked = True
#     # get the comments
#     comments = db.session.query(Blog_Comments).filter(
#         Blog_Comments.post_id == index).order_by(Blog_Comments.date_submitted.desc()).limit(25)
#     # get the replies
#     replies = db.session.query(Blog_Replies).filter(Blog_Replies.post_id == index,
#                                                     ).order_by(Blog_Replies.date_submitted.asc()).limit(100)
#     return render_template('website/post_lama.html', blog_posts=blog_post, logged_in=current_user.is_authenticated, comments=comments, replies=replies, post_likes=post_likes, user_liked=user_liked, user_bookmarked=user_bookmarked)

@website.route("/post/<int:index>", methods=["GET", "POST"])
def blog_post(index):
    index = index - 1
    text_data = text()
    isi_dict = text_data.get('isi_isi_data', {}).get('Isi', {})
    outer_keys = list(isi_dict)
    if index < 0 or index >= len(outer_keys):
        return "Post Not Found", 404
    
    selected_key = outer_keys[index]
    post_dict = isi_dict.get(selected_key, {})
    post_list = list(post_dict.values())
    
    items = []
    for post in post_list:
        items.append({
            "id" : post.get("id"),
            "title" : post.get("title"),
            "short_title" : post.get("short_title"),
            "content" : post.get("content"),
            "image" : post.get("image"),
            "description" : post.get("description"),
            "judul" : selected_key
    })
    return render_template('website/post.html', items = items)

# Comment or reply on post
@website.route("/comment_post/<int:index>", methods=["POST"])
def post_comment(index):
    data = request.get_json()
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.get_json()
        if not data.get('comment') and not data.get('reply'):
            return make_response(jsonify({"message": "Comment empty"}), 400)
        if data.get('reply') and not data.get('comment'):
            # add reply
            reply = Blog_Replies(
                text=data.get('reply'), post_id=index, user_id=current_user.id, comment_id=int(data.get('commentId')))
            db.session.add(reply)
            db.session.commit()
            return make_response(jsonify({"message": "Reply added"}), 200)
        elif data.get('comment') and not data.get('reply'):
            # add comment
            comment = Blog_Comments(
                text=data.get('comment'), post_id=index, user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            return make_response(jsonify({"message": "Comment added"}), 200)
        else:
            return make_response(jsonify({"message": "Must be either a comment or a reply"}), 400)
    else:
        return make_response(jsonify({"message": "Content type not supported"}), 412)

# Delete comment or reply
@website.route("/delete_comment_or_reply/<int:index>", methods=["POST"])
def post_delete_comment(index):
    data = request.get_json()
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.get_json()
        if not data.get('commentId') and not data.get('replyId'):
            return make_response(jsonify({"message": "Nothing to delete"}), 400)
        if data.get('replyId') and not data.get('commentId'):
            # delete reply
            res = delete_reply(int(data.get('replyId')))
            if res == "success":
                return make_response(jsonify({"message": "Successfully deleted"}), 200)
            else:
                return make_response(jsonify({"message": "Reply not found"}), 404)
        elif data.get('commentId') and not data.get('replyId'):
            # delete comment
            res = delete_comment(int(data.get('commentId')))
            if res == "success":
                return make_response(jsonify({"message": "Successfully deleted"}), 200)
            else:
                return make_response(jsonify({"message": "Comment not found"}), 404)
        else:
            return make_response(jsonify({"message": "Must be either a commentId or a replyId"}), 400)
    else:
        return make_response(jsonify({"message": "Content type not supported"}), 412)

# Like post request sent by JavaScript
@website.route("/like_post/<int:index>", methods=["POST"])
def post_like(index):
    # check if post exists
    post = db.session.query(Blog_Posts).filter_by(id=index)
    if not post:
        return jsonify({"error":"post does not exist"}, 400)
    # check how many likes this post has
    post_likes = db.session.query(Blog_Likes).filter(
        Blog_Likes.post_id == index).all()

    # check if user already liked this post
    like = db.session.query(Blog_Likes).filter(
        Blog_Likes.user_id == current_user.id, Blog_Likes.post_id == index).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        update_likes(-1)
        has_liked = "false"
    else:
        like = Blog_Likes(user_id=current_user.id, post_id=index)
        db.session.add(like)
        db.session.commit()
        update_likes(1)
        has_liked = "true"
    return jsonify({"likes": len(post_likes), "user_liked": has_liked})

# Bookmark post request sent by JavaScript
@website.route("/bookmark_post/<int:index>", methods=["POST"])
def post_bookmark(index):
    # check if post exists
    post = db.session.query(Blog_Posts).filter_by(id=index)
    if not post:
        return jsonify({"error": "post does not exist"}, 400)

    # check if user already bookmarked this post to decide whether to add or remove the bookmark
    bookmark = db.session.query(Blog_Bookmarks).filter(
        Blog_Bookmarks.user_id == current_user.id, Blog_Bookmarks.post_id == index).first()
    if bookmark:
        db.session.delete(bookmark)
        db.session.commit()
        update_bookmarks(-1)
        has_bookmarked = "false"
    else:
        bookmark = Blog_Bookmarks(user_id=current_user.id, post_id=index)
        db.session.add(bookmark)
        db.session.commit()
        update_bookmarks(1)
        has_bookmarked = "true"
    return jsonify({"user_bookmarked": has_bookmarked})

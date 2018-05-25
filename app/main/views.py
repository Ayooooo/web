from datetime import datetime
from flask import render_template,session,redirect,url_for,request,flash,abort,jsonify
from flask_login import login_required,current_user
from flask_mail import current_app
from . import main
from .forms import  PostForm
from .. import  db
from ..models import User,Permission,Post

@main.route('/post',methods=['GET','POST'])
def index():
    form =PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return jsonify({'posts': [post.to_json() for post in posts] })
    '''page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination, Permission=Permission)
'''
@main.route('/post/<int:id>',methods=['POST'])
def new_post():
    post = Post.from_json(request.json)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, {'Location': url_for('main.get_post', id=post.id, _external=True)}


@main.route('/user/<username>')
def user(username):
   user=User.query.filter_by(username=username).first()
   if User is None:
       abort(404)
   posts=user.posts.order_by(Post.timestamp.desc()).all()
   return render_template('user.html',user=user,posts=posts)


@main.route('/post/<int:id>',methods=['GET'])
def post(id):
   post=Post.query.get_or_404(id)
   return jsonify({'post':post.to_json()})


@main.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit(id):
   post=Post.query.get_or_404(id)
   if current_user!=post.author and not current_user.can(PermissionError.ADMINISTER):
       abort(403)
   form = PostForm()
   if form.validate_on_submit():
       post.body=form.body.data
       db.session.add(post)
       flash('The post has been updated.')
       return redirect(url_for('main.post',id=post.id))
   form.body.data=post.body
   return render_template('edit_post.html',form=form)




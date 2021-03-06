from datetime import datetime
from flask import render_template,session,redirect,url_for,request,flash,abort
from flask_login import login_required,current_user
from flask_mail import current_app
from . import main
from .forms import  PostForm
from .. import  db
from ..models import User,Permission,Post

'''
@main.route('/', methods=['GET','POST'])
def index():
    form=PostForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.name.data).first()
        if user is None:
            user=User(username=form.name.data)
            db.session.add(user)
            session['known']=False
        else:
            session['known']=True
        session['name']=form.name.data
        form.name.data=''
        return redirect(url_for('.index'))
    return render_template('index.html',form=form,name=session.get('name'),Permission=Permission,known=session.get('known',False),current_time=datetime.utcnow())

'''
@main.route('/',methods=['GET','POST'])
def index():
    form =PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post=Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    posts=Post.query.order_by(Post.timestamp.desc()).all
    page=request.args.get('page',1,type=int)
    pagination=Post.query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts=pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination, Permission=Permission)

@main.route('/user/<username>')
def user(username):
    user=User.query.filter_by(username=username).first()
    if User is None:
        abort(404)
    posts=user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

@main.route('/post/<int:id>')
def post(id):
    post=Post.query.get_or_404(id)
    return render_template('post.html',posts=[post])

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




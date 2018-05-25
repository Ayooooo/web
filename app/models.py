from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from markdown import markdown
import bleach
from . import db
from flask_moment import datetime
from flask import current_app,url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Permission:
    FOLLOW=0X01
    COMMENT=0X02
    WRITE_ARTICLES=0X04
    MODERATE_COMMENTS=0X08
    ADMINISTER=0X80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default=db.Column(db.Boolean,default=False,index=True)
    permissions=db.Column(db.Integer)
    users=db.relationship('User',backref='role',lazy='dynamic')
    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.WRITE_ARTICLES, True),
            'Moderator':(Permission.FOLLOW |
                            Permission.COMMENT |
                            Permission.WRITE_ARTICLES |
                            Permission.MODERATE_COMMENTS, False),
            'Administrator':(0xff, False)
            }
        for r in roles:
            role=Role.query.filter_by(name=r).first()
            if role is None:
                role =Role(name=r)
            role.permissions=roles[r][0]
            role.default=roles[r][1]
            db.session.add(role)
        db.session.commit()

class User(UserMixin,db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True,index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash=db.Column(db.String(128))
    role_id=db.Column(db.Integer,db.ForeignKey('roles.id'))
    posts=db.relationship('Post',backref='author',lazy='dynamic')
    confirmed=db.Column(db.Boolean,default=False)
    name=db.Column(db.String(64))
    location=db.Column(db.String(64))
    about_me=db.Column(db.Text())
    member_since=db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen=db.Column(db.DateTime(),default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['FLASKY_ADMIN']:
                self.role=Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role=Role.query.filter_by(permissions=0x07).first()


    password_hash=db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash=generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions)==permissions

    def is_administrator(self):
        return False

    def ping(self):
        self.last_seen=datetime.utcnow()
        db.session.add(self)

    def generate_confirmation_token(self,expiration=3600):
        s=Serializer(current_app.config['SECRET_KEY'],expiration)
        return  s.dumps({'confirm':self.id})

    def confirm(self,token):
        s=Serializer(current_app.config['SECRET_KEY'])
        try:
            data=s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed=True
        db.session.add(self)
        return True

class AnonymousUser(AnonymousUserMixin):
    def can(self,permissions):
        return False
    def is_administrator(self):
        return False

login_manager.anonymous_user=AnonymousUser

class Post(db.Model):
    tablename='posts'
    id=db.Column(db.Integer,primary_key=True)
    body=db.Column(db.Text)
    timestamp=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id=db.Column(db.Integer,db.ForeignKey('users.id'))
    body_html=db.Column(db.Text)

    def to_json(self):
        json_post={
            'url':url_for('main.post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'id':self.id
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body=json_post.get('body')
        timestamp=json_post.get('timestamp')
        author=json_post.get('author')
        return Post(body=body,timestamp=timestamp,author=author)

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count=User.query.count()
        for i in range(count):
            u=User.query.offset(randint(0,user_count-1)).first()
            p=Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                   timestamp=forgery_py.date.date(True),
                   author=u)
            db.session.add(p)
            db.session.commit()


    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags=['a','abbr','acronym','b','blockquote','code','em','i','li','ol','pre','strong',
                      'ul','h1','h2','h3','p']
        target.body_html=bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))

db.event.listen(Post.body,'set',Post.on_changed_body)
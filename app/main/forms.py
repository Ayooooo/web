from flask_wtf import FlaskForm
from wtforms import SubmitField,TextAreaField
from wtforms.validators import Required
from flask_pagedown.fields import PageDownField

class PostForm(FlaskForm):
    body=PageDownField("What's on your mind?", validators=[Required()])
    submit=SubmitField('Submit')
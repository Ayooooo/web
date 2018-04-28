from flask_wtf import Form
from wtforms import SubmitField,TextAreaField
from wtforms.validators import Required
from flask_pagedown.fields import PageDownField

class PostForm(Form):
    body=PageDownField("What's on your mind?", validators=[Required()])
    submit=SubmitField('Submit')
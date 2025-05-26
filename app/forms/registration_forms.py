from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from flask_wtf.file import FileRequired, FileAllowed
from datetime import datetime

class DocumentUploadForm(FlaskForm):
    name = StringField('Document Name', validators=[DataRequired(), Length(min=3, max=120)])
    document_type = SelectField('Document Type', 
                               choices=[('Certificate', 'Certificate'), 
                                       ('Form', 'Form'),
                                       ('Constitution', 'Constitution/M&AOA'),
                                       ('Financial Statement', 'Financial Statement'),
                                       ('Annual Report', 'Annual Report'),
                                       ('Work Plan', 'Work Plan'),
                                       ('Budget', 'Budget'),
                                       ('Minutes', 'Minutes'),
                                       ('Other', 'Other')],
                               validators=[DataRequired()])
    document = FileField('Document File', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'], 'Only PDF, Word, text, and image files are allowed')
    ])
    submit = SubmitField('Upload Document')

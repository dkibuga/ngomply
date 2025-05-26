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

'''class OrganizationRegistrationForm(FlaskForm):
    organization_name = StringField('Organization Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    organization_type = SelectField('Organization Type', 
                                  choices=[('ngo', 'NGO'), ('company', 'Company'), ('government', 'Government')],
                                  validators=[DataRequired()])
    submit = SubmitField('Register Organization')
    '''
class OrganizationRegistrationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(min=3, max=120)])
    org_type = SelectField('Organization Type', 
                          choices=[('NGO', 'Non-Governmental Organization (NGO)'), 
                                  ('CBO', 'Community-Based Organization (CBO)')],
                          validators=[DataRequired()])
    ngo_type = SelectField('NGO Type', 
                          choices=[('National', 'National NGO'), 
                                  ('International', 'International NGO'),
                                  ('Regional', 'Regional NGO'),
                                  ('District', 'District NGO')],
                          validators=[Optional()])
    address = TextAreaField('Address', validators=[DataRequired(), Length(min=5, max=200)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Register Organization')

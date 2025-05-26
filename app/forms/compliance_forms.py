from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField, SubmitField, FileField
from wtforms.validators import DataRequired, Email, Optional
from datetime import datetime

class ComplianceTaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired()])
    description = TextAreaField('Task Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()], default=datetime.utcnow)
    task_type = SelectField('Task Type', 
                          choices=[('Financial', 'Financial'), 
                                  ('Reporting', 'Reporting'),
                                  ('Planning', 'Planning'),
                                  ('Audit', 'Audit'),
                                  ('Tax', 'Tax'),
                                  ('Other', 'Other')],
                          validators=[DataRequired()])
    submit = SubmitField('Add Task')

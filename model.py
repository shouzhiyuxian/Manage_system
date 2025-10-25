from email.policy import default
from mako.ext.autohandler import autohandler
from sqlalchemy.orm import backref, foreign
from datetime import datetime
from settings import db
import cpca
association_table = db.Table('association',
                             db.Column('user_stu_id', db.Integer, db.ForeignKey('user.stu_id')),
                             db.Column('work_id', db.Integer, db.ForeignKey('work_info.id'))
                             )


class User(db.Model):
    stu_id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    sex = db.Column(db.String(5), nullable=True)
    name = db.relationship('Stu_info', backref='user', lazy='dynamic')
    phone = db.Column(db.String(11))
    address = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(20), nullable=True)
    isadmin = db.Column(db.Integer, default=0)
    work_info = db.relationship('Work_info', secondary=association_table, back_populates='user')

    def __repr__(self):
        return f'<User {self.stu_id}>'


class Stu_info(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    stu_id = db.Column(db.Integer, db.ForeignKey('user.stu_id'))
    grade = db.Column(db.String(10))
    department_id = db.Column(db.Integer)
    department_name = db.Column(db.String(50))
    major_id = db.Column(db.Integer)
    major_name = db.Column(db.String(50))
    class_id = db.Column(db.Integer)
    work_info = db.relationship('Work_info', backref='stu_info', lazy='dynamic')
    internship_positions = db.Column(db.String(100))
    score = db.Column(db.Float)

    def __repr__(self):
        return f'<Stu_info {self.id}>'


class Work_info(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stu_info_id = db.Column(db.Integer, db.ForeignKey('stu_info.id'))
    name = db.Column(db.String(50))
    position = db.Column(db.String(100))
    user = db.relationship('User', secondary=association_table, back_populates='work_info')

    def __repr__(self):
        return f'<Work_info {self.name}>'


class FeedBack(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user1_name = db.Column(db.String(50))
    feedback = db.Column(db.Text)
    teacher_text = db.Column(db.Text)
    user2_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def formatted_created_at(self):
        return self.created_at.strftime('%Y年/%m月/%d日 %H时/%M分/%S秒')

    def __repr__(self):
        return f'<Feed {self.id}>'


class Excellent_stu_application(db.Model):
    stu_name = db.Column(db.String(50))
    sex = db.Column(db.String(5))
    stu_id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(10))
    department = db.Column(db.String(50))
    major = db.Column(db.String(50))
    class_id = db.Column(db.Integer)
    work_name = db.Column(db.String(50))
    begin_date = db.Column(db.DateTime)  # 实习开始时间
    end_date = db.Column(db.DateTime)
    approval_date = db.Column(db.DateTime, default=datetime.now)  # 审批提交时间
    state = db.Column(db.String(10), default='未处理')
    mentor = db.Column(db.String(20))
    reason = db.Column(db.String(400))

    def formatted_begin_date(self):
        return self.begin_date.strftime('%Y年/%m月/%d日 %H时/%M分/%S秒')

    def formatted_approval_date(self):
        return self.approval_date.strftime('%Y年/%m月/%d日 %H时/%M分/%S秒')

    def __repr__(self):
        return f'<Application {self.stu_id}>'


class Excellent_stu_info(db.Model):
    stu_name = db.Column(db.String(50))
    sex = db.Column(db.String(5))
    stu_id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.String(10))
    department = db.Column(db.String(50))
    major = db.Column(db.String(50))
    class_id = db.Column(db.Integer)
    work_name = db.Column(db.String(50))
    begin_date = db.Column(db.DateTime)  # 实习开始时间
    end_date = db.Column(db.DateTime)
    mentor = db.Column(db.String(20))


class Department_info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(20))
    major = db.relationship('Major_info', backref='department_info', lazy='dynamic')


class Major_info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    major_name = db.Column(db.String(20))
    department_id = db.Column(db.Integer, db.ForeignKey('department_info.id'))
    department_name = db.Column(db.String(20))


class SignInRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.stu_id'))
    student_name = db.Column(db.String(20), nullable=False)
    sign_in_time = db.Column(db.DateTime, default=datetime.now)
    location = db.Column(db.String(120))


    def formatted_sign_in_time(self):
        return self.sign_in_time.strftime('%Y年/%m月/%d日 %H时/%M分/%S秒')

    @property
    def is_abnormal(self):
        # 获取学生关联的工作信息
        user = User.query.get(self.student_id)
        if not user or not user.work_info:
            return True

        # 获取工作地点（假设取第一个工作信息）
        work_location = user.work_info[0].position

        # 解析地点信息
        sign_province, sign_city = self.parse_region(self.location)
        work_province, work_city = self.parse_region(work_location)

        return not (sign_province == work_province and sign_city == work_city)

    @staticmethod
    def parse_region(address):
        """使用cpca库解析省市区"""
        df = cpca.transform([address])
        return df.iloc[0]['省'], df.iloc[0]['市']


class WeeklyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer)
    stu_id = db.Column(db.Integer)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    main_content = db.Column(db.Text)
    summary = db.Column(db.Text)
    # student_signature = db.Column(db.String(100))
    # student_sign_date = db.Column(db.Date)
    teacher_feedback = db.Column(db.Text)
    attachment_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    daily_records = db.relationship('DailyRecord', backref='report', lazy=True)
    dim_skill = db.Column(db.Integer)
    dim_attitude = db.Column(db.Integer)
    dim_teamwork = db.Column(db.Integer)
    dim_task = db.Column(db.Integer)
    dim_innovation = db.Column(db.Integer)


class DailyRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stu_id = db.Column(db.Integer)
    day_number = db.Column(db.Integer)
    work_time = db.Column(db.Time)
    location = db.Column(db.String(100))
    content = db.Column(db.Text)
    report_id = db.Column(db.Integer, db.ForeignKey('weekly_report.id'))

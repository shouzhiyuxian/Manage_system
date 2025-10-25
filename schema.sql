-- 创建 association 表
CREATE TABLE association (
    user_stu_id INTEGER,
    work_id INTEGER,
    FOREIGN KEY(user_stu_id) REFERENCES user(stu_id),
    FOREIGN KEY(work_id) REFERENCES work_info(id)
);

-- 创建 user 表
CREATE TABLE user (
    stu_id INTEGER NOT NULL AUTO_INCREMENT,
    password VARCHAR(255) NOT NULL,
    sex VARCHAR(5),
    phone VARCHAR(11),
    address VARCHAR(30),
    email VARCHAR(20),
    isadmin INTEGER DEFAULT 0,
    PRIMARY KEY (stu_id)
);

-- 创建 stu_info 表
CREATE TABLE stu_info (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(20) NOT NULL,
    stu_id INTEGER,
    grade VARCHAR(10),
    department_id INTEGER,
    department_name VARCHAR(50),
    major_id INTEGER,
    major_name VARCHAR(50),
    class_id INTEGER,
    internship_positions VARCHAR(100),
    score FLOAT,
    PRIMARY KEY (id),
    FOREIGN KEY(stu_id) REFERENCES user(stu_id)
);

-- 创建 work_info 表
CREATE TABLE work_info (
    id INTEGER NOT NULL AUTO_INCREMENT,
    stu_info_id INTEGER,
    name VARCHAR(50),
    position VARCHAR(100),
    PRIMARY KEY (id),
    FOREIGN KEY(stu_info_id) REFERENCES stu_info(id)
);

-- 创建 feedback 表
CREATE TABLE feedback (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user1_name VARCHAR(50),
    feedback TEXT,
    teacher_text TEXT,
    user2_name VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- 创建 excellent_stu_application 表
CREATE TABLE excellent_stu_application (
    stu_name VARCHAR(50),
    sex VARCHAR(5),
    stu_id INTEGER NOT NULL AUTO_INCREMENT,
    grade VARCHAR(10),
    department VARCHAR(50),
    major VARCHAR(50),
    class_id INTEGER,
    work_name VARCHAR(50),
    begin_date DATETIME,
    end_date DATETIME,
    approval_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    state VARCHAR(10) DEFAULT '未处理',
    mentor VARCHAR(20),
    reason VARCHAR(400),
    PRIMARY KEY (stu_id)
);

-- 创建 excellent_stu_info 表
CREATE TABLE excellent_stu_info (
    stu_name VARCHAR(50),
    sex VARCHAR(5),
    stu_id INTEGER NOT NULL AUTO_INCREMENT,
    grade VARCHAR(10),
    department VARCHAR(50),
    major VARCHAR(50),
    class_id INTEGER,
    work_name VARCHAR(50),
    begin_date DATETIME,
    end_date DATETIME,
    mentor VARCHAR(20),
    PRIMARY KEY (stu_id)
);

-- 创建 department_info 表
CREATE TABLE department_info (
    id INTEGER NOT NULL AUTO_INCREMENT,
    department_name VARCHAR(20),
    PRIMARY KEY (id)
);

-- 创建 major_info 表
CREATE TABLE major_info (
    id INTEGER NOT NULL AUTO_INCREMENT,
    major_name VARCHAR(20),
    department_id INTEGER,
    department_name VARCHAR(20),
    PRIMARY KEY (id),
    FOREIGN KEY(department_id) REFERENCES department_info(id)
);

-- 创建 sign_in_record 表
CREATE TABLE sign_in_record (
    id INTEGER NOT NULL AUTO_INCREMENT,
    student_id INTEGER,
    student_name VARCHAR(20) NOT NULL,
    sign_in_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(120),
    PRIMARY KEY (id),
    FOREIGN KEY(student_id) REFERENCES user(stu_id)
);

-- 创建 weekly_report 表
CREATE TABLE weekly_report (
    id INTEGER NOT NULL AUTO_INCREMENT,
    week_number INTEGER,
    stu_id INTEGER,
    start_date DATE,
    end_date DATE,
    main_content TEXT,
    summary TEXT,
    teacher_feedback TEXT,
    attachment_path VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dim_skill INTEGER,
    dim_attitude INTEGER,
    dim_teamwork INTEGER,
    dim_task INTEGER,
    dim_innovation INTEGER,
    PRIMARY KEY (id)
);

-- 创建 daily_record 表
CREATE TABLE daily_record (
    id INTEGER NOT NULL AUTO_INCREMENT,
    stu_id INTEGER,
    day_number INTEGER,
    work_time TIME,
    location VARCHAR(100),
    content TEXT,
    report_id INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY(report_id) REFERENCES weekly_report(id)
);

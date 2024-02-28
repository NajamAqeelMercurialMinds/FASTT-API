from sqlalchemy import Column,Integer,String,Table,ForeignKey
from sqlalchemy.orm import relationship
from database import Base



student_course_association = Table(
    'student_course_association',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Student(Base):
    __tablename__='students'

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(50),unique=True)
    courses = relationship('Course', secondary=student_course_association, back_populates='students')

class Course(Base):
    __tablename__ ='courses'

    id=Column(Integer,primary_key=True,index=True)
    course=Column(String(50))

    students = relationship('Student', secondary=student_course_association, back_populates='courses')

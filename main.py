
import traceback
from fastapi import FastAPI,Depends,HTTPException,UploadFile, File
from pydantic import BaseModel
#from routes.index import StudentBase
from typing import Annotated
from sqlalchemy import and_, delete
from sqlalchemy.sql import text
import models
import csv
from fastapi.middleware.cors import CORSMiddleware
from database import engine,SessionLocal
from sqlalchemy.orm import Session
#from models import Table

app = FastAPI()

#app.include_router(StudentBase)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(bind=engine)

class CourseBase(BaseModel):
    course:str

class StudentBase(BaseModel):
    name:str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency= Annotated[Session,Depends(get_db)]

#---------------------------------------------------------------------------------------------Get API's------------------------------------------------
@app.get("/",response_model=list[StudentBase])
async def read_all_data(db:db_dependency):
    try:
        query = text("SELECT * FROM students;")
        
        result =  db.execute(query).all()
        if(not result):
           return "No records found"
        # Convert the result to a list of dictionaries
        return result
    except Exception as e:
        print("Error occurred:", e)
        return {"error": "An error occurred while fetching data from the database"}
    

    #----------------------------------------------------------------------

@app.get("/getspecificstudent/{id}")
async def read_data(id: int,  db: Session = Depends(get_db)):                        #------------
    
        try:
           existing_student = db.query(models.Student).filter(models.Student.id == id).first()
          # result = db_dependency.execute(existing_student).all()
           

           if not existing_student:

              raise HTTPException(status_code=404, detail="Student not found")
           return existing_student
        
        except Exception as e:
            print("Error occurred:", e)
            return {"error": "Student not Found"}

#----------------------------------------------------------------------

@app.get("/students/{student_id}/courses")
def get_student_with_courses(student_id: int, db: db_dependency):
    # Retrieve student from the database
    student = db.query(models.Student).filter(models.Student.id == student_id).first()

    # Check if student exists
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Access the assigned courses of the student
    courses = [{"id": course.id, "name": course.course} for course in student.courses]

    return {"student": {"id": student.id, "name": student.name}, "courses": courses}


#---------------------------------------------------------------------------------------------Update API's-----------------------------------------
@app.put("/updatestudent/{student_id}")
async def update_data(id: int, updatedstudent: StudentBase,db:Session=Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.id == id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        student.name=updatedstudent.name
        db.commit()
        return {"message": "Student Updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update student")
 
 #---------------------------------------------------------------------- 
    
@app.put("/updatecourse/{Course_id}")
async def update_data(id: int, updatedcourse: CourseBase,db:Session=Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        course.course=updatedcourse.course
        db.commit()
        return {"message": "Course Updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update student")
    
#---------------------------------------------------------------------------------------------Delete API's--------------------------------------
    
@app.delete("/deletestudents/{student_id}")
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    # Query the student by ID
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        db.delete(student)
        db.commit()
        return {"message": "Student deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete student")

    #----------------------------------------------------------------------


    
@app.delete("/deletestudentfromCourse/{student_id}/courses/{course_id}")
async def delete_student_fromCourse(student_id: int, course_id: int, db: Session = Depends(get_db)):
   
    try:
      
      stmt = delete(models.student_course_association).where((models.student_course_association.c.student_id == student_id) & (models.student_course_association.c.course_id == course_id)         )        
      db.execute(stmt)
      db.commit()
      return {"message": "Student deleted from course successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to delete student from course")

#----------------------------------------------------------------------
    
@app.delete("/deleteCourse/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(get_db)):
    # Query  Course by ID
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        db.delete(course)
        db.commit()
        return {"message": "Course deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete Course")

#----------------------------------------------------------------------------------------------------------Add API's---------------------------------
    
@app.post("/students/{student_id}/courses/{course_id}")
def add_student_to_course(student_id: int, course_id: int, db:db_dependency):
    # Retrieve student and course from the database
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    course = db.query(models.Course).filter(models.Course.id == course_id).first()

    # Check if student and course exist
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    

      # Check if the student is already enrolled in the course
    if student in course.students:
        raise HTTPException(status_code=400, detail="Student already enrolled in course")

    # Add the student to the course
    course.students.append(student)
    db.commit()

    return {"message": f"Student {student.name} added to course {course.course}"}

 #----------------------------------------------------------------------


@app.post("/addcoursePayload")
async def write_course(course: CourseBase,db:db_dependency):
    try:
         
        existing_course = db.query(models.Course).filter(models.Course.course == course.course).first()
        if existing_course:
            return {"message": "Course already exists"}
        db_course = models.Course(**course.dict())
        db.add(db_course)
        db.commit()  # Commit the transaction
        return "Course Added successfully"
    except Exception as e:
        print("Error occurred:", e)
 

        #-----------------------------------------------------------------------


@app.post("/addstudentPayload")
async def write_data(student: StudentBase,db:db_dependency):
    try:
      
        db_user = models.Student(**student.dict())
        db.add(db_user)
        db.commit()          
        return "Record inserted successfully"
    except Exception as e:
        print("Error occurred:", e)

    #-------------------------------------------------------------------------------

@app.post("/upload_students/")
async def upload_students_csv(file: UploadFile = File(...),db: Session = Depends(get_db)):
    try:
        content = await file.read()
        decoded_content = content.decode('utf-8-sig')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        
        for row in csv_reader:
            name = row['name']
            existing_student = db.query(models.Student).filter(models.Student.name == name).first()
            if existing_student:
                # Course already exists, skip insertion
                continue
            insert_query = text(
                """INSERT INTO students (name) VALUES (:name)"""
            )
            db.execute(insert_query,{'name':name})
              # Commit the transaction
        db.commit()
        return "CSV data inserted successfully"
    except Exception as e:
         error_message = f"An error occurred: {e}\n{traceback.format_exc()}"
         print(error_message)
         return {"error": "An error occurred while inserting data from CSV into the database"}


      #----------------------------------------------------------------------
    
@app.post("/upload_courses/")
async def upload_courses_csv(file: UploadFile = File(...),db: Session = Depends(get_db)):
     try:
        content = await file.read()
        decoded_content = content.decode('utf-8-sig')
        csv_reader = csv.DictReader(decoded_content.splitlines(), delimiter=',')
        
        for row in csv_reader:
            name = row['course']
            existing_course = db.query(models.Course).filter(models.Course.course == name).first()
            if existing_course:
                # Course already exists, skip insertion
                continue
            insert_query = text(
                """INSERT INTO courses (course) VALUES (:name)"""
            )
            db.execute(insert_query,{'name':name})
              # Commit the transaction
        db.commit()
        return "CSV courses data inserted successfully"
     except Exception as e:
         error_message = f"An error occurred: {e}\n{traceback.format_exc()}"
         print(error_message)
         return {"error": "An error occurred while inserting data from CSV into the database"}    


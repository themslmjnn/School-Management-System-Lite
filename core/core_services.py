from fastapi import HTTPException


MESSAGE_403 = "Accessing denied"


class CoreService:
    @staticmethod
    def is_admin(user):
        if user["role"] != "admin":
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        
    
    @staticmethod
    def does_have_access(user):
        if user["role"] not in ("director", "vice_director", "head_of_class"):
            raise HTTPException(status_code=403, detail=MESSAGE_403)
        
    
    @staticmethod
    def is_student(user, student_id):
        if user["id"] != student_id:
            raise HTTPException(status_code=403, detail=MESSAGE_403)

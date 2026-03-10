from src.models.mark_model import Mark
from src.repositories.mark_repositories import MarkRepository
from utils.helpers import require_teacher, require_admin, require_existence, update_object


MESSAGE_404 = "Mark not found"


class MarkService:
    @staticmethod
    def put_mark(db, user, mark_request):
        require_teacher(user)

        mark = Mark(**mark_request.model_dum())

        MarkRepository.put_mark(db, mark)

        db.commit()
        db.refresh(mark)
        
        return mark
    

    @staticmethod
    def delete_mark(db, user, mark_id):
        try:
            require_admin(user)

        finally:
            require_teacher(user)

        
        mark = MarkRepository.get_mark_by_id(db, mark_id)

        require_existence(mark, MESSAGE_404)

        MarkRepository.delete_mark(db, mark)

        db.commit()


    @staticmethod
    def update_mark_info(db, user, mark_id, mark_update_info_request):
        require_admin(user)

        mark = MarkRepository.get_mark_by_id(db, mark_id)

        require_existence(mark, MESSAGE_404)

        update_object(mark, mark_update_info_request)

        db.commit()

        return mark
    

    @staticmethod
    def get_marks(db, user):
        try:
            require_admin(user)

        finally:
            require_teacher(user)

        return MarkRepository.get_marks(db)
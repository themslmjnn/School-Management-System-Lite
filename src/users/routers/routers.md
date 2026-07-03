-- SYSTEM ADMIN --
1. POST "/users" - system admin creating staff and parent
2. POST "/users/students" - system admin creating students
3. DELETE "/users/parents/{parent_id}" - system admin deleting parent
4. PATCH "/users/{target_user_id}/deactivate" - system admin deactivating users
5. PATCH "/users/{target_user_id}/activate" - system admin activating users
6. PATCH "/users/{target_user_id}" - system admin updating users' info
7. PATCH "/users/{target_user_ud}/email" - system admin updating users' email
8. POST "/users/{target_user_id}/reset_password" - system admin creating reset password request
9. GET "/users" - system admin viewing only staff
10. GET "/users/{target_user_id}" - system admin viewing only staff by id
11. GET "/users/parents" - system admin viewing only parents
12. GET "/users/parents/{target_parent_id}" - system admin viewing only parent by id
13. GET "/users/students" - system admin viewing only students
14. GET "/users/{target_student_id}" - system admin viewing only student by id


-- DIRECTOR --
1. GET "/users" - director viewing staff
2. GET "/users/{target_user_id}" - director viewing only staff by id
3. GET "/users/students" - director viewing only students
4. GET "/users/{target_student_id}" - director viewing only student by id


-- VICE DIRECTOR --
1. GET "/users" - director viewing staff
2. GET "/users/{target_user_id}" - director viewing only staff by id
3. GET "/users/students" - director viewing only students
4. GET "/users/{target_student_id}" - director viewing only student by id


-- TEACHER --
1. GET "/groups/{target_group_id}/students" - teacher viewing only students that he teaches
2. GET "/groups/{target_group_id}/students/{target_student_id}" - teacher viewing only student that he teaches by id
3. GET "/my_groups"- head of class viewing their groups
4. GET "/my_groups/{target_group_id}"- head of class viewing their groups by id
3. GET "/my_groups/{target_group_id}/my-students" - head of class viewing his students
4. GET GET "/my_groups/{target_group_id}/my-students/{target_student_id}" - head of class viewing only student that he teaches by id


-- PARENT --
1. GET "/my-children" - guardians viewing their children
2. GET "/my-children/{target_child_id}" - guardians viewing their child by id
3. DELETE "/users/me" - guardians deleting their account
4. PATCH "/users/me/deactivate" - guardians deactivating their profile
5. PATCH "/users/me" - guardians updating their info


-- OTHER ROUTERS -- 
1. GET "/users/me" - users viewing their profile
2. PATCH "/users/students/me" - students updating their username
3. PATCH "/users/me" - users updating their info (username, email)
4. PATCH "/users/me/password" - users updating their password
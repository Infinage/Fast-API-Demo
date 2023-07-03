from fastapi import APIRouter, Body, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from data.db.client import mongo_client
from utils.util import ResponseModel
from data.models.user import User, UserTypeEnum, UpdateUser
import datetime as dt
from typing import Annotated
from utils.security import HashUtil, JWTUtil, UserUtil

user_router = APIRouter(
    prefix="/user",
    tags=["user"]
)

@user_router.get("/", deprecated=True, response_model=ResponseModel, dependencies=[Depends(UserUtil.is_atleast_admin)])
async def get_all_users():
    '''Lists all the users. This API might be of use to Admins and Owners, otherwise it's usage discouraged.'''
    users = [user async for user in mongo_client.user.find({}, { "password": 0 })]
    return ResponseModel(content=users)

@user_router.post("/create", response_model=ResponseModel)
async def create_user(logged_in_user: Annotated[User, Depends(JWTUtil.get_current_user)], user: User = Body(...)):

    if (logged_in_user and 
            (logged_in_user["type"] == UserTypeEnum.owner) or # Owner can create all user types
            (logged_in_user["type"] == UserTypeEnum.admin and user.type != UserTypeEnum.owner) or # Admin can create user types admin and below
            (logged_in_user["type"] == UserTypeEnum.user and user.type == UserTypeEnum.user) # User can create only 'users'
        ):
        if (not await mongo_client.user.find_one({ "username": user.username })):
            
            # Add the audit fields
            user.create_date = logged_in_user["AH_DATE"]()
            user.created_by = logged_in_user["AH_USER"]

            user.password = HashUtil.get_password_hash(user.password)
            inserted = await mongo_client.user.insert_one(user.dict())
            new_user = await mongo_client.user.find_one({ "_id": inserted.inserted_id }, { "password": 0 } )
            return ResponseModel(
                content=new_user, 
                message="User has been successfully added",
                status_code=status.HTTP_201_CREATED
            )
        else:
            return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"Username: {user.username} already exists.")
    else:
        return ResponseModel(status_code=status.HTTP_401_UNAUTHORIZED, message="User is unauthorized for this operation.")
    
@user_router.post("/login", response_model=JWTUtil.TokenModel)
async def login_user_for_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_in_db = await mongo_client.user.find_one({"username": form_data.username})
    pwd_match = HashUtil.verify_password(form_data.password, user_in_db["password"]) if (user_in_db) else False
    if (user_in_db and not user_in_db["disabled"] and pwd_match):
        token = JWTUtil.generate_access_token({"sub": user_in_db["username"]})
        return {"access_token": token, "token_type": "bearer"}
    else:
        if not user_in_db:
            message = f"Username: {form_data.username} doesn't exist."
        elif user_in_db["disabled"]:
            message = f"Username: {form_data.username} is not currently active. Please check with your immediate supervisor."
        else:
            message = f"Username and Password doesn't match."
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message, headers={"WWW-Authenticate": "Bearer"})
    
@user_router.patch("/{username}", response_model=ResponseModel)
async def update_user(logged_in_user: Annotated[User, Depends(JWTUtil.get_current_user)], username: str, update_user: UpdateUser):
    '''
    Possible usage: Update allowed only on Password, Disabled fields

    1. Reset password<br>
    2. Disable / Enable user (Admin & above)<br>
    3. Delete user (only owner)<br>

    '''
    user_to_update: dict = await mongo_client.user.find_one({"username": username})
    if user_to_update:
        if (
            # Id to update should match, but users can self delete or disable
            (user_to_update["_id"] == logged_in_user["_id"] and update_user.deleted != True and update_user.disabled != True) or 

            # Admin can update on behalf of all 'user'(s) but can't delete an user
            (logged_in_user["type"] == UserTypeEnum.admin and user_to_update["type"] == UserTypeEnum.user and update_user.deleted != True) or 

            # Owner can update everyone except for owner types
            (logged_in_user["type"] == UserTypeEnum.owner and user_to_update["type"] != UserTypeEnum.owner) 
        ):
            if update_user.deleted:
                update_result = await mongo_client.user.delete_one({"username": username})
            else: 
                update_result = await mongo_client.user.update_one({"username": username}, {"$set": {
                    "disabled": bool(update_user.disabled), 
                    "updated_by": logged_in_user["AH_USER"], 
                    "update_date": logged_in_user["AH_DATE"](), 
                    "password": HashUtil.get_password_hash(update_user.password) if update_user.password else user_to_update["password"]
                }})
            if update_result:
                return ResponseModel(
                    content=await mongo_client.user.find_one({"username": username}), 
                    message=f"User: {username} {'updated' if not update_user.deleted else 'deleted'} successfully."
                )
        else:
            return ResponseModel(status_code=status.HTTP_403_FORBIDDEN, message="Insufficient access privileges.")
    else:
        return ResponseModel(status_code=status.HTTP_400_BAD_REQUEST, message=f"User Name: {username} is not found.")

@user_router.get("/me", response_model=ResponseModel)
async def read_users_me(current_user: Annotated[User, Depends(JWTUtil.get_current_user)]):
    '''Shows the currently logged in user details.'''
    if current_user:
        cu = dict(current_user)

        # Remove the Audit helper fields
        cu.pop("AH_DATE", None)
        cu.pop("AH_USER", None)
        
        return ResponseModel(content=cu)
    else:
        return ResponseModel(status_code=status.HTTP_401_UNAUTHORIZED, message="No user currently logged in (or) user is invalid.")
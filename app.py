from fastapi import FastAPI, HTTPException, Response
from fastapi.encoders import jsonable_encoder
import motor.motor_asyncio
from pydantic import BaseModel, BeforeValidator, Field
from fastapi.responses import JSONResponse
from typing import Annotated, List
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [ "https://ecse3038-lab3-tester.netlify.app" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

app = FastAPI()

connection = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URL"))
people_db = connection.people

PyObbjectId = Annotated[str, BeforeValidator(str)]

class Profile(BaseModel):
    id: PyObbjectId | None = Field(default = None, alias="_id")
    last_updated: datetime = datetime.now()
    username: str
    role: str
    color: str

class Tank(BaseModel):
    id: PyObbjectId | None = Field(default=None, alias="_id")
    location: str
    lat: float
    long: float

class ProfileCollection(BaseModel):
    profile: List[Profile]

class TankCollection(BaseModel):
    tanks: List[Tank]

class TankUpdate(BaseModel):
    location: str | None = None
    lat: float | None = None
    long: float | None = None

@app.get("/profile")
async def get_profile():
    profile_collection = await people_db["profiles"].find().to_list(999)
    return ProfileCollection(profile=profile_collection)

@app.get("/tank")
async def get_tanks():
    tank_collection = await people_db["tanks"].find().to_list(999)
    return TankCollection(tanks=tank_collection)

@app.post("/profile")
async def create_profile(profile_request: Profile):
    profile_dictionary = profile_request.model_dump()
    created_profile = await people_db["profiles"].insert_one(profile_dictionary)

    new_profile = await people_db["profiles"].find_one({"_id":created_profile.inserted_id})

    profile_new = Profile(**new_profile)#explodes the object "explodes the object profile"

    json_updated_profile = jsonable_encoder(profile_new)
    return JSONResponse(json_updated_profile,status_code=201)

@app.post("/tank")
async def create_tank(tank_request: Tank):
    tank_dictionary = tank_request.model_dump()
    created_tank = await people_db["tanks"].insert_one(tank_dictionary)

    new_tank = await people_db["tanks"].find_one({"_id":created_tank.inserted_id})
    tank_new = Tank(**new_tank)

    json_updated_tank = jsonable_encoder(tank_new)
    return JSONResponse(json_updated_tank,status_code=201)

@app.patch("/tank/{id}")
async def update_tank(id: str, tank_update: TankUpdate):
    tank_dictionary = tank_update.model_dump()
    updated_tank = await people_db["tanks"].update_one({"_id":ObjectId(id)},{"$set":tank_dictionary})
    updated_tank = await people_db["tanks"].find_one({"_id":ObjectId(id)})
    if updated_tank:
        return Tank(**updated_tank)
    raise HTTPException(status_code=404,detail="Tank not found")
    pass

@app.delete("/tank/{id}")
async def delete_tank(id: str):
    search_tank = await people_db["tanks"].find_one({"_id":ObjectId(id)})
    if search_tank:
       await people_db["tanks"].delete_one({"_id":ObjectId(id)})
       return Response(status_code=200)
    
    raise HTTPException(status_code=404,detail="Tank not found")

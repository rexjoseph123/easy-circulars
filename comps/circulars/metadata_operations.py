from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException, Request
from datetime import datetime
import traceback
from comps.mongo_client import mongo_client

collection = mongo_client['easy_circulars']['circulars']

class CircularUpdateData(BaseModel):
    circular_id: str
    bookmark: Optional[bool] = None
    conversation_id: Optional[str] = None 

async def handle_circular_post(request: Request):
    try:
        circular_data = await request.json()
        if 'date' in circular_data:
            circular_data['date'] = datetime.fromisoformat(circular_data['date'])

        inserted_circular_data = collection.insert_one(circular_data)
        circular_id = str(inserted_circular_data.inserted_id)
        return circular_id

    except Exception as e:
        print(e)
        raise Exception(e)  

def handle_circular_update(circularUpdate: CircularUpdateData):
    try:
        update_fields = {}
        if circularUpdate.bookmark is not None:
            update_fields["bookmark"] = circularUpdate.bookmark
        if circularUpdate.conversation_id is not None:
            update_fields["conversation_id"] = circularUpdate.conversation_id
        updated_result = collection.update_one(
            {"_id": circularUpdate.circular_id},
            {"$set": update_fields},
        )

        if updated_result.modified_count == 1:
            return True
        else:
            raise Exception("Not able to update the data.")

    except Exception as e:
        raise Exception(e)
    
def get_bookmarked_circulars() -> list[dict]:
    try:
        circulars: list = []
        cursor = collection.find({"bookmark": True})

        for document in cursor:
            document["circular_id"] = str(document["_id"])
            del document["_id"]
            circulars.append(document)
        return circulars

    except Exception as e:
        print(e)
        raise Exception(e)
    
def get_circular_by_id(circular_id) -> dict | None:
    try:

        main_circular = collection.find_one({"_id": circular_id})
        if not main_circular:
            return None

        references_ids = main_circular.get("references", [])

        referenced_circulars = []
        if references_ids:
            object_ids = [ref_id for ref_id in references_ids]
            cursor = collection.find({"_id": {"$in": object_ids}})
            referenced_circulars = cursor.to_list(length=len(references_ids))

            for ref in referenced_circulars:
                ref["circular_id"] = str(ref["_id"])

        main_circular["circular_id"] = str(main_circular["_id"])
        
        return {
            "circular": main_circular,
            "references": referenced_circulars
        }
    except Exception as e:
        print(f"Error fetching circular: {e}")
        return None
    
def get_circulars_by_month_and_year(month, year) -> list[dict]:
    try:
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")

        circulars: list = []

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        cursor = collection.find({
            "date": {
                "$gte": start_date,
                "$lt": end_date
            }
        })

        for document in cursor:
            document["circular_id"] = str(document["_id"])
            del document["_id"]
            circulars.append(document)
        return circulars

    except Exception as e:
        print(e)
        raise Exception(e)
    
def get_all_circulars() -> list[dict]:
    try:
        circulars: list = []
        cursor = collection.find()

        for document in cursor:
            document["circular_id"] = str(document["_id"])
            del document["_id"]
            circulars.append(document)
        return circulars

    except Exception as e:
        print(e)
        raise Exception(e)
    
def handle_circular_get(request: Request):
    try:
        circular_id = request.query_params.get("circular_id")
        bookmark = request.query_params.get("bookmark", "false").lower() == "true"

        year_param = request.query_params.get("year")
        month_param = request.query_params.get("month")
        year = int(year_param) if year_param is not None else None
        month = int(month_param) if month_param is not None else None
        
        if bookmark:
            response = get_bookmarked_circulars()
        elif circular_id:
            response = get_circular_by_id(circular_id)
        elif year and month:
            response = get_circulars_by_month_and_year(month, year)
        else:
            response = get_all_circulars()

        return response

    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print("Error fetching circulars:", error_details)
        raise HTTPException(status_code=500, detail=error_details)

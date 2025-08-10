from fastapi import Header, HTTPException, status


API_KEY=""

def verify_api_key(api_key:str=Header(...)):
     if api_key !=API_KEY:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API token!")
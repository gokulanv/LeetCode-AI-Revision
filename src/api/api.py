import httpx
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
leetcode_url = "https://leetcode.com/graphql"

# Get LeetCode session from environment
LEETCODE_SESSION = os.getenv('LEETCODE_SESSION')

def get_authenticated_client() -> httpx.AsyncClient:
    """Create an authenticated HTTP client with LeetCode session cookie"""
    headers = {}
    if LEETCODE_SESSION:
        headers['Cookie'] = f'LEETCODE_SESSION={LEETCODE_SESSION}'
    return httpx.AsyncClient(headers=headers)


async def get_submission_code(submission_id: int) -> Optional[str]:
    """
    Fetch the code for a specific submission ID.
    Requires authentication via LEETCODE_SESSION cookie.
    """
    if not LEETCODE_SESSION:
        return None
    
    query = """query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code
            runtime
            memory
            statusDisplay
            lang
            langName
            timestamp
        }
    }"""
    
    payload = {
        "query": query,
        "variables": {"submissionId": submission_id},
        "operationName": "submissionDetails"
    }
    
    try:
        async with get_authenticated_client() as client:
            response = await client.post(leetcode_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    return None
                submission = data.get("data", {}).get("submissionDetails")
                return submission.get("code") if submission else None
    except Exception as e:
        print(f"Error fetching submission code: {e}")
        return None
    
    return None


@app.get("/user/{username}/submissions", tags=["Submissions"])
async def get_recent_submissions(username: str, limit: int = 20, include_code: bool = True):
    """
    Get user's recent submissions with optional code.
    
    Args:
        username: LeetCode username
        limit: Maximum number of submissions to return (default: 20)
        include_code: If True, include submission code (requires authentication, default: True)
    
    Returns:
        List of submissions with metadata and optionally code
    """
    authenticated = bool(LEETCODE_SESSION)
    
    if include_code and not authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required to fetch code. Please set LEETCODE_SESSION in your .env file."
        )
    
    client_to_use = get_authenticated_client() if authenticated else httpx.AsyncClient()
    
    query = """query recentSubmissions($username: String!, $limit: Int) {
        recentSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
            status
            statusDisplay
            lang
            url
            langName
            runtime
            isPending
            memory
            hasNotes
            notes
            flagType
            frontendId
            topicTags {
                id
            }
        }
    }"""
    
    payload = {
        "query": query,
        "variables": {"username": username, "limit": limit}
    }
    
    try:
        async with client_to_use as client:
            response = await client.post(leetcode_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    raise HTTPException(status_code=404, detail="User not found")
                
                submissions = data["data"]["recentSubmissionList"]
                
                # Fetch code for each submission if requested
                if include_code and authenticated:
                    for submission in submissions:
                        code = await get_submission_code(submission["id"])
                        submission["code"] = code
                
                return submissions
            raise HTTPException(status_code=response.status_code, detail="Error fetching submissions")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/submission/{submission_id}", tags=["Submissions"])
async def get_submission_details(submission_id: int):
    """
    Get detailed information about a specific submission, including code.
    Requires LEETCODE_SESSION to be set in .env file.
    """
    if not LEETCODE_SESSION:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Please set LEETCODE_SESSION in your .env file."
        )
    
    query = """query submissionDetails($submissionId: Int!) {
        submissionDetails(submissionId: $submissionId) {
            code
            runtime
            memory
            timestamp
            question {
                questionId
                title
                titleSlug
            }
        }
    }"""
    
    payload = {
        "query": query,
        "variables": {"submissionId": submission_id},
        "operationName": "submissionDetails"
    }
    
    try:
       async with get_authenticated_client() as client:
            response = await client.post(leetcode_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    error_msg = data["errors"][0].get("message", "Unknown error")
                    raise HTTPException(status_code=404, detail=f"Submission not found: {error_msg} {data}")
                
                submission = data.get("data", {}).get("submissionDetails")
                if not submission:
                    raise HTTPException(status_code=404, detail=f"Submission not found {data}")
                
                return submission
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching submission {response.text}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Utility"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

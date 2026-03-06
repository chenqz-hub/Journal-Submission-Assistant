from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.routes import router
from api.auth import verify_access_code
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title='SciAutoFormat API',
    description='科研投稿自动化排版与辅助工具 - V1.0 API',
    version='1.0.0'
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Mount static files (Frontend H5)
app.mount('/static', StaticFiles(directory='static'), name='static')

# Include API router requiring Access Code
app.include_router(router, prefix='/api/v1', dependencies=[Depends(verify_access_code)])

@app.get('/')
def read_root():
    return FileResponse('static/index.html')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)

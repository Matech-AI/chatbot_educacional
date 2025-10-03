# Deployment Instructions for Coolify

## Prerequisites

*   A Coolify instance
*   A domain name
*   A Git repository containing the project code

## Steps

1.  **Create a new project in Coolify.**
2.  **Connect your Git repository to the project.**
3.  **Configure the environment variables.**

    *   Go to the "Environment Variables" section of your project.
    *   Add the following environment variables, using the values from your `.env.example` files:

        ```
        VITE_SUPABASE_URL=your_supabase_url
        VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
        VITE_API_URL=your_api_url
        OPENAI_API_KEY=your_openai_api_key
        GOOGLE_CREDENTIALS_PATH=backend/credentials.json
        DATABASE_URL=your_database_url
        ENVIRONMENT=production
        CORS_ORIGINS=your_cors_origins
        JWT_SECRET_KEY=your_jwt_secret_key
        GEMINI_API_KEY=your_gemini_api_key
        NVIDIA_API_KEY=your_nvidia_api_key
        GOOGLE_DRIVE_API_KEY=your_google_drive_api_key
        PREFER_OPEN_SOURCE_EMBEDDINGS=true
        OPEN_SOURCE_EMBEDDING_MODEL=intfloat/multilingual-e5-large
        RAG_SERVER_URL=http://rag-server:8001
        CHROMA_PERSIST_DIR=/app/data/.chromadb
        MATERIALS_DIR=/app/data/materials
        JWT_ALGORITHM=HS256
        ACCESS_TOKEN_EXPIRE_MINUTES=30
        LOG_LEVEL=INFO
        REDIS_URL=redis://redis:6379
        EMAIL_HOST=smtp.gmail.com
        EMAIL_PORT=587
        EMAIL_USERNAME=your_email@gmail.com
        EMAIL_PASSWORD=your_app_password
        EMAIL_FROM=your_email@gmail.com
        HOSTINGER=false
        SERVER_IP=0.0.0.0
        RAG_PORT=8000
        API_PORT=8001
        FRONTEND_PORT=3000
        HOSTINGER_CHROMADB_PATH=/root/dna-forca-complete/backend/data/.chromadb
        HOSTINGER_MATERIALS_PATH=/root/dna-forca-complete/backend/data/materials
        ```
4.  **Configure the services.**

    *   Create three services: `frontend`, `backend`, and `rag_server`.
    *   Use the `Dockerfile.frontend` for the `frontend` service.
    *   Use the `backend/Dockerfile.api` for the `backend` service.
    *   Use the `backend/Dockerfile.rag` for the `rag_server` service.
    *   Set the ports for each service according to the `docker-compose.yml` file.
    *   Define volumes for `chromadb_data` and `materials_data` in the backend service.

5.  **Deploy the application.**

    *   Click the "Deploy" button to deploy the application.

## Notes

*   Make sure to update the environment variables with your actual values.
*   The `GOOGLE_CREDENTIALS_PATH` environment variable should point to the location of your Google Drive API credentials file.
*   The `DATABASE_URL` environment variable should point to your PostgreSQL database.
*   The `REDIS_URL` environment variable should point to your Redis instance.
*   The `EMAIL_*` environment variables should be configured with your email provider settings.
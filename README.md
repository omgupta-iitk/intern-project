## Intern-Project
---
#### Here's how to run the messaging app and test it! :

Firstly, clone this repo:
```
git clone https://github.com/omgupta-iitk/intern-project
cd intern-project/
```

### Backend Setup:

1. Setup python environment:
Note: You can use any python environment but with `python@3.11.11`.
Using miniconda,
Installation Instructions: [conda-docs](https://www.anaconda.com/docs/getting-started/miniconda/install)
```
conda create -n myenv python=3.11.11
conda activate myenv
```

2. Install the requirements:
```
cd backend/
pip install -r requirements.txt

```

3. Rename the `backend/.env_example` to `backend/.env` and fill in the credentials there.

4. Run the following command in the terminal to start the backend server:
```
uvicorn main:app
```

### Frontend Setup

Note: Here `nodejs@v22.15.0` is used.

1. Installing Packages:
```
cd frontend-message-app/
npm install
```

2. To run the frontend:
```
npm run dev
```

Note: The frontend makes a GET request to the backend just after launching, so make sure to start the backend first, then Frontend. Or Restart the frontend if any errors encountered at the launch.

#### Here's how to inference data-analysis API endpoints:

1. First setup the backend and start the server.

2. Here's the postman collection([link]()) to test it.

Note: If face any problem and the backend crashes due to network issues, then restart the backend server and try again to inference.
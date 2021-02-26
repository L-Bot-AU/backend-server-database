# backend-server
This is the code for the backend server which manages the library system's database, updates it with incoming requests from the library camera and sends data to the dashboard website and the librarian interface.

To setup:
- Uncomment the  `restartdb()` function if your database is already created and don't want to replace it with a new one
- Run `client_side_interface.py` with a python interpreter and replace the value of `KEY` to a more secure one
